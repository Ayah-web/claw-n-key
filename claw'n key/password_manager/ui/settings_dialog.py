"""
settings_dialog.py
Settings dialog for Claw'n Key.
Allows users to configure auto-lock timeout, pet name, theme, and more.
Includes Reset Pet and Delete Account options.
"""

import flet as ft
from .theme import ThemeManager
from .widgets import show_snack, open_dialog, close_dialog


def settings_dialog(page, api, pet, theme: ThemeManager, session_mgr,
                    on_theme_toggle, cat_widget=None, refresh_pet=None,
                    on_reset_account=None):
    """Open the settings dialog."""

    # --- Auto-lock timeout ---
    timeout_options = {
        "1 minute": 60,
        "2 minutes": 120,
        "5 minutes": 300,
        "10 minutes": 600,
        "15 minutes": 900,
        "30 minutes": 1800,
        "Never": 0,
    }

    current_timeout = session_mgr.timeout if session_mgr else 300
    current_label = "5 minutes"
    for label, val in timeout_options.items():
        if val == current_timeout:
            current_label = label
            break

    # ✅ FIX: switched to DropdownM2 to match vault.py
    timeout_dropdown = ft.DropdownM2(
        value=current_label,
        options=[ft.dropdownm2.Option(key=k, text=k) for k in timeout_options],
        label="Auto-lock after",
        border_radius=10,
        filled=True,
        bgcolor=theme.c["surface_2"],
        border_color=theme.c["border"],
        focused_border_color=theme.c["primary"],
        color=theme.c["text"],
        width=250,
    )

    # --- Theme toggle ---
    theme_switch = ft.Switch(
        label="Dark Mode" if theme.mode == "dark" else "Light Mode",
        value=(theme.mode == "dark"),
        active_color=theme.c["primary"],
    )

    # --- Pet name ---
    pet_name_field = ft.TextField(
        label="Pet Name",
        value=pet.pet_name if pet else "Whiskers",
        border_radius=10,
        filled=True,
        bgcolor=theme.c["surface_2"],
        border_color=theme.c["border"],
        focused_border_color=theme.c["primary"],
        width=250,
    )

    # --- Hotkey info ---
    hotkey_info = ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.KEYBOARD, color=theme.c["primary"], size=18),
                ft.Column(
                    [
                        ft.Text("Global Hotkey", size=13,
                                weight=ft.FontWeight.W_600,
                                color=theme.c["text"]),
                        ft.Text("Ctrl + Shift + K — Bring app to front",
                                size=12, color=theme.c["text_muted"]),
                    ],
                    spacing=2,
                ),
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=theme.c["surface_2"],
        border=ft.border.all(1, theme.c["border"]),
        border_radius=10,
        padding=12,
    )

    # --- App info ---
    app_info = ft.Container(
        content=ft.Column(
            [
                ft.Text("🐾 Claw'n Key 🔑", size=16,
                        weight=ft.FontWeight.BOLD,
                        color=theme.c["primary"]),
                ft.Text("Your passwords, guarded by a cat.", size=12,
                        color=theme.c["text_muted"]),
                ft.Text("Encryption: AES-256 via Fernet (PBKDF2 key derivation)",
                        size=11, color=theme.c["text_muted"]),
                ft.Text("All data stored locally in vault.db",
                        size=11, color=theme.c["text_muted"]),
            ],
            spacing=4,
        ),
        bgcolor=theme.c["surface_2"],
        border=ft.border.all(1, theme.c["border"]),
        border_radius=10,
        padding=12,
    )

    # --- Stats summary ---
    stats_items = []
    if pet:
        # ✅ FIX: removed coins line
        stats_items = [
            f"📝 Entries added: {pet.total_entries_added}",
            f"⭐ Total points earned: {pet.total_points_earned}",
            f"🍲 Times fed: {pet.times_fed}",
            f"🎾 Times played: {pet.times_played}",
            f"🐾 Times petted: {pet.times_petted}",
            f"🏆 Pet level: {pet.level}",
        ]

    stats_container = ft.Container(
        content=ft.Column(
            [
                ft.Text("Lifetime Stats", size=13,
                        weight=ft.FontWeight.W_600,
                        color=theme.c["text"]),
            ] + [
                ft.Text(s, size=12, color=theme.c["text_muted"])
                for s in stats_items
            ],
            spacing=4,
        ),
        bgcolor=theme.c["surface_2"],
        border=ft.border.all(1, theme.c["border"]),
        border_radius=10,
        padding=12,
        visible=bool(stats_items),
    )

    # --- Danger zone ---

    def on_reset_pet(_):
        """Reset pet stats only — passwords are kept."""
        confirm_dlg = ft.AlertDialog(
            modal=True,
            bgcolor=theme.c["surface"],
            title=ft.Text("Reset Pet?", color=theme.c["danger"]),
            content=ft.Text(
                # ✅ FIX: removed "coins" from this string
                "This resets your pet's stats, level and inventory. "
                "Your passwords will NOT be affected.",
                color=theme.c["text"],
            ),
            actions=[
                ft.TextButton("Cancel",
                              on_click=lambda _: close_dialog(page, confirm_dlg)),
                ft.FilledButton(
                    "Reset Pet",
                    on_click=lambda _: _do_reset_pet(confirm_dlg),
                    style=ft.ButtonStyle(
                        bgcolor=theme.c["danger"], color="#ffffff",
                    ),
                ),
            ],
        )
        open_dialog(page, confirm_dlg)

    def _do_reset_pet(confirm_dlg):
        close_dialog(page, confirm_dlg)
        if pet:
            pet.reset()
            if cat_widget:
                cat_widget.say("Starting fresh! Meow~", 3.0)
            if refresh_pet:
                refresh_pet()
        show_snack(page, "🐾 Pet has been reset!")

    def on_delete_account(_):
        """Wipe everything and restart from splash."""
        confirm_dlg = ft.AlertDialog(
            modal=True,
            bgcolor=theme.c["surface"],
            title=ft.Text("Delete Account?", color=theme.c["danger"]),
            content=ft.Column(
                [
                    ft.Text(
                        "This will permanently delete:",
                        color=theme.c["text"],
                        weight=ft.FontWeight.W_600,
                    ),
                    ft.Text(
                        "• All saved passwords\n"
                        "• Your master password\n"
                        "• Your recovery key\n"
                        "• Your pet and all its progress",
                        color=theme.c["danger"],
                        size=13,
                    ),
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.WARNING_AMBER,
                                        color="#FFA726", size=16),
                                ft.Text(
                                    "This CANNOT be undone!",
                                    size=12,
                                    color="#FFA726",
                                    weight=ft.FontWeight.W_600,
                                ),
                            ],
                            spacing=6,
                        ),
                        bgcolor=theme.c["surface_2"],
                        border=ft.border.all(1, "#FFA726"),
                        border_radius=8,
                        padding=ft.padding.symmetric(horizontal=10, vertical=8),
                    ),
                ],
                spacing=10,
                tight=True,
            ),
            actions=[
                ft.TextButton(
                    "Cancel",
                    on_click=lambda _: close_dialog(page, confirm_dlg),
                ),
                ft.FilledButton(
                    "Delete Everything",
                    on_click=lambda _: _do_delete_account(confirm_dlg),
                    style=ft.ButtonStyle(
                        bgcolor=theme.c["danger"], color="#ffffff",
                    ),
                ),
            ],
        )
        open_dialog(page, confirm_dlg)

    def _do_delete_account(confirm_dlg):
        close_dialog(page, confirm_dlg)
        close_dialog(page, dlg)
        if on_reset_account:
            on_reset_account()

    danger_zone = ft.Container(
        content=ft.Column(
            [
                ft.Text("Danger Zone", size=13,
                        weight=ft.FontWeight.W_600,
                        color=theme.c["danger"]),
                ft.Text(
                    "These actions cannot be undone.",
                    size=11,
                    color=theme.c["text_muted"],
                ),
                ft.Container(height=4),
                # Reset pet row
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text("Reset Pet", size=12,
                                        weight=ft.FontWeight.W_600,
                                        color=theme.c["text"]),
                                ft.Text("Resets pet stats only.\nPasswords kept.",
                                        size=11, color=theme.c["text_muted"]),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                        ft.OutlinedButton(
                            "Reset",
                            icon=ft.Icons.RESTART_ALT,
                            on_click=on_reset_pet,
                            style=ft.ButtonStyle(
                                color=theme.c["danger"],
                                side=ft.BorderSide(1, theme.c["danger"]),
                                shape=ft.RoundedRectangleBorder(radius=8),
                            ),
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Divider(color=theme.c["border"], height=1),
                # Delete account row
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text("Delete Account", size=12,
                                        weight=ft.FontWeight.W_600,
                                        color=theme.c["danger"]),
                                ft.Text(
                                    "Wipes all passwords, pet\nand account data.",
                                    size=11, color=theme.c["text_muted"],
                                ),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                        ft.FilledButton(
                            "Delete",
                            icon=ft.Icons.DELETE_FOREVER,
                            on_click=on_delete_account,
                            style=ft.ButtonStyle(
                                bgcolor=theme.c["danger"],
                                color="#ffffff",
                                shape=ft.RoundedRectangleBorder(radius=8),
                            ),
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            spacing=8,
        ),
        bgcolor=theme.c["surface_2"],
        border=ft.border.all(1, theme.c["danger"]),
        border_radius=10,
        padding=12,
    )

    # --- Save handler ---
    def on_save(_):
        changes = []

        if session_mgr:
            new_timeout = timeout_options.get(timeout_dropdown.value, 300)
            if new_timeout == 0:
                session_mgr.stop()
                changes.append("Auto-lock disabled")
            else:
                session_mgr.set_timeout(new_timeout)
                if not session_mgr.is_active:
                    session_mgr.start()
                changes.append(f"Auto-lock: {timeout_dropdown.value}")
            api.set_setting("auto_lock_timeout", str(new_timeout))

        if pet:
            new_name = (pet_name_field.value or "").strip()
            if new_name and new_name != pet.pet_name:
                pet.pet_name = new_name
                pet.save()
                if cat_widget:
                    cat_widget.say(f"I'm {new_name} now! Nya~", 3.0)
                if refresh_pet:
                    refresh_pet()
                changes.append(f"Pet renamed to {new_name}")

        is_dark = theme_switch.value
        current_is_dark = (theme.mode == "dark")
        if is_dark != current_is_dark:
            close_dialog(page, dlg)
            on_theme_toggle()
            changes.append(f"Theme: {'Dark' if is_dark else 'Light'}")
            return

        if changes:
            show_snack(page, "✅ " + " | ".join(changes))
        else:
            show_snack(page, "No changes made.")

        close_dialog(page, dlg)

    # --- Section helper ---
    def section_header(icon, text):
        return ft.Row(
            [
                ft.Icon(icon, size=16, color=theme.c["primary"]),
                ft.Text(text, size=14, weight=ft.FontWeight.W_600,
                        color=theme.c["text"]),
            ],
            spacing=6,
        )

    # --- Dialog ---
    dlg = ft.AlertDialog(
        modal=True,
        bgcolor=theme.c["surface"],
        title=ft.Row(
            [
                ft.Icon(ft.Icons.SETTINGS, color=theme.c["primary"]),
                ft.Text("Settings", color=theme.c["text"]),
            ],
            spacing=8,
        ),
        content=ft.Container(
            width=460,
            height=480,
            content=ft.Column(
                [
                    section_header(ft.Icons.SECURITY, "Security"),
                    timeout_dropdown,
                    hotkey_info,
                    ft.Divider(color=theme.c["border"], height=1),
                    section_header(ft.Icons.PALETTE, "Appearance"),
                    theme_switch,
                    ft.Divider(color=theme.c["border"], height=1),
                    section_header(ft.Icons.PETS, "Pet"),
                    pet_name_field,
                    ft.Divider(color=theme.c["border"], height=1),
                    app_info,
                    stats_container,
                    ft.Divider(color=theme.c["border"], height=1),
                    danger_zone,
                ],
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
            ),
        ),
        actions=[
            ft.TextButton(
                "Cancel",
                on_click=lambda _: close_dialog(page, dlg),
            ),
            ft.FilledButton(
                "Save",
                icon=ft.Icons.SAVE,
                on_click=on_save,
                style=ft.ButtonStyle(
                    bgcolor=theme.c["primary"],
                    color="#ffffff",
                    shape=ft.RoundedRectangleBorder(radius=8),
                ),
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    open_dialog(page, dlg)