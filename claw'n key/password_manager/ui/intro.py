"""
intro.py
First-launch intro scene where the cat greets the user
and lets them choose a name before setting up the vault.
"""

import flet as ft
import asyncio
import random

from .theme import ThemeManager
from .cat_widget import CatWidget


def build_intro_view(page: ft.Page, pet, theme: ThemeManager, on_complete):
    """
    on_complete: callback with no args, fired when user finishes naming the cat
                 and is ready to proceed to master password setup.
    """

    # --- Animated cat (big and center stage) ---
    cat_widget = CatWidget(theme_mode=theme.mode, display_width=260, display_height=200)

    # --- Dialogue system ---
    dialogue_text = ft.Text(
        "",
        size=16,
        color=theme.c["text"],
        text_align=ft.TextAlign.CENTER,
    )

    dialogue_container = ft.Container(
        content=dialogue_text,
        bgcolor=theme.c["surface_2"],
        border=ft.border.all(1, theme.c["border"]),
        border_radius=16,
        padding=ft.padding.symmetric(horizontal=24, vertical=14),
        width=440,
        visible=False,
    )

    # --- Name input (hidden initially) ---
    name_field = ft.TextField(
        label="Name your cat",
        hint_text="e.g. Whiskers, Luna, Shadow...",
        border_radius=10,
        filled=True,
        bgcolor=theme.c["surface_2"],
        border_color=theme.c["border"],
        focused_border_color=theme.c["primary"],
        text_align=ft.TextAlign.CENTER,
        width=300,
        visible=False,
    )

    confirm_btn = ft.FilledButton(
        "That's my name!",
        icon=ft.Icons.PETS,
        visible=False,
        width=300,
        height=44,
        style=ft.ButtonStyle(
            bgcolor=theme.c["primary"],
            color="#ffffff",
            shape=ft.RoundedRectangleBorder(radius=10),
        ),
    )

    skip_btn = ft.TextButton(
        "Keep 'Whiskers'",
        visible=False,
        style=ft.ButtonStyle(
            color=theme.c["text_muted"],
        ),
    )

    # --- Title ---
    title_text = ft.Text(
        "",
        size=28,
        weight=ft.FontWeight.BOLD,
        color=theme.c["primary"],
        text_align=ft.TextAlign.CENTER,
    )

    subtitle_text = ft.Text(
        "",
        size=13,
        color=theme.c["text_muted"],
        text_align=ft.TextAlign.CENTER,
    )

    # --- State for name confirmation ---
    _intro_state = {"waiting_for_name": False, "done": False}

    # --- Async typewriter effect ---
    async def typewrite(text_control, message, delay=0.04):
        """Simulate typing effect character by character."""
        text_control.value = ""
        page.update()
        for i, ch in enumerate(message):
            text_control.value = message[:i + 1]
            try:
                page.update()
            except Exception:
                pass
            await asyncio.sleep(delay)

    # --- Async intro sequence ---
    async def run_intro_sequence():
        """Run the animated intro sequence."""
        await asyncio.sleep(0.5)

        # Step 1: Show title
        title_text.value = "\U0001f43e Claw'n Key \U0001f511"
        page.update()
        await asyncio.sleep(0.8)

        subtitle_text.value = "Your passwords, guarded by a cat."
        page.update()
        await asyncio.sleep(1.5)

        # Step 2: Cat says hello
        dialogue_container.visible = True
        page.update()
        await asyncio.sleep(0.3)

        greetings = [
            "Mrrp? Oh! A new human!",
            "Hello there! I've been waiting for you~",
            "I'm going to be your personal vault guardian!",
            "But first... I need a name!",
        ]

        for i, msg in enumerate(greetings):
            await typewrite(dialogue_text, msg, delay=0.035)
            await asyncio.sleep(1.5)

            # Cat does cute things between lines
            if i == 0:
                cat_widget.trigger_happy()
            elif i == 1:
                cat_widget.trigger_pet()
            elif i == 2:
                cat_widget.trigger_play()

        # Step 3: Show name input
        await asyncio.sleep(0.3)
        name_field.visible = True
        confirm_btn.visible = True
        skip_btn.visible = True
        _intro_state["waiting_for_name"] = True
        page.update()

    # --- Async finalize sequence ---
    async def run_finalize_sequence(chosen_name):
        """Run the post-naming sequence."""
        pet.pet_name = chosen_name
        pet.is_first_launch = False
        pet.save()

        # Hide input controls
        name_field.visible = False
        confirm_btn.visible = False
        skip_btn.visible = False
        page.update()

        # Cat reacts to name
        reactions = [
            f"{chosen_name}... I love it! *purrs loudly*",
            f"Call me {chosen_name}! Let's secure some passwords!",
            f"{chosen_name} reporting for duty! *salutes with paw*",
        ]
        cat_widget.trigger_happy()
        chosen_reaction = random.choice(reactions)
        await typewrite(dialogue_text, chosen_reaction, delay=0.035)
        await asyncio.sleep(2.0)

        # Final message
        await typewrite(dialogue_text, "Now let's set up your master password!", delay=0.035)
        await asyncio.sleep(1.5)

        # Clean up cat animation and proceed
        cat_widget.stop()
        _intro_state["done"] = True
        on_complete()

    # --- Name confirmation handlers ---
    def on_confirm(_):
        if not _intro_state["waiting_for_name"] or _intro_state["done"]:
            return
        chosen_name = name_field.value.strip()
        if not chosen_name:
            name_field.error_text = "Give me a name! Meow!"
            page.update()
            return
        name_field.error_text = None
        _intro_state["waiting_for_name"] = False

        async def _finalize():
            await run_finalize_sequence(chosen_name)
        page.run_task(_finalize)

    def on_skip(_):
        if not _intro_state["waiting_for_name"] or _intro_state["done"]:
            return
        _intro_state["waiting_for_name"] = False

        async def _finalize_default():
            await run_finalize_sequence("Whiskers")
        page.run_task(_finalize_default)

    def on_name_submit(_):
        on_confirm(None)

    confirm_btn.on_click = on_confirm
    skip_btn.on_click = on_skip
    name_field.on_submit = on_name_submit

    # --- Layout ---
    card = ft.Container(
        content=ft.Column(
            [
                title_text,
                subtitle_text,
                ft.Container(height=8),
                cat_widget.container,
                ft.Container(height=4),
                dialogue_container,
                ft.Container(height=12),
                name_field,
                ft.Container(height=4),
                confirm_btn,
                skip_btn,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=6,
            tight=True,
        ),
        bgcolor=theme.c["surface"],
        padding=40,
        border_radius=20,
        border=ft.border.all(1, theme.c["border"]),
        width=500,
    )

    view = ft.Container(
        content=ft.Column(
            [card],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        alignment=ft.Alignment(0, 0),
        expand=True,
        bgcolor=theme.c["bg"],
    )

    # Start cat animation and intro sequence
    cat_widget.start(page)
    page.run_task(run_intro_sequence)

    return view