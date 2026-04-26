"""
auth.py
Login and first-run setup screen.
"""

import flet as ft
from .theme import ThemeManager
from .widgets import show_snack


def build_auth_view(page: ft.Page, api, theme: ThemeManager,
                    mode: str, on_success):
    """
    mode: "setup" for first-run, "login" for returning users
    on_success: callback with no args, fired when auth completes
    """
    is_setup = mode == "setup"

    pwd_field = ft.TextField(
        label="Master password",
        password=True,
        can_reveal_password=True,
        border_radius=10,
        filled=True,
        bgcolor=theme.c["surface_2"],
        border_color=theme.c["border"],
        focused_border_color=theme.c["primary"],
        width=340,
    )
    confirm_field = ft.TextField(
        label="Confirm password",
        password=True,
        can_reveal_password=True,
        border_radius=10,
        filled=True,
        bgcolor=theme.c["surface_2"],
        border_color=theme.c["border"],
        focused_border_color=theme.c["primary"],
        width=340,
        visible=is_setup,
    )

    def submit(_=None):
        if is_setup and pwd_field.value != confirm_field.value:
            show_snack(page, "Passwords do not match.", error=True)
            return
        fn = api.setup_master if is_setup else api.login
        result = fn(pwd_field.value)
        if not result["ok"]:
            show_snack(page, result["error"], error=True)
            pwd_field.value = ""
            if is_setup:
                confirm_field.value = ""
            page.update()
            return
        on_success()

    pwd_field.on_submit = submit
    confirm_field.on_submit = submit

    submit_btn = ft.FilledButton(
        "Create Vault" if is_setup else "Unlock",
        on_click=submit,
        width=340,
        height=44,
        style=ft.ButtonStyle(
            bgcolor=theme.c["primary"],
            color="#ffffff",
            shape=ft.RoundedRectangleBorder(radius=10),
        ),
    )

    card = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [ft.Icon(ft.Icons.LOCK_ROUNDED, size=36, color=theme.c["primary"])],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Text(
                    "Create Master Password" if is_setup else "Unlock Your Vault",
                    size=22,
                    weight=ft.FontWeight.BOLD,
                    color=theme.c["text"],
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "This is the only password you'll need to remember. "
                    "It cannot be recovered."
                    if is_setup
                    else "Enter your master password to continue.",
                    size=13,
                    color=theme.c["text_muted"],
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=8),
                pwd_field,
                confirm_field,
                ft.Container(height=4),
                submit_btn,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
            tight=True,
        ),
        bgcolor=theme.c["surface"],
        padding=32,
        border_radius=16,
        border=ft.border.all(1, theme.c["border"]),
        width=420,
    )

    return ft.Container(
        content=ft.Column(
            [card],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        alignment=ft.Alignment.CENTER,
        expand=True,
        bgcolor=theme.c["bg"],
    )
