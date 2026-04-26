"""
vault.py
Main view shown after unlock: toolbar with search + category filter +
theme toggle + lock button, and a scrollable list of entries.
"""

import flet as ft
from .theme import ThemeManager, CATEGORY_COLORS
from .widgets import category_chip, show_snack
from .dialogs import entry_form_dialog, view_entry_dialog, generator_dialog


def build_vault_view(page: ft.Page, api, theme: ThemeManager,
                     on_logout, on_theme_toggle):
    """
    on_logout: callback fired when user clicks Lock
    on_theme_toggle: callback to switch theme (handled at app level
                     because it needs to re-render everything)
    """
    filter_state = {"query": "", "category": "All"}

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
        alignment=ft.Alignment.CENTER,
        padding=60,
    )

    def entry_card(e):
        cat_color = CATEGORY_COLORS.get(e["category"], theme.c["text_muted"])

        def on_click(_):
            view_entry_dialog(page, api, theme, e["id"], refresh)

        # A colored left stripe by category + main content
        return ft.Container(
            content=ft.Row(
                [
                    # Category color stripe
                    ft.Container(width=4, bgcolor=cat_color, border_radius=2),
                    ft.Container(width=8),
                    ft.Column(
                        [
                            ft.Text(
                                e["service"],
                                weight=ft.FontWeight.W_600,
                                size=15,
                                color=theme.c["text"],
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
                    ft.Icon(ft.Icons.CHEVRON_RIGHT,
                            color=theme.c["text_muted"]),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=theme.c["surface"],
            padding=ft.padding.symmetric(horizontal=14, vertical=12),
            border_radius=10,
            border=ft.border.all(1, theme.c["border"]),
            on_click=on_click,
            ink=True,
        )

    def apply_filters(entries):
        q = filter_state["query"].lower().strip()
        cat = filter_state["category"]
        out = []
        for e in entries:
            if cat != "All" and e["category"] != cat:
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
        entry_form_dialog(page, api, theme, refresh, existing=None)

    def open_generator(_):
        generator_dialog(page, api, theme)

    def toggle_theme(_):
        on_theme_toggle()

    def lock(_):
        on_logout()

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
        [search_field, category_filter],
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

    view = ft.Container(
        content=ft.Column(
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
        ),
        padding=24,
        bgcolor=theme.c["bg"],
        expand=True,
    )

    # Populate on first render
    refresh()
    return view
