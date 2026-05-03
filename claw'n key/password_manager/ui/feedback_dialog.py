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

    type_dropdown = ft.DropdownM2(
        value="note",
        options=[
            ft.dropdownm2.Option(key="note", text="📝 Note"),
            ft.dropdownm2.Option(key="feedback", text="💬 Feedback"),
            ft.dropdownm2.Option(key="bug", text="🐛 Bug Report"),
        ],
        border_radius=8,
        filled=True,
        bgcolor=theme.c["surface_2"],
        border_color=theme.c["border"],
        focused_border_color=theme.c["primary"],
        color=theme.c["text"],
        width=200,
    )

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

    list_column = ft.Column(
        spacing=6,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    type_icons = {
        "note": "📝",
        "feedback": "💬",
        "bug": "🐛",
    }

    def _build_feedback_card(fb):
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

    def _refresh_list(fb_type="all"):
        entries = api.get_feedback() if fb_type == "all" else api.get_feedback(fb_type=fb_type)
        list_column.controls.clear()
        if not entries:
            list_column.controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("📭", size=28, text_align=ft.TextAlign.CENTER),
                            ft.Text(
                                "No entries yet.",
                                size=12,
                                color=theme.c["text_muted"],
                                italic=True,
                                text_align=ft.TextAlign.CENTER,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=6,
                    ),
                    bgcolor=theme.c["surface_2"],
                    border_radius=8,
                    padding=ft.padding.symmetric(horizontal=10, vertical=6),
                    alignment=ft.Alignment(0, 0),
                    expand=True,
                    height=168,
                )
            )
        else:
            for i, fb in enumerate(entries[:20]):
                list_column.controls.append(_build_feedback_card(fb))
                if i < len(entries[:20]) - 1:
                    list_column.controls.append(
                        ft.Divider(color=theme.c["border"], height=1)
                    )

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

    filter_dropdown = ft.DropdownM2(
        value="all",
        options=[
            ft.dropdownm2.Option(key="all", text="All"),
            ft.dropdownm2.Option(key="note", text="📝 Notes"),
            ft.dropdownm2.Option(key="feedback", text="💬 Feedback"),
            ft.dropdownm2.Option(key="bug", text="🐛 Bugs"),
        ],
        border_radius=8,
        filled=True,
        bgcolor=theme.c["surface_2"],
        border_color=theme.c["border"],
        focused_border_color=theme.c["primary"],
        color=theme.c["text"],
        width=150,
    )

    def on_filter_change(e):
        _refresh_list(e.control.value or "all")
        page.update()

    filter_dropdown.on_change = on_filter_change

    history_section = ft.Container(
        content=list_column,
        height=180,
        bgcolor=theme.c["surface_2"],
        border_radius=8,
        padding=ft.padding.symmetric(horizontal=4, vertical=4),
    )

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
            height=500,
            content=ft.Column(
                [
                    ft.Text(
                        "New Entry",
                        size=14,
                        weight=ft.FontWeight.W_600,
                        color=theme.c["text"],
                    ),
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
                    ft.Row(
                        [
                            ft.Text(
                                "History",
                                size=14,
                                weight=ft.FontWeight.W_600,
                                color=theme.c["text"],
                            ),
                            ft.Container(expand=True),
                            filter_dropdown,
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    history_section,
                ],
                spacing=10,
                tight=True,
                scroll=ft.ScrollMode.AUTO,
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

    _refresh_list()
    open_dialog(page, dlg)