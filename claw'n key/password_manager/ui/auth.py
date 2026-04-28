"""
auth.py
Login, first-run setup, recovery key display, and forgot-password screens.
"""

import flet as ft
from .theme import ThemeManager
from .widgets import show_snack, set_clipboard


def build_auth_view(page: ft.Page, api, theme: ThemeManager,
                    mode: str, on_success):
    """
    mode: "setup" for first-run, "login" for returning users
    on_success: callback with no args, fired when auth completes
    """

    # We use a container ref so we can swap content without re-rendering the whole page
    content_holder = ft.Ref[ft.Container]()

    def show_setup():
        """First-run: create master password."""
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
        )

        def submit(_=None):
            if pwd_field.value != confirm_field.value:
                show_snack(page, "Passwords do not match.", error=True)
                return
            result = api.setup_master(pwd_field.value)
            if not result["ok"]:
                show_snack(page, result["error"], error=True)
                pwd_field.value = ""
                confirm_field.value = ""
                page.update()
                return
            # Show recovery key screen
            show_recovery_key(result["recovery_key"], is_new_setup=True)

        pwd_field.on_submit = submit
        confirm_field.on_submit = submit

        card = _build_card(
            theme,
            icon=ft.Icons.LOCK_ROUNDED,
            title="Create Master Password",
            subtitle=(
                "This is the only password you'll need to remember. "
                "It cannot be recovered without a recovery key."
            ),
            controls=[
                pwd_field,
                confirm_field,
                ft.Container(height=4),
                ft.FilledButton(
                    "Create Vault",
                    on_click=submit,
                    width=340,
                    height=44,
                    style=ft.ButtonStyle(
                        bgcolor=theme.c["primary"],
                        color="#ffffff",
                        shape=ft.RoundedRectangleBorder(radius=10),
                    ),
                ),
            ],
        )
        _set_content(card)

    def show_login():
        """Returning user: enter master password."""
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

        def submit(_=None):
            result = api.login(pwd_field.value)
            if not result["ok"]:
                show_snack(page, result["error"], error=True)
                pwd_field.value = ""
                page.update()
                return
            on_success()

        pwd_field.on_submit = submit

        card = _build_card(
            theme,
            icon=ft.Icons.LOCK_ROUNDED,
            title="Unlock Your Vault",
            subtitle="Enter your master password to continue.",
            controls=[
                pwd_field,
                ft.Container(height=4),
                ft.FilledButton(
                    "Unlock",
                    on_click=submit,
                    width=340,
                    height=44,
                    style=ft.ButtonStyle(
                        bgcolor=theme.c["primary"],
                        color="#ffffff",
                        shape=ft.RoundedRectangleBorder(radius=10),
                    ),
                ),
                ft.Container(height=8),
                ft.TextButton(
                    "Forgot Password?",
                    on_click=lambda _: show_forgot_password(),
                    style=ft.ButtonStyle(color=theme.c["text_muted"]),
                ),
            ],
        )
        _set_content(card)

    def show_recovery_key(recovery_key: str, is_new_setup: bool = False):
        """Display the recovery key to the user — shown only once."""

        key_field = ft.TextField(
            value=recovery_key,
            read_only=True,
            text_align=ft.TextAlign.CENTER,
            text_style=ft.TextStyle(
                font_family="Consolas",
                size=16,
                weight=ft.FontWeight.BOLD,
            ),
            border_radius=10,
            filled=True,
            bgcolor=theme.c["surface_2"],
            border_color=theme.c["primary"],
            width=380,
        )

        def copy_key(_):
            set_clipboard(page, recovery_key)
            show_snack(page, "Recovery key copied to clipboard!")

        def confirm(_):
            on_success()

        card = _build_card(
            theme,
            icon=ft.Icons.KEY_ROUNDED,
            title="\U0001f43e Your Recovery Key",
            subtitle=(
                "Write this down somewhere safe! "
                "If you forget your master password, this is the ONLY way to recover your vault. "
                "It will NOT be shown again."
            ),
            controls=[
                ft.Container(height=8),
                key_field,
                ft.Container(height=8),
                ft.Row(
                    [
                        ft.OutlinedButton(
                            "\U0001f4cb Copy to Clipboard",
                            on_click=copy_key,
                            style=ft.ButtonStyle(
                                color=theme.c["primary"],
                                side=ft.BorderSide(1, theme.c["border"]),
                                shape=ft.RoundedRectangleBorder(radius=10),
                            ),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Container(height=12),
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.WARNING_AMBER, color="#FFA726", size=18),
                            ft.Text(
                                "This key will NOT be shown again!",
                                size=12,
                                color="#FFA726",
                                weight=ft.FontWeight.W_600,
                            ),
                        ],
                        spacing=6,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    bgcolor=theme.c["surface_2"],
                    border=ft.border.all(1, "#FFA726"),
                    border_radius=8,
                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                ),
                ft.Container(height=12),
                ft.FilledButton(
                    "\u2705 I've Saved My Recovery Key",
                    on_click=confirm,
                    width=340,
                    height=44,
                    style=ft.ButtonStyle(
                        bgcolor=theme.c["primary"],
                        color="#ffffff",
                        shape=ft.RoundedRectangleBorder(radius=10),
                    ),
                ),
            ],
            width=480,
        )
        _set_content(card)

    def show_forgot_password():
        """Forgot password: enter recovery key + new password."""
        recovery_field = ft.TextField(
            label="Recovery Key",
            hint_text="RKEY-XXXX-XXXX-XXXX-XXXX-XXXX",
            text_style=ft.TextStyle(font_family="Consolas"),
            border_radius=10,
            filled=True,
            bgcolor=theme.c["surface_2"],
            border_color=theme.c["border"],
            focused_border_color=theme.c["primary"],
            width=380,
        )
        new_pwd_field = ft.TextField(
            label="New master password",
            password=True,
            can_reveal_password=True,
            border_radius=10,
            filled=True,
            bgcolor=theme.c["surface_2"],
            border_color=theme.c["border"],
            focused_border_color=theme.c["primary"],
            width=380,
        )
        confirm_pwd_field = ft.TextField(
            label="Confirm new password",
            password=True,
            can_reveal_password=True,
            border_radius=10,
            filled=True,
            bgcolor=theme.c["surface_2"],
            border_color=theme.c["border"],
            focused_border_color=theme.c["primary"],
            width=380,
        )

        def submit(_=None):
            if new_pwd_field.value != confirm_pwd_field.value:
                show_snack(page, "Passwords do not match.", error=True)
                return
            recovery_key = (recovery_field.value or "").strip().upper()
            if not recovery_key:
                show_snack(page, "Please enter your recovery key.", error=True)
                return
            result = api.recover_with_key(recovery_key, new_pwd_field.value)
            if not result["ok"]:
                show_snack(page, result["error"], error=True)
                return
            # Show the NEW recovery key
            show_snack(page, "\U0001f389 Password reset successful!")
            show_recovery_key(result["new_recovery_key"], is_new_setup=False)

        recovery_field.on_submit = submit
        confirm_pwd_field.on_submit = submit

        card = _build_card(
            theme,
            icon=ft.Icons.HEALTH_AND_SAFETY,
            title="Recover Your Vault",
            subtitle=(
                "Enter the recovery key you saved when you created your vault, "
                "then choose a new master password."
            ),
            controls=[
                recovery_field,
                ft.Container(height=4),
                new_pwd_field,
                confirm_pwd_field,
                ft.Container(height=4),
                ft.FilledButton(
                    "Reset Password",
                    on_click=submit,
                    width=380,
                    height=44,
                    style=ft.ButtonStyle(
                        bgcolor=theme.c["primary"],
                        color="#ffffff",
                        shape=ft.RoundedRectangleBorder(radius=10),
                    ),
                ),
                ft.Container(height=8),
                ft.TextButton(
                    "\u2190 Back to Login",
                    on_click=lambda _: show_login(),
                    style=ft.ButtonStyle(color=theme.c["text_muted"]),
                ),
            ],
            width=460,
        )
        _set_content(card)

    # --- Helper to swap the visible card ---

    def _set_content(card):
        wrapper = content_holder.current
        wrapper.content = ft.Column(
            [card],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        page.update()

    # --- Outer container ---

    initial_content = ft.Column([], alignment=ft.MainAxisAlignment.CENTER,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    view = ft.Container(
        content=initial_content,
        ref=content_holder,
        alignment=ft.Alignment.CENTER,
        expand=True,
        bgcolor=theme.c["bg"],
    )

    # Show the right screen on first render
    if mode == "setup":
        show_setup()
    else:
        show_login()

    return view


def _build_card(theme, icon, title, subtitle, controls, width=420):
    """Helper to build a styled auth card."""
    return ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [ft.Icon(icon, size=36, color=theme.c["primary"])],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Text(
                    title,
                    size=22,
                    weight=ft.FontWeight.BOLD,
                    color=theme.c["text"],
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    subtitle,
                    size=13,
                    color=theme.c["text_muted"],
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=8),
            ] + controls,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
            tight=True,
        ),
        bgcolor=theme.c["surface"],
        padding=32,
        border_radius=16,
        border=ft.border.all(1, theme.c["border"]),
        width=width,
    )