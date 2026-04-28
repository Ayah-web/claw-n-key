"""
vault.py
Main view shown after unlock: toolbar with search + category filter +
theme toggle + lock button, and a scrollable list of entries.
Now includes: pet panel, favorites, stale badges, status bar,
feedback button, settings button.
"""

import flet as ft
from .theme import ThemeManager, CATEGORY_COLORS
from .widgets import category_chip, show_snack, open_dialog, close_dialog
from .dialogs import entry_form_dialog, view_entry_dialog, generator_dialog
from .cat_widget import CatWidget
from .pet_panel import build_pet_panel
from .feedback_dialog import feedback_dialog
from .settings_dialog import settings_dialog
from .status_bar import build_status_bar


def build_vault_view(page: ft.Page, api, theme: ThemeManager,
                     on_logout, on_theme_toggle, on_reset_account=None,
                     pet=None, session_mgr=None):
    """
    on_logout: callback fired when user clicks Lock
    on_theme_toggle: callback to switch theme
    on_reset_account: callback to wipe everything and restart from splash
    pet: PetState instance (optional)
    session_mgr: SessionManager instance (optional)
    """
    filter_state = {"query": "", "category": "All", "favorites_only": False}

    # ---------- Pet setup ----------

    cat_widget = None
    pet_panel = None
    refresh_pet = None

    if pet:
        cat_widget = CatWidget(
            theme_mode=theme.mode,
            display_width=200,
            display_height=140,
            scale=2,
        )
        pet_panel, refresh_pet = build_pet_panel(page, pet, cat_widget, theme)

    # ---------- Status bar ----------

    status_bar, refresh_status, start_status, stop_status = build_status_bar(
        page, api, pet, theme, session_mgr
    )

    # ---------- Stale password effect on pet ----------

    def _apply_stale_effect():
        if pet:
            stale_count = api.get_stale_count()
            if stale_count > 0:
                pet.apply_stale_penalty(stale_count)
                if cat_widget:
                    if stale_count >= 3:
                        cat_widget.say(f"{stale_count} stale passwords! 😿", 4.0)
                    elif stale_count >= 1:
                        cat_widget.say("Some passwords are getting old...", 3.0)

    # ---------- Toolbar controls ----------

    search_field = ft.TextField(
        hint_text="Search services or usernames…",
        prefix_icon=ft.Icons.SEARCH,
        border_radius=10,
        filled=True,
        bgcolor=theme.c["surface_2"],
        border_color=theme.c["border"],
        focused_border_color=theme.c["primary"],
        content_padding=ft.padding.symmetric(horizontal=12, vertical=10),
        expand=True,
    )

    category_filter = ft.Dropdown(
        value="All",
        options=[ft.dropdown.Option("All")] +
                [ft.dropdown.Option(c) for c in api.categories()],
        border_radius=10,
        filled=True,
        bgcolor=theme.c["surface_2"],
        border_color=theme.c["border"],
        focused_border_color=theme.c["primary"],
        content_padding=ft.padding.symmetric(horizontal=12, vertical=10),
        width=140,
    )

    fav_button = ft.IconButton(
        icon=ft.Icons.STAR_BORDER,
        tooltip="Show favorites only",
        icon_color=theme.c["text_muted"],
    )

    def toggle_favorites(_):
        filter_state["favorites_only"] = not filter_state["favorites_only"]
        if filter_state["favorites_only"]:
            fav_button.icon = ft.Icons.STAR
            fav_button.icon_color = "#e5c14a"
            fav_button.tooltip = "Show all entries"
        else:
            fav_button.icon = ft.Icons.STAR_BORDER
            fav_button.icon_color = theme.c["text_muted"]
            fav_button.tooltip = "Show favorites only"
        refresh()

    fav_button.on_click = toggle_favorites

    theme_icon = (
        ft.Icons.LIGHT_MODE_OUTLINED if theme.mode == "dark"
        else ft.Icons.DARK_MODE_OUTLINED
    )

    # ---------- Entry list ----------

    entries_column = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
    empty_state = ft.Container(
        content=ft.Column(
            [
                ft.Icon(ft.Icons.INBOX_OUTLINED, size=48,
                        color=theme.c["text_muted"]),
                ft.Text("No entries yet", size=16, color=theme.c["text_muted"]),
                ft.Text("Click + Add to save your first password.",
                        size=12, color=theme.c["text_muted"]),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        ),
        alignment=ft.Alignment(0, 0),
        padding=60,
    )

    def entry_card(e):
        cat_color = CATEGORY_COLORS.get(e["category"], theme.c["text_muted"])
        is_fav = e.get("is_favorite", 0)
        is_stale = e.get("is_stale", False)

        def on_click(_):
            view_entry_dialog(page, api, theme, e["id"], refresh,
                              pet=pet, cat_widget=cat_widget,
                              refresh_pet=refresh_pet)

        def on_fav_click(_):
            result = api.toggle_favorite(e["id"])
            if result["ok"]:
                refresh()

        badges = []
        if is_fav:
            badges.append(
                ft.Icon(ft.Icons.STAR, color="#e5c14a", size=16)
            )
        if is_stale:
            badges.append(
                ft.Container(
                    content=ft.Text("⏰ Stale", size=10, color="#ffffff",
                                    weight=ft.FontWeight.BOLD),
                    bgcolor="#FFA726",
                    border_radius=6,
                    padding=ft.padding.symmetric(horizontal=6, vertical=2),
                )
            )

        return ft.Container(
            content=ft.Row(
                [
                    ft.Container(width=4, bgcolor=cat_color, border_radius=2),
                    ft.Container(width=8),
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(
                                        e["service"],
                                        weight=ft.FontWeight.W_600,
                                        size=15,
                                        color=theme.c["text"],
                                    ),
                                ] + badges,
                                spacing=6,
                            ),
                            ft.Row(
                                [
                                    ft.Text(
                                        e["username"] or "—",
                                        size=12,
                                        color=theme.c["text_muted"],
                                    ),
                                    ft.Container(
                                        width=3, height=3,
                                        bgcolor=theme.c["text_muted"],
                                        border_radius=2,
                                    ),
                                    ft.Text(
                                        e["category"],
                                        size=12,
                                        color=theme.c["text_muted"],
                                    ),
                                ],
                                spacing=8,
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.STAR if is_fav else ft.Icons.STAR_BORDER,
                        icon_color="#e5c14a" if is_fav else theme.c["text_muted"],
                        icon_size=18,
                        tooltip="Toggle favorite",
                        on_click=on_fav_click,
                    ),
                    ft.Icon(ft.Icons.CHEVRON_RIGHT,
                            color=theme.c["text_muted"]),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=theme.c["surface"],
            padding=ft.padding.symmetric(horizontal=14, vertical=12),
            border_radius=10,
            border=ft.border.all(
                1,
                "#FFA726" if is_stale else theme.c["border"],
            ),
            on_click=on_click,
            ink=True,
        )

    def apply_filters(entries):
        q = filter_state["query"].lower().strip()
        cat = filter_state["category"]
        fav_only = filter_state["favorites_only"]
        out = []
        for e in entries:
            if cat != "All" and e["category"] != cat:
                continue
            if fav_only and not e.get("is_favorite", 0):
                continue
            if q:
                haystack = (e["service"] + " " + (e["username"] or "")).lower()
                if q not in haystack:
                    continue
            out.append(e)
        return out

    def refresh():
        res = api.list_entries()
        if not res["ok"]:
            show_snack(page, res.get("error", "Failed to load entries."),
                       error=True)
            return
        entries_column.controls.clear()
        filtered = apply_filters(res["entries"])
        if not filtered:
            entries_column.controls.append(empty_state)
        else:
            entries_column.controls.extend(entry_card(e) for e in filtered)
        if refresh_pet:
            refresh_pet()
        refresh_status()
        page.update()

    def on_search(e):
        filter_state["query"] = e.control.value
        refresh()

    def on_category(e):
        filter_state["category"] = e.control.value
        refresh()

    search_field.on_change = on_search
    category_filter.on_change = on_category

    # ---------- Button handlers ----------

    def open_add(_):
        entry_form_dialog(page, api, theme, refresh, existing=None, pet=pet,
                          cat_widget=cat_widget, refresh_pet=refresh_pet)

    def open_generator(_):
        generator_dialog(page, api, theme)

    def open_feedback(_):
        feedback_dialog(page, api, theme)

    def open_settings(_):
        settings_dialog(
            page, api, pet, theme, session_mgr,
            on_theme_toggle, cat_widget, refresh_pet,
            on_reset_account=on_reset_account,
        )

    def toggle_theme(_):
        if cat_widget:
            cat_widget.set_theme("light" if theme.mode == "dark" else "dark")
        on_theme_toggle()

    def lock(_):
        stop_status()
        if cat_widget:
            cat_widget.stop()
            cat_widget.say("Bye bye! Stay safe!", 2.0)
        if pet:
            pet.save()
        on_logout()

    def on_keyboard(e):
        if session_mgr:
            session_mgr.touch()

    page.on_keyboard_event = on_keyboard

    # ---------- Assemble ----------

    header = ft.Row(
        [
            ft.Row(
                [
                    ft.Icon(ft.Icons.LOCK_ROUNDED, color=theme.c["primary"]),
                    ft.Text("Vault", size=20, weight=ft.FontWeight.BOLD,
                            color=theme.c["text"]),
                ],
                spacing=8,
            ),
            ft.Container(expand=True),
            ft.IconButton(
                icon=ft.Icons.FEEDBACK_OUTLINED,
                tooltip="Feedback & Notes",
                icon_color=theme.c["text_muted"],
                on_click=open_feedback,
            ),
            ft.IconButton(
                icon=ft.Icons.SETTINGS_OUTLINED,
                tooltip="Settings",
                icon_color=theme.c["text_muted"],
                on_click=open_settings,
            ),
            ft.IconButton(
                icon=theme_icon,
                tooltip="Toggle theme",
                icon_color=theme.c["text_muted"],
                on_click=toggle_theme,
            ),
            ft.IconButton(
                icon=ft.Icons.LOCK_OUTLINE,
                tooltip="Lock vault",
                icon_color=theme.c["text_muted"],
                on_click=lock,
            ),
        ],
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    toolbar = ft.Row(
        [search_field, category_filter, fav_button],
        spacing=10,
    )

    actions = ft.Row(
        [
            ft.FilledButton(
                "Add Entry",
                icon=ft.Icons.ADD,
                on_click=open_add,
                style=ft.ButtonStyle(
                    bgcolor=theme.c["primary"], color="#ffffff",
                    shape=ft.RoundedRectangleBorder(radius=10),
                ),
            ),
            ft.OutlinedButton(
                "Generate",
                icon=ft.Icons.AUTO_AWESOME,
                on_click=open_generator,
                style=ft.ButtonStyle(
                    color=theme.c["primary"],
                    side=ft.BorderSide(1, theme.c["border"]),
                    shape=ft.RoundedRectangleBorder(radius=10),
                ),
            ),
        ],
        spacing=10,
    )

    vault_content = ft.Column(
        [
            header,
            ft.Container(height=8),
            toolbar,
            ft.Container(height=4),
            actions,
            ft.Container(height=8),
            ft.Divider(color=theme.c["border"], height=1),
            ft.Container(height=8),
            entries_column,
        ],
        expand=True,
    )

    if pet_panel:
        main_row = ft.Row(
            [
                ft.Container(content=vault_content, expand=True),
                ft.Container(width=16),
                ft.Container(
                    content=ft.Column(
                        [pet_panel],
                        scroll=ft.ScrollMode.AUTO,
                        expand=True,
                    ),
                    width=290,
                ),
            ],
            expand=True,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
    else:
        main_row = vault_content

    view = ft.Column(
        [
            ft.Container(
                content=main_row,
                padding=24,
                bgcolor=theme.c["bg"],
                expand=True,
            ),
            status_bar,
        ],
        spacing=0,
        expand=True,
    )

    refresh()
    _apply_stale_effect()

    if cat_widget:
        cat_widget.start(page)
        cat_widget.say("Welcome back! Meow~", 3.0)

    start_status()

    return view