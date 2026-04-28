"""
feedback_dialog.py
Feedback & Notes dialog for Claw'n Key.
Users can submit bug reports, feature requests, or personal notes.
"""

import flet as ft
from datetime import datetime
from .theme import ThemeManager
from .widgets import show_snack, open_dialog, close_dialog


def feedback_dialog(page, api, theme: ThemeManager):
    """Open the feedback/notes dialog."""

    # --- Type selector ---
    type_dropdown = ft.Dropdown(
        value="note",
        options=[
            ft.dropdown.Option("note", "📝 Note"),
            ft.dropdown.Option("feedback", "💬 Feedback"),
            ft.dropdown.Option("bug", "🐛 Bug Report"),
        ],
        border_radius=8,
        filled=True,
        bgcolor=theme.c["surface_2"],
        border_color=theme.c["border"],
        focused_border_color=theme.c["primary"],
        width=200,
    )

    # --- Input fields ---
    title_field = ft.TextField(
        label="Title (optional)",
        hint_text="Brief title…",
        border_radius=10,
        filled=True,
        bgcolor=theme.c["surface_2"],
        border_color=theme.c["border"],
        focused_border_color=theme.c["primary"],
    )

    content_field = ft.TextField(
        label="Content",
        hint_text="Write your note or feedback…",
        multiline=True,
        min_lines=3,
        max_lines=6,
        border_radius=10,
        filled=True,
        bgcolor=theme.c["surface_2"],
        border_color=theme.c["border"],
        focused_border_color=theme.c["primary"],
    )

    # --- List of existing feedback ---
    list_column = ft.Column(
        spacing=6,
        scroll=ft.ScrollMode.AUTO,
        height=200,
    )

    type_icons = {
        "note": "📝",
        "feedback": "💬",
        "bug": "🐛",
    }

    def _build_feedback_card(fb):
        """Build a single feedback card."""
        created = datetime.fromtimestamp(fb["created_at"]).strftime("%b %d, %Y %H:%M")
        icon = type_icons.get(fb["type"], "📝")
        title_str = fb["title"] if fb["title"] else fb["type"].capitalize()

        def on_delete(_, fid=fb["id"]):
            api.delete_feedback(fid)
            _refresh_list()
            page.update()
            show_snack(page, "🗑 Deleted")

        return ft.Container(
            content=ft.Row(
                [
                    ft.Text(icon, size=16),
                    ft.Column(
                        [
                            ft.Text(
                                title_str,
                                size=13,
                                weight=ft.FontWeight.W_600,
                                color=theme.c["text"],
                            ),
                            ft.Text(
                                fb["content"][:80] + ("…" if len(fb["content"]) > 80 else ""),
                                size=11,
                                color=theme.c["text_muted"],
                            ),
                            ft.Text(
                                created,
                                size=9,
                                color=theme.c["text_muted"],
                            ),
                        ],
                        spacing=1,
                        expand=True,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        icon_color=theme.c["danger"],
                        icon_size=16,
                        on_click=on_delete,
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=theme.c["surface_2"],
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=10, vertical=6),
        )

    def _refresh_list():
        """Reload and display feedback entries."""
        entries = api.get_feedback()
        list_column.controls.clear()
        if not entries:
            list_column.controls.append(
                ft.Text(
                    "No entries yet.",
                    size=12,
                    color=theme.c["text_muted"],
                    italic=True,
                )
            )
        else:
            for fb in entries[:20]:
                list_column.controls.append(_build_feedback_card(fb))

    # --- Submit handler ---
    def on_submit(_):
        content = (content_field.value or "").strip()
        if not content:
            show_snack(page, "Content cannot be empty.", error=True)
            return
        title = (title_field.value or "").strip()
        fb_type = type_dropdown.value or "note"

        api.add_feedback(content, title, fb_type)
        content_field.value = ""
        title_field.value = ""
        show_snack(page, "✅ Saved!")
        _refresh_list()
        page.update()

    # --- Filter dropdown ---
    filter_dropdown = ft.Dropdown(
        value="all",
        options=[
            ft.dropdown.Option("all", "All"),
            ft.dropdown.Option("note", "📝 Notes"),
            ft.dropdown.Option("feedback", "💬 Feedback"),
            ft.dropdown.Option("bug", "🐛 Bugs"),
        ],
        border_radius=8,
        filled=True,
        bgcolor=theme.c["surface_2"],
        border_color=theme.c["border"],
        focused_border_color=theme.c["primary"],
        width=150,
    )

    def on_filter_change(_):
        val = filter_dropdown.value
        if val == "all":
            entries = api.get_feedback()
        else:
            entries = api.get_feedback(fb_type=val)
        list_column.controls.clear()
        if not entries:
            list_column.controls.append(
                ft.Container(
                    content=ft.Text(
                        "Nothing here.",
                        size=12,
                        color=theme.c["text_muted"],
                        text_align=ft.TextAlign.CENTER,
                    ),
                    padding=20,
                )
            )
        else:
            for fb in entries[:30]:
                list_column.controls.append(_build_feedback_card(fb))
        page.update()

    filter_dropdown.on_change = on_filter_change

    # --- Layout ---
    dlg = ft.AlertDialog(
        modal=True,
        bgcolor=theme.c["surface"],
        title=ft.Row(
            [
                ft.Icon(ft.Icons.FEEDBACK_OUTLINED, color=theme.c["primary"]),
                ft.Text("Feedback & Notes", color=theme.c["text"]),
            ],
            spacing=8,
        ),
        content=ft.Container(
            width=480,
            content=ft.Column(
                [
                    # --- Submit section ---
                    ft.Text("New Entry", size=14,
                            weight=ft.FontWeight.W_600,
                            color=theme.c["text"]),
                    ft.Row(
                        [type_dropdown],
                        spacing=8,
                    ),
                    title_field,
                    content_field,
                    ft.Row(
                        [
                            ft.Container(expand=True),
                            ft.FilledButton(
                                "Submit",
                                icon=ft.Icons.SEND,
                                on_click=on_submit,
                                style=ft.ButtonStyle(
                                    bgcolor=theme.c["primary"],
                                    color="#ffffff",
                                    shape=ft.RoundedRectangleBorder(radius=8),
                                ),
                            ),
                        ],
                    ),
                    ft.Divider(color=theme.c["border"], height=1),
                    # --- Existing entries ---
                    ft.Row(
                        [
                            ft.Text("History", size=14,
                                    weight=ft.FontWeight.W_600,
                                    color=theme.c["text"]),
                            ft.Container(expand=True),
                            filter_dropdown,
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    list_column,
                ],
                spacing=10,
                tight=True,
            ),
        ),
        actions=[
            ft.TextButton(
                "Close",
                on_click=lambda _: close_dialog(page, dlg),
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    # Load existing entries
    _refresh_list()

    open_dialog(page, dlg)