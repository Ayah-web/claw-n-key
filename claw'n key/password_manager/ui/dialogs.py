"""
dialogs.py
Modal dialogs: add/edit entry, view entry, standalone generator.

Each dialog is built on demand via a factory, so theme changes apply
immediately to the next dialog that opens.
"""

import flet as ft
from .theme import ThemeManager
from .widgets import (
    strength_badge, show_snack,
    open_dialog, close_dialog, set_clipboard,
)


def _styled_textfield(label, theme: ThemeManager, **kwargs):
    return ft.TextField(
        label=label,
        border_radius=10,
        filled=True,
        bgcolor=theme.c["surface_2"],
        border_color=theme.c["border"],
        focused_border_color=theme.c["primary"],
        **kwargs,
    )


def entry_form_dialog(page, api, theme: ThemeManager, on_saved,
                      existing=None, pet=None, cat_widget=None,
                      refresh_pet=None):
    """
    Single dialog for both 'Add' and 'Edit'.
    existing: None for new, or the entry dict from api.get_entry
    pet: PetState instance (optional)
    cat_widget: CatWidget instance (optional)
    refresh_pet: callback to refresh pet panel (optional)
    """
    is_edit = existing is not None

    service = _styled_textfield(
        "Service", theme,
        value=existing["service"] if is_edit else "",
        autofocus=not is_edit,
    )
    username = _styled_textfield(
        "Username / email (optional)", theme,
        value=existing["username"] if is_edit else "",
    )
    password = _styled_textfield(
        "Password", theme,
        value=existing["password"] if is_edit else "",
        password=True,
        can_reveal_password=True,
    )

    category = ft.Dropdown(
        label="Category",
        value=existing["category"] if is_edit else "Personal",
        options=[ft.dropdown.Option(c) for c in api.categories()],
        border_radius=10,
        filled=True,
        bgcolor=theme.c["surface_2"],
        border_color=theme.c["border"],
        focused_border_color=theme.c["primary"],
    )

    strength_row = ft.Row([], spacing=8)

    def refresh_strength():
        strength_row.controls.clear()
        if password.value:
            label = api.check_strength(password.value)
            strength_row.controls.append(strength_badge(label, theme))
            # Show point preview
            from backend.password_tools import strength_points
            pts = strength_points(label)
            if pts > 0:
                strength_row.controls.append(
                    ft.Text(
                        f"+{pts}★",
                        size=12,
                        color="#e5c14a",
                        weight=ft.FontWeight.W_600,
                    )
                )
        page.update()

    def on_pwd_change(_):
        refresh_strength()

    password.on_change = on_pwd_change

    def do_generate(_):
        password.value = api.generate_password(16, True)
        refresh_strength()
        page.update()

    generate_btn = ft.TextButton(
        "Generate strong password",
        icon=ft.Icons.AUTO_AWESOME,
        on_click=do_generate,
        style=ft.ButtonStyle(color=theme.c["primary"]),
    )

    def save(_):
        if not service.value or not password.value:
            show_snack(page, "Service and password are required.", error=True)
            return
        if is_edit:
            result = api.update_entry(
                existing["id"],
                service.value.strip(),
                (username.value or "").strip(),
                password.value,
                category.value,
            )
        else:
            result = api.add_entry(
                service.value.strip(),
                (username.value or "").strip(),
                password.value,
                category.value,
            )
        if not result["ok"]:
            show_snack(page, result["error"], error=True)
            return

        # --- Award pet points ---
        if pet and not is_edit:
            pts = result.get("points", 0)
            strength = result.get("strength", "")
            if pts > 0:
                pet.award_points(pts, reason=f"Added {service.value.strip()} ({strength})")
                show_snack(page, f"🐱 +{pts} pet points! ({strength} password)")
                if cat_widget:
                    cat_widget.trigger_happy()
                if refresh_pet:
                    refresh_pet()
            else:
                show_snack(page, "Entry saved. (Weak password = no pet points 😿)")
        elif pet and is_edit:
            # Award 1 point for updating (encourages password rotation)
            pet.award_points(1, reason=f"Updated {service.value.strip()}")
            if cat_widget:
                cat_widget.trigger_happy()
            if refresh_pet:
                refresh_pet()
        # --- End pet points ---

        close_dialog(page, dlg)
        if not pet or (pet and is_edit):
            show_snack(page, "Entry saved.")
        on_saved()

    def cancel(_):
        close_dialog(page, dlg)

    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text("Edit Entry" if is_edit else "Add Entry"),
        bgcolor=theme.c["surface"],
        content=ft.Container(
            width=380,
            content=ft.Column(
                [service, username, password, generate_btn, strength_row, category],
                tight=True,
                spacing=12,
            ),
        ),
        actions=[
            ft.TextButton("Cancel", on_click=cancel),
            ft.FilledButton(
                "Save",
                on_click=save,
                style=ft.ButtonStyle(
                    bgcolor=theme.c["primary"], color="#ffffff"
                ),
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    if is_edit and existing.get("password"):
        refresh_strength()

    open_dialog(page, dlg)


def view_entry_dialog(page, api, theme: ThemeManager, entry_id, on_changed):
    """View an entry with reveal / copy / edit / delete."""
    r = api.get_entry(entry_id)
    if not r["ok"]:
        show_snack(page, r["error"], error=True)
        return
    entry = r["entry"]

    revealed = {"value": False}
    pwd_display = ft.Text(
        "•" * 12,
        font_family="Consolas",
        size=15,
        selectable=True,
        color=theme.c["text"],
    )
    reveal_btn = ft.IconButton(
        icon=ft.Icons.VISIBILITY_OUTLINED,
        tooltip="Show password",
        icon_color=theme.c["text_muted"],
    )

    def toggle_reveal(_):
        revealed["value"] = not revealed["value"]
        pwd_display.value = entry["password"] if revealed["value"] else "•" * 12
        reveal_btn.icon = (
            ft.Icons.VISIBILITY_OFF_OUTLINED if revealed["value"]
            else ft.Icons.VISIBILITY_OUTLINED
        )
        reveal_btn.tooltip = (
            "Hide password" if revealed["value"] else "Show password"
        )
        page.update()

    reveal_btn.on_click = toggle_reveal

    def copy_pwd(_):
        set_clipboard(page, entry["password"])
        show_snack(page, "Password copied to clipboard.")

    def do_edit(_):
        close_dialog(page, dlg)
        entry_form_dialog(page, api, theme, on_changed, existing=entry)

    def do_delete(_):
        close_dialog(page, dlg)
        _confirm_delete(page, api, theme, entry, on_changed)

    def field_row(label, value):
        return ft.Row(
            [
                ft.Text(label, width=80, size=13, color=theme.c["text_muted"]),
                ft.Text(value, size=14, color=theme.c["text"], selectable=True,
                        expand=True),
            ],
        )

    dlg = ft.AlertDialog(
        modal=True,
        bgcolor=theme.c["surface"],
        title=ft.Row(
            [
                ft.Icon(ft.Icons.KEY_ROUNDED, color=theme.c["primary"]),
                ft.Text(entry["service"]),
            ],
            spacing=8,
        ),
        content=ft.Container(
            width=400,
            content=ft.Column(
                [
                    field_row("Username", entry["username"] or "—"),
                    field_row("Category", entry["category"]),
                    ft.Row(
                        [
                            ft.Text("Password", width=80, size=13,
                                    color=theme.c["text_muted"]),
                            pwd_display,
                            reveal_btn,
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(height=4),
                    ft.Row([strength_badge(entry["strength"], theme)]),
                ],
                tight=True,
                spacing=10,
            ),
        ),
        actions=[
            ft.TextButton(
                "Delete",
                on_click=do_delete,
                style=ft.ButtonStyle(color=theme.c["danger"]),
            ),
            ft.TextButton("Edit", on_click=do_edit),
            ft.TextButton("Copy", icon=ft.Icons.COPY, on_click=copy_pwd),
            ft.TextButton("Close", on_click=lambda _: close_dialog(page, dlg)),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    open_dialog(page, dlg)


def _confirm_delete(page, api, theme: ThemeManager, entry, on_changed):
    def do_it(_):
        api.delete_entry(entry["id"])
        close_dialog(page, dlg)
        show_snack(page, f"Deleted {entry['service']}.")
        on_changed()

    dlg = ft.AlertDialog(
        modal=True,
        bgcolor=theme.c["surface"],
        title=ft.Text("Delete entry?"),
        content=ft.Text(
            f"This will permanently delete the entry for "
            f"\"{entry['service']}\". This cannot be undone.",
            color=theme.c["text"],
        ),
        actions=[
            ft.TextButton("Cancel", on_click=lambda _: close_dialog(page, dlg)),
            ft.FilledButton(
                "Delete",
                on_click=do_it,
                style=ft.ButtonStyle(bgcolor=theme.c["danger"], color="#ffffff"),
            ),
        ],
    )
    open_dialog(page, dlg)


def generator_dialog(page, api, theme: ThemeManager):
    """Standalone password generator (no saving)."""
    length_val = {"n": 16}
    symbols_val = {"on": True}

    length_label = ft.Text(f"Length: {length_val['n']}", color=theme.c["text"])
    slider = ft.Slider(
        min=8, max=64, divisions=56,
        value=length_val["n"],
        active_color=theme.c["primary"],
    )
    symbols_switch = ft.Switch(
        label="Include symbols",
        value=True,
        active_color=theme.c["primary"],
    )

    result_text = ft.TextField(
        value="",
        read_only=True,
        multiline=False,
        text_style=ft.TextStyle(font_family="Consolas", size=14),
        border_radius=10,
        filled=True,
        bgcolor=theme.c["surface_2"],
        border_color=theme.c["border"],
    )
    strength_row = ft.Row([], spacing=8)

    def on_slider(e):
        length_val["n"] = int(e.control.value)
        length_label.value = f"Length: {length_val['n']}"
        page.update()
    slider.on_change = on_slider

    def on_symbols(e):
        symbols_val["on"] = bool(e.control.value)
    symbols_switch.on_change = on_symbols

    def do_generate(_):
        pwd = api.generate_password(length_val["n"], symbols_val["on"])
        result_text.value = pwd
        strength_row.controls = [strength_badge(api.check_strength(pwd), theme)]
        page.update()

    def do_copy(_):
        if not result_text.value:
            return
        set_clipboard(page, result_text.value)
        show_snack(page, "Copied to clipboard.")

    dlg = ft.AlertDialog(
        modal=True,
        bgcolor=theme.c["surface"],
        title=ft.Text("Password Generator"),
        content=ft.Container(
            width=400,
            content=ft.Column(
                [
                    length_label,
                    slider,
                    symbols_switch,
                    ft.FilledButton(
                        "Generate",
                        icon=ft.Icons.AUTO_AWESOME,
                        on_click=do_generate,
                        style=ft.ButtonStyle(
                            bgcolor=theme.c["primary"], color="#ffffff",
                        ),
                    ),
                    result_text,
                    strength_row,
                ],
                tight=True,
                spacing=12,
            ),
        ),
        actions=[
            ft.TextButton("Copy", on_click=do_copy),
            ft.TextButton("Close", on_click=lambda _: close_dialog(page, dlg)),
        ],
    )
    open_dialog(page, dlg)
    do_generate(None)