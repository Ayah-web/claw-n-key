"""
dialogs.py
Modal dialogs: add/edit entry, view entry, standalone generator.

Each dialog is built on demand via a factory, so theme changes apply
immediately to the next dialog that opens.
Now includes: favorites toggle, stale badges, pet reward popups.
"""

import flet as ft
from .theme import ThemeManager
from .widgets import (
    strength_badge, stale_badge, favorite_star,
    show_snack, reward_snack,
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

    # Favorite checkbox (only for edit)
    fav_checkbox = None
    if is_edit:
        fav_checkbox = ft.Checkbox(
            label="\u2b50 Favorite",
            value=bool(existing.get("is_favorite", 0)),
            check_color=theme.c["primary"],
        )

    strength_row = ft.Row([], spacing=8)

    def refresh_strength():
        strength_row.controls.clear()
        if password.value:
            label = api.check_strength(password.value)
            strength_row.controls.append(strength_badge(label, theme))
            # Show point preview
            from backend.password_tools import strength_points, strength_tips
            pts = strength_points(label)
            if pts > 0:
                strength_row.controls.append(
                    ft.Text(
                        f"+{pts}\u2605",
                        size=12,
                        color="#e5c14a",
                        weight=ft.FontWeight.W_600,
                    )
                )
            # Show tips for weak passwords
            tips = strength_tips(password.value)
            if tips and label in ("Bad", "Not Good"):
                strength_row.controls.append(
                    ft.Text(
                        tips[0],
                        size=11,
                        color=theme.c["text_muted"],
                        italic=True,
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

    # Stale warning for edits
    stale_warning = None
    if is_edit and existing.get("is_stale"):
        stale_warning = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.WARNING_AMBER, color="#FFA726", size=18),
                    ft.Text(
                        "This password hasn't been changed in 30+ days!",
                        size=12, color="#FFA726",
                        weight=ft.FontWeight.W_600,
                    ),
                ],
                spacing=6,
            ),
            bgcolor=theme.c["surface_2"],
            border=ft.border.all(1, "#FFA726"),
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
        )

    def save(_):
        if not service.value or not password.value:
            show_snack(page, "Service and password are required.", error=True)
            return

        is_fav = None
        if fav_checkbox:
            is_fav = 1 if fav_checkbox.value else 0

        if is_edit:
            result = api.update_entry(
                existing["id"],
                service.value.strip(),
                (username.value or "").strip(),
                password.value,
                category.value,
                is_favorite=is_fav,
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

        # --- Award pet rewards ---
        if pet and not is_edit:
            pts = result.get("points", 0)
            strength = result.get("strength", "")
            tier = result.get("strength_tier", 0)
            reward = pet.award_points(pts, strength_tier=tier,
                                       reason=f"Added {service.value.strip()} ({strength})")
            if pts > 0:
                show_snack(page, f"\U0001f43e +{pts} points! ({strength} password)")
                if cat_widget:
                    cat_widget.trigger_happy()
                    if reward.get("item_drop"):
                        _, item_name, rarity = reward["item_drop"]
                        cat_widget.say(f"Ooh! Got {item_name}! ({rarity})", 4.0)
                    elif reward.get("level_ups"):
                        new_lvl = reward["level_ups"][-1]["new_level"]
                        cat_widget.say(f"LEVEL UP! I'm level {new_lvl}!", 4.0)
                    else:
                        cat_widget.trigger_password_added()
                # Show reward snack
                reward_snack(page, reward, pet.pet_name)
            else:
                show_snack(page, "Entry saved. (Weak password = no rewards \U0001f63f)")
                if cat_widget:
                    cat_widget.say("That password is weak...", 3.0)

            if refresh_pet:
                refresh_pet()

        elif pet and is_edit:
            was_stale = result.get("was_stale", False)
            pts = result.get("points", 0)
            tier = result.get("strength_tier", 0)

            # Award update points
            reward = pet.award_points(max(1, pts), strength_tier=tier,
                                       reason=f"Updated {service.value.strip()}")

            # Stale update bonus
            stale_reward = None
            if was_stale:
                stale_reward = pet.award_stale_update_bonus()
                show_snack(page, "\U0001f389 Stale password updated! Bonus rewards!")
                if cat_widget:
                    cat_widget.trigger_happy()
                    cat_widget.say("Thank you for updating! *purrs*", 3.0)
                if stale_reward:
                    reward_snack(page, stale_reward, pet.pet_name)
            else:
                if cat_widget:
                    cat_widget.trigger_happy()

            if refresh_pet:
                refresh_pet()

        # --- End pet rewards ---

        close_dialog(page, dlg)
        if not pet:
            show_snack(page, "Entry saved.")
        on_saved()

    def cancel(_):
        close_dialog(page, dlg)

    # Build content column
    content_controls = [service, username, password, generate_btn, strength_row, category]
    if stale_warning:
        content_controls.insert(0, stale_warning)
    if fav_checkbox:
        content_controls.append(fav_checkbox)

    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text("Edit Entry" if is_edit else "Add Entry"),
        bgcolor=theme.c["surface"],
        content=ft.Container(
            width=400,
            content=ft.Column(
                content_controls,
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


def view_entry_dialog(page, api, theme: ThemeManager, entry_id, on_changed,
                      pet=None, cat_widget=None, refresh_pet=None):
    """View an entry with reveal / copy / edit / delete / favorite."""
    r = api.get_entry(entry_id)
    if not r["ok"]:
        show_snack(page, r["error"], error=True)
        return
    entry = r["entry"]

    revealed = {"value": False}
    pwd_display = ft.Text(
        "\u2022" * 12,
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
        pwd_display.value = entry["password"] if revealed["value"] else "\u2022" * 12
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
        entry_form_dialog(page, api, theme, on_changed, existing=entry,
                          pet=pet, cat_widget=cat_widget, refresh_pet=refresh_pet)

    def do_delete(_):
        close_dialog(page, dlg)
        _confirm_delete(page, api, theme, entry, on_changed)

    def do_toggle_fav(_):
        result = api.toggle_favorite(entry["id"])
        if result["ok"]:
            entry["is_favorite"] = result["is_favorite"]
            fav_btn.icon = ft.Icons.STAR if entry["is_favorite"] else ft.Icons.STAR_BORDER
            fav_btn.icon_color = "#e5c14a" if entry["is_favorite"] else theme.c["text_muted"]
            page.update()

    def field_row(label, value):
        return ft.Row(
            [
                ft.Text(label, width=80, size=13, color=theme.c["text_muted"]),
                ft.Text(value, size=14, color=theme.c["text"], selectable=True,
                        expand=True),
            ],
        )

    # Favorite button
    fav_btn = ft.IconButton(
        icon=ft.Icons.STAR if entry.get("is_favorite") else ft.Icons.STAR_BORDER,
        icon_color="#e5c14a" if entry.get("is_favorite") else theme.c["text_muted"],
        icon_size=22,
        tooltip="Toggle favorite",
        on_click=do_toggle_fav,
    )

    # Build content
    content_controls = [
        field_row("Username", entry["username"] or "\u2014"),
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
        ft.Row([
            strength_badge(entry["strength"], theme),
            ft.Text(
                f"+{entry.get('points', 0)}\u2605",
                size=12, color="#e5c14a",
                weight=ft.FontWeight.W_600,
            ),
        ], spacing=8),
    ]

    # Stale warning
    if entry.get("is_stale"):
        content_controls.insert(0, ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.WARNING_AMBER, color="#FFA726", size=16),
                    ft.Text("This password is over 30 days old! Consider updating.",
                            size=12, color="#FFA726"),
                ],
                spacing=6,
            ),
            bgcolor=theme.c["surface_2"],
            border=ft.border.all(1, "#FFA726"),
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=10, vertical=6),
        ))

    dlg = ft.AlertDialog(
        modal=True,
        bgcolor=theme.c["surface"],
        title=ft.Row(
            [
                ft.Icon(ft.Icons.KEY_ROUNDED, color=theme.c["primary"]),
                ft.Text(entry["service"], expand=True),
                fav_btn,
            ],
            spacing=8,
        ),
        content=ft.Container(
            width=420,
            content=ft.Column(
                content_controls,
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
        label = api.check_strength(pwd)
        from backend.password_tools import strength_points
        pts = strength_points(label)
        strength_row.controls = [
            strength_badge(label, theme),
            ft.Text(
                f"+{pts}\u2605",
                size=12, color="#e5c14a",
                weight=ft.FontWeight.W_600,
            ),
        ]
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