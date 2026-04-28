"""
widgets.py
Small reusable UI pieces so the main views stay readable.

Also contains compatibility shims for Flet's API churn: dialog
open/close and clipboard have all been renamed at least once. The
helpers here try the current name first and fall back to older ones
so the app works on Flet 0.21+ through 0.84+.
"""

import flet as ft
from .theme import ThemeManager, CATEGORY_COLORS


# ---------- Flet compat helpers ----------

def open_dialog(page: ft.Page, dialog):
    """Open a dialog across Flet versions."""
    # 0.84+: show_dialog / pop_dialog
    if hasattr(page, "show_dialog"):
        try:
            page.show_dialog(dialog)
            return
        except Exception:
            pass
    # 0.21 - 0.83: page.open()
    if hasattr(page, "open"):
        try:
            page.open(dialog)
            return
        except Exception:
            pass
    # Overlay approach (Flet 0.84 AlertDialog)
    try:
        if dialog not in page.overlay:
            page.overlay.append(dialog)
        dialog.open = True
        page.update()
        return
    except Exception:
        pass
    # pre-0.21: assign + set open flag
    page.dialog = dialog
    dialog.open = True
    page.update()


def close_dialog(page: ft.Page, dialog=None):
    """Close a dialog across Flet versions."""
    if hasattr(page, "pop_dialog"):
        try:
            page.pop_dialog()
            return
        except Exception:
            pass
    if hasattr(page, "close") and dialog is not None:
        try:
            page.close(dialog)
            return
        except Exception:
            pass
    # Overlay approach
    if dialog is not None:
        try:
            dialog.open = False
            page.update()
            if dialog in page.overlay:
                page.overlay.remove(dialog)
        except Exception:
            pass
        return
    if dialog is not None:
        dialog.open = False
        page.update()


def set_clipboard(page: ft.Page, text: str):
    """Copy text to the system clipboard. Uses pyperclip for reliability."""
    # Try pyperclip first — most reliable on desktop
    try:
        import pyperclip
        pyperclip.copy(text)
        return
    except Exception:
        pass
    # Flet fallbacks
    if hasattr(page, "set_clipboard"):
        try:
            page.set_clipboard(text)
            page.update()
            return
        except Exception:
            pass
    try:
        page.clipboard = text
        page.update()
    except Exception:
        pass

# ---------- Visual widgets ----------


def strength_badge(label: str, theme: ThemeManager) -> ft.Container:
    """Pill-shaped strength indicator matching the current theme."""
    fg, bg = theme.strength(label)
    return ft.Container(
        content=ft.Text(label, size=12, weight=ft.FontWeight.W_600, color=fg),
        bgcolor=bg,
        padding=ft.padding.symmetric(horizontal=10, vertical=4),
        border_radius=12,
    )


def category_chip(name: str, theme: ThemeManager) -> ft.Container:
    """Small colored dot + category name."""
    color = CATEGORY_COLORS.get(name, theme.c["text_muted"])
    return ft.Row(
        [
            ft.Container(width=8, height=8, bgcolor=color, border_radius=4),
            ft.Text(name, size=12, color=theme.c["text_muted"]),
        ],
        spacing=6,
        tight=True,
    )


def stale_badge(theme: ThemeManager) -> ft.Container:
    """Small orange 'Stale' badge for entries not updated in 30+ days."""
    return ft.Container(
        content=ft.Text(
            "\u23f0 Stale", size=10, color="#ffffff",
            weight=ft.FontWeight.BOLD,
        ),
        bgcolor="#FFA726",
        border_radius=6,
        padding=ft.padding.symmetric(horizontal=6, vertical=2),
    )


def favorite_star(is_favorite: bool, theme: ThemeManager,
                  on_click=None) -> ft.IconButton:
    """Star icon button for toggling favorites."""
    return ft.IconButton(
        icon=ft.Icons.STAR if is_favorite else ft.Icons.STAR_BORDER,
        icon_color="#e5c14a" if is_favorite else theme.c["text_muted"],
        icon_size=18,
        tooltip="Toggle favorite",
        on_click=on_click,
    )


def reward_snack(page: ft.Page, reward: dict, pet_name: str = "Cat"):
    """
    Show a rich snack bar for pet rewards.
    reward dict keys: coins_earned, xp_earned, level_ups, item_drop,
                      bonus_coins, bonus_xp
    """
    parts = []

    coins = reward.get("coins_earned", 0) + reward.get("bonus_coins", 0)
    if coins > 0:
        parts.append(f"\U0001fa99 +{coins} coins")

    xp = reward.get("xp_earned", 0) + reward.get("bonus_xp", 0)
    if xp > 0:
        parts.append(f"\u2728 +{xp} XP")

    level_ups = reward.get("level_ups", [])
    if level_ups:
        new_level = level_ups[-1]["new_level"]
        bonus = sum(lu["bonus_coins"] for lu in level_ups)
        parts.append(f"\U0001f389 Level {new_level}! (+{bonus} bonus coins)")

    item_drop = reward.get("item_drop")
    if item_drop:
        item_type, item_name, rarity = item_drop
        from backend.pet import RARITY_EMOJI
        emoji = RARITY_EMOJI.get(rarity, "\u2b50")
        parts.append(f"{emoji} Got: {item_name} ({rarity})")

    if parts:
        msg = " | ".join(parts)
        show_snack(page, f"\U0001f43e {msg}")


def show_snack(page: ft.Page, msg: str, error: bool = False):
    """Toast-style notification. Works across Flet versions."""
    snack = ft.SnackBar(
        ft.Text(msg, color="#ffffff"),
        bgcolor="#c44054" if error else "#2e8050",
        duration=2500,
    )
    # 0.84+: SnackBar is a DialogControl, shown via show_dialog / open
    # Older: page.snack_bar = snack; snack.open = True
    if hasattr(page, "show_dialog"):
        try:
            page.show_dialog(snack)
            return
        except Exception:
            pass
    if hasattr(page, "open"):
        try:
            page.open(snack)
            return
        except Exception:
            pass
    # Overlay approach
    try:
        page.overlay.append(snack)
        snack.open = True
        page.update()
        return
    except Exception:
        pass
    # Pre-0.21 fallback
    try:
        page.snack_bar = snack
        snack.open = True
        page.update()
    except Exception:
        pass  # Best effort - snackbar is non-critical