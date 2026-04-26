"""
cat_widget.py
Animated virtual pet cat for Flet using catode32 sprite data.
Renders monochrome sprites to a PNG each frame, displayed as ft.Image.
"""

import sys
import base64
import struct
import zlib
import random
import threading
import asyncio
import time

import flet as ft

# Add catode32 source for sprite data
CATODE_SRC = r"C:\Users\lunaa\Desktop\catode32-master\src"
if CATODE_SRC not in sys.path:
    sys.path.insert(0, CATODE_SRC)

from assets.character import POSES
from sprite_transform import mirror_sprite_h


# --- Pixel Canvas ---

class PixelCanvas:
    """Small monochrome pixel buffer that exports to PNG."""

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.pixels = bytearray(width * height)

    def clear(self):
        for i in range(len(self.pixels)):
            self.pixels[i] = 0

    def set_pixel(self, x, y, color=1):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.pixels[y * self.width + x] = color

    def draw_sprite(self, data, w, h, x, y, transparent=True,
                    invert=False, transparent_color=0):
        if not data:
            return
        buf = bytearray(data)
        if invert:
            buf = bytearray(b ^ 0xFF for b in buf)
        bpr = (w + 7) // 8
        for py in range(h):
            for px in range(w):
                idx = py * bpr + px // 8
                bit = 7 - (px % 8)
                if idx < len(buf):
                    pixel = (buf[idx] >> bit) & 1
                else:
                    pixel = 0
                if transparent and pixel == transparent_color:
                    continue
                self.set_pixel(x + px, y + py, pixel)

    def to_base64_png(self, fg_color=(255, 255, 255), bg_color=None):
        """Export as base64-encoded PNG with transparency support."""
        w, h = self.width, self.height
        raw = bytearray()
        for y in range(h):
            raw.append(0)
            for x in range(w):
                if self.pixels[y * w + x]:
                    raw.extend(fg_color)
                    raw.append(255)
                else:
                    if bg_color:
                        raw.extend(bg_color)
                        raw.append(255)
                    else:
                        raw.extend((0, 0, 0, 0))

        def chunk(ctype, data):
            c = ctype + data
            crc = struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
            return struct.pack(">I", len(data)) + c + crc

        sig = b'\x89PNG\r\n\x1a\n'
        ihdr = struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)
        idat = zlib.compress(bytes(raw), 9)
        png = sig + chunk(b'IHDR', ihdr) + chunk(b'IDAT', idat) + chunk(b'IEND', b'')
        return base64.b64encode(png).decode()


# --- Cat Animation State ---

def _get_pose(name):
    parts = name.split(".")
    if len(parts) != 3:
        return None
    try:
        return POSES[parts[0]][parts[1]][parts[2]]
    except KeyError:
        return None


class CatAnimator:
    """Manages sprite animation state and rendering."""

    def __init__(self, pose_list=None):
        self._pose_list = pose_list or [
            "sitting.side.neutral",
            "sitting.forward.neutral",
        ]
        self.pose_name = self._pose_list[0]
        self._pose = _get_pose(self.pose_name)
        self.mirror = random.choice([True, False])

        self.anim_body = 0.0
        self.anim_head = 0.0
        self.anim_eyes = 0.0
        self.anim_tail = 0.0

        self._pose_timer = 0.0
        self._next_switch = random.uniform(6, 15)

        self._mirror_cache = {}
        self._inv_fill_cache = {}

    def set_poses(self, pose_list):
        if pose_list != self._pose_list:
            self._pose_list = pose_list
            if self.pose_name not in pose_list and pose_list:
                self._set_pose(random.choice(pose_list))

    def _set_pose(self, name):
        pose = _get_pose(name)
        if pose is None:
            return
        self.pose_name = name
        self._pose = pose
        self._mirror_cache = {}
        self._inv_fill_cache = {}
        self.anim_body = 0.0
        self.anim_head = 0.0
        self.anim_eyes = 0.0
        self.anim_tail = 0.0

    def _total(self, sprite):
        return len(sprite["frames"]) + sprite.get("extra_frames", 0)

    def _fidx(self, sprite, counter):
        fc = len(sprite["frames"])
        if fc == 0:
            return 0
        idx = int(counter) % self._total(sprite)
        return idx if idx < fc else 0

    def _point(self, sprite, key, frame=0, mirror=False):
        val = sprite[key]
        r = val[frame] if isinstance(val, list) else val
        if mirror and key.endswith('_x'):
            return sprite["width"] - r
        return r

    def _anchor_x(self, sprite, mirror=False):
        ax = sprite["anchor_x"]
        return sprite["width"] - ax if mirror else ax

    def _ensure_mirror(self, sprite):
        sid = id(sprite)
        if sid not in self._mirror_cache:
            w, h = sprite["width"], sprite["height"]
            entry = {"frames": [mirror_sprite_h(f, w, h) for f in sprite["frames"]]}
            if "fill_frames" in sprite and sprite["fill_frames"]:
                mf = [mirror_sprite_h(f, w, h) for f in sprite["fill_frames"]]
                entry["inv_fills"] = [bytearray(b ^ 0xFF for b in f) for f in mf]
            self._mirror_cache[sid] = entry
        return self._mirror_cache[sid]

    def _ensure_inv_fill(self, sprite):
        sid = id(sprite)
        if sid not in self._inv_fill_cache:
            self._inv_fill_cache[sid] = [
                bytearray(b ^ 0xFF for b in f) for f in sprite["fill_frames"]
            ]
        return self._inv_fill_cache[sid]

    def update(self, dt):
        pose = self._pose
        if not pose:
            return

        self.anim_body = (self.anim_body + dt * pose["body"].get("speed", 1)) % max(1, self._total(pose["body"]))
        self.anim_head = (self.anim_head + dt * pose["head"].get("speed", 1)) % max(1, self._total(pose["head"]))
        self.anim_eyes = (self.anim_eyes + dt * pose["eyes"].get("speed", 1)) % max(1, self._total(pose["eyes"]))
        self.anim_tail = (self.anim_tail + dt * pose["tail"].get("speed", 1)) % max(1, self._total(pose["tail"]))

        self._pose_timer += dt
        if self._pose_timer >= self._next_switch:
            self._pose_timer = 0.0
            self._next_switch = random.uniform(6, 15)
            if self._pose_list:
                self._set_pose(random.choice(self._pose_list))
            if random.random() < 0.3:
                self.mirror = not self.mirror
                self._mirror_cache = {}

    def render(self, canvas, cx, cy):
        pose = self._pose
        if not pose:
            return
        mirror = self.mirror

        body = pose["body"]
        bf = self._fidx(body, self.anim_body)
        bx = cx - self._anchor_x(body, mirror)
        by = cy - body["anchor_y"]

        head = pose["head"]
        hf = self._fidx(head, self.anim_head)
        hx = bx + self._point(body, "head_x", bf, mirror) - self._anchor_x(head, mirror)
        hy = by + self._point(body, "head_y", bf) - head["anchor_y"]

        eyes = pose["eyes"]
        ef = self._fidx(eyes, self.anim_eyes)
        ex = hx + self._point(head, "eye_x", hf, mirror) - self._anchor_x(eyes, mirror)
        ey = hy + self._point(head, "eye_y", hf) - eyes["anchor_y"]

        tail = pose["tail"]
        tf = self._fidx(tail, self.anim_tail)
        tx = bx + self._point(body, "tail_x", bf, mirror) - self._anchor_x(tail, mirror)
        ty = by + self._point(body, "tail_y", bf) - tail["anchor_y"]

        head_first = pose.get("head_first", False)

        parts = [("tail", tail, tx, ty, tf)]
        if head_first:
            parts += [("head", head, hx, hy, hf), ("body", body, bx, by, bf)]
        else:
            parts += [("body", body, bx, by, bf), ("head", head, hx, hy, hf)]
        parts.append(("eyes", eyes, ex, ey, ef))

        for _, sprite, sx, sy, sf in parts:
            if mirror:
                cached = self._ensure_mirror(sprite)
                if "inv_fills" in cached and sf < len(cached["inv_fills"]):
                    canvas.draw_sprite(cached["inv_fills"][sf],
                                       sprite["width"], sprite["height"],
                                       sx, sy, transparent=True,
                                       transparent_color=1)
                if sf < len(cached["frames"]):
                    canvas.draw_sprite(cached["frames"][sf],
                                       sprite["width"], sprite["height"],
                                       sx, sy)
            else:
                if "fill_frames" in sprite and sprite["fill_frames"]:
                    inv = self._ensure_inv_fill(sprite)
                    if sf < len(inv):
                        canvas.draw_sprite(inv[sf],
                                           sprite["width"], sprite["height"],
                                           sx, sy, transparent=True,
                                           transparent_color=1)
                if sf < len(sprite["frames"]):
                    canvas.draw_sprite(sprite["frames"][sf],
                                       sprite["width"], sprite["height"],
                                       sx, sy)


# --- Flet Widget ---

class CatWidget:
    """
    Animated cat widget for Flet.

    Usage:
        cat = CatWidget(theme_mode="dark")
        page.add(cat.container)
        cat.start(page)
    """

    def __init__(self, theme_mode="dark", display_width=200, display_height=160):
        self._canvas_w = 80
        self._canvas_h = 64
        self._canvas = PixelCanvas(self._canvas_w, self._canvas_h)
        self._animator = CatAnimator()
        self._theme_mode = theme_mode
        self._running = False
        self._task = None
        self._page = None
        self._speech = ""
        self._speech_timer = 0.0

        # Handle different Flet versions
        try:
            img_fit = ft.ImageFit.CONTAIN
        except AttributeError:
            img_fit = "contain"

        # Render first frame BEFORE creating Image
        self._canvas.clear()
        self._animator.render(self._canvas, self._canvas_w // 2, self._canvas_h - 4)
        first_frame = self._canvas.to_base64_png(fg_color=self._fg_color())

        self._image = ft.Image(
            src=f"data:image/png;base64,{first_frame}",
            width=display_width,
            height=display_height,
            fit=img_fit,
        )

        # Speech bubble text
        self._speech_text = ft.Text(
            "",
            size=11,
            italic=True,
            text_align=ft.TextAlign.CENTER,
        )

        self._speech_container = ft.Container(
            content=self._speech_text,
            visible=False,
            padding=ft.padding.symmetric(horizontal=10, vertical=4),
            border_radius=10,
        )

        self.container = ft.Container(
            content=ft.Column(
                [
                    self._speech_container,
                    self._image,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
            ),
            padding=0,
            alignment=ft.Alignment(0, 0),
        )

    def _fg_color(self):
        if self._theme_mode == "dark":
            return (225, 220, 240)
        return (60, 50, 80)

    def _render_frame(self):
        self._canvas.clear()
        self._animator.render(self._canvas, self._canvas_w // 2, self._canvas_h - 4)
        b64 = self._canvas.to_base64_png(fg_color=self._fg_color())
        self._image.src = f"data:image/png;base64,{b64}"

    def set_theme(self, mode):
        self._theme_mode = mode

    def set_mood_poses(self, pose_list):
        self._animator.set_poses(pose_list)

    def say(self, text, duration=4.0):
        """Show a speech bubble above the cat."""
        self._speech = text
        self._speech_timer = duration
        self._speech_text.value = text
        self._speech_container.visible = True

    def start(self, page):
        """Start the animation loop using page.run_task for reliable updates."""
        if self._running:
            return
        self._page = page
        self._running = True

        async def _async_loop():
            fps = 8
            interval = 1.0 / fps
            idle_sayings = [
                "Mrrp?", "Purrr~", "*yawn*", "*stretches*",
                "Feed me!", "Play with me!", "*tail swish*",
                "Meow~", "*blinks slowly*", "Nya~",
                "*kneads paws*", "..zzZ", "*chirps at screen*",
            ]
            idle_timer = 0.0
            next_idle_say = random.uniform(20, 45)

            while self._running:
                try:
                    self._animator.update(interval)
                    self._render_frame()

                    # Speech bubble timer
                    if self._speech_timer > 0:
                        self._speech_timer -= interval
                        if self._speech_timer <= 0:
                            self._speech_container.visible = False
                            self._speech = ""

                    # Random idle chatter
                    idle_timer += interval
                    if idle_timer >= next_idle_say and not self._speech:
                        self.say(random.choice(idle_sayings), 3.0)
                        idle_timer = 0.0
                        next_idle_say = random.uniform(20, 45)

                    if self._page and self._running:
                        self._page.update()

                except Exception as e:
                    err_msg = str(e).lower()
                    if "destroyed" in err_msg or "session" in err_msg:
                        self._running = False
                        break

                await asyncio.sleep(interval)

        # Use page.run_task if available, otherwise fall back to threading
        if hasattr(page, "run_task"):
            page.run_task(_async_loop)
        else:
            # Fallback for older Flet
            def _thread_loop():
                loop = asyncio.new_event_loop()
                loop.run_until_complete(_async_loop())
            self._thread = threading.Thread(target=_thread_loop, daemon=True)
            self._thread.start()

    def stop(self):
        """Stop the animation loop."""
        self._running = False
        self._page = None

    def trigger_happy(self):
        """Briefly show a happy pose."""
        happy = [
            "sitting.side.happy",
            "sitting.forward.happy",
            "standing.side.happy",
        ]
        self._animator._set_pose(random.choice(happy))
        self._animator._pose_timer = 0.0
        self._animator._next_switch = 4.0
        happy_msgs = [
            "Yummy! *purrs*", "More please!", "Nom nom~",
            "*happy wiggle*", "Thank you! Nya~", "So tasty!",
        ]
        self.say(random.choice(happy_msgs), 3.0)

    def trigger_play(self):
        """Briefly show an energetic pose after playing."""
        play_poses = [
            "standing.side.happy",
            "sitting.side.happy",
            "sitting.forward.happy",
        ]
        self._animator._set_pose(random.choice(play_poses))
        self._animator._pose_timer = 0.0
        self._animator._next_switch = 5.0
        play_msgs = [
            "*pounces!*", "Wheee!", "*zoomies!*",
            "Catch me!", "*chases tail*", "So fun!",
        ]
        self.say(random.choice(play_msgs), 3.0)

    def trigger_pet(self):
        """React to being petted."""
        self._animator._set_pose("sitting.forward.happy")
        self._animator._pose_timer = 0.0
        self._animator._next_switch = 3.0
        pet_msgs = [
            "*purrrrrr*", "*leans into hand*", "Mrrrp~",
            "*slow blink*", "*head bonk*", "More pets!",
        ]
        self.say(random.choice(pet_msgs), 3.0)

    def trigger_password_added(self):
        """React when user adds a new password."""
        msgs = [
            "Good job! +points!", "Secure! *approves*",
            "Nya! More treats soon?", "*watches proudly*",
        ]
        self.say(random.choice(msgs), 3.5)