"""
splash.py
One-time welcome splash screen shown on very first launch.
The cat sleeps peacefully here before being awakened in the intro.
"""

import flet as ft
from .theme import ThemeManager
from .cat_widget import CatWidget


def build_splash_view(page: ft.Page, theme: ThemeManager,
                      on_complete, on_theme_toggle):
    """
    Shown once ever on first launch, before the intro sequence.
    on_complete: callback to proceed to intro
    on_theme_toggle: callback to toggle theme
    """

    # Sleeping cat — locked to sleeping pose
    cat_widget = CatWidget(
        theme_mode=theme.mode,
        display_width=240,
        display_height=180,
        scale=3,
        initial_poses=["sleeping.side.sploot"],
    )

    # --- Logo ---
    logo = ft.Row(
        [
            ft.Icon(ft.Icons.LOCK_ROUNDED, size=48, color=theme.c["primary"]),
            ft.Text(
                "Claw'n Key",
                size=42,
                weight=ft.FontWeight.BOLD,
                color=theme.c["text"],
            ),
        ],
        spacing=12,
        alignment=ft.MainAxisAlignment.CENTER,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    tagline = ft.Text(
        "Your passwords, guarded by a cat.",
        size=16,
        color=theme.c["text_muted"],
        italic=True,
        text_align=ft.TextAlign.CENTER,
    )

    # --- Feature highlights ---
    def feature_chip(icon, label):
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(icon, size=16, color=theme.c["primary"]),
                    ft.Text(label, size=12, color=theme.c["text_muted"]),
                ],
                spacing=6,
                tight=True,
            ),
            bgcolor=theme.c["surface"],
            border=ft.border.all(1, theme.c["border"]),
            border_radius=20,
            padding=ft.padding.symmetric(horizontal=14, vertical=8),
        )

    features = ft.Row(
        [
            feature_chip(ft.Icons.SHIELD_ROUNDED, "AES-256 Encrypted"),
            feature_chip(ft.Icons.PETS, "Virtual Pet Companion"),
            feature_chip(ft.Icons.VISIBILITY_OFF_OUTLINED, "Zero-Knowledge"),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=10,
        wrap=True,
    )

    # --- Sleeping label ---
    sleeping_label = ft.Text(
        "Shhh... the guardian is sleeping 💤",
        size=11,
        color=theme.c["text_muted"],
        italic=True,
        text_align=ft.TextAlign.CENTER,
    )

    # --- Get Started button ---
    def on_start(_):
        cat_widget.stop()
        on_complete()

    start_btn = ft.FilledButton(
        "Get Started",
        icon=ft.Icons.ARROW_FORWARD_ROUNDED,
        width=260,
        height=50,
        on_click=on_start,
        style=ft.ButtonStyle(
            bgcolor=theme.c["primary"],
            color="#ffffff",
            shape=ft.RoundedRectangleBorder(radius=12),
        ),
    )

    # --- Theme toggle ---
    theme_btn = ft.IconButton(
        icon=(
            ft.Icons.LIGHT_MODE_OUTLINED
            if theme.mode == "dark"
            else ft.Icons.DARK_MODE_OUTLINED
        ),
        tooltip="Toggle theme",
        icon_color=theme.c["text_muted"],
        on_click=lambda _: on_theme_toggle(),
    )

    # --- Card ---
    card = ft.Container(
        content=ft.Column(
            [
                logo,
                tagline,
                ft.Container(height=4),
                sleeping_label,
                cat_widget.container,
                ft.Container(height=4),
                features,
                ft.Container(height=20),
                start_btn,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
            tight=True,
        ),
        bgcolor=theme.c["surface"],
        padding=40,
        border_radius=20,
        border=ft.border.all(1, theme.c["border"]),
        width=560,
    )

    # --- Main layout ---
    view = ft.Container(
        content=ft.Column(
            [
                # Top bar with theme toggle
                ft.Row(
                    [
                        ft.Container(expand=True),
                        theme_btn,
                    ],
                    alignment=ft.MainAxisAlignment.END,
                ),
                # Main content centered
                ft.Container(
                    content=card,
                    expand=True,
                    alignment=ft.Alignment(0, -0.3),
                ),
            ],
            spacing=0,
            expand=True,
        ),
        expand=True,
        bgcolor=theme.c["bg"],
        padding=ft.padding.only(top=8, right=8),
    )

    # Start cat animation
    cat_widget.start(page)

    return view