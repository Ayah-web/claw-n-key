"""
widgets.py
Small reusable UI pieces so the main views stay readable.

Also contains compatibility shims for Flet's API churn: dialog
open/close and clipboard have all been renamed at least once. The
helpers here try the current name first and fall back to older ones
so the app works on Flet 0.21+ through 0.84+.
"""

import flet as ft
from .theme import ThemeManager, CATEGORY_COLORS


# ---------- Flet compat helpers ----------

def open_dialog(page: ft.Page, dialog):
    """Open a dialog across Flet versions."""
    # 0.84+: show_dialog / pop_dialog
    if hasattr(page, "show_dialog"):
        page.show_dialog(dialog)
        return
    # 0.21 - 0.83: page.open()
    if hasattr(page, "open"):
        page.open(dialog)
        return
    # pre-0.21: assign + set open flag
    page.dialog = dialog
    dialog.open = True
    page.update()


def close_dialog(page: ft.Page, dialog=None):
    """Close a dialog across Flet versions."""
    if hasattr(page, "pop_dialog"):
        page.pop_dialog()
        return
    if hasattr(page, "close") and dialog is not None:
        page.close(dialog)
        return
    if dialog is not None:
        dialog.open = False
        page.update()


def set_clipboard(page: ft.Page, text: str):
    """Copy text to the system clipboard across Flet versions."""
    if hasattr(page, "set_clipboard"):
        page.set_clipboard(text)
        return
    # Newer Flet: clipboard is a property
    try:
        page.clipboard = text
    except Exception:
        pass  # Best effort


# ---------- Visual widgets ----------


def strength_badge(label: str, theme: ThemeManager) -> ft.Container:
    """Pill-shaped strength indicator matching the current theme."""
    fg, bg = theme.strength(label)
    return ft.Container(
        content=ft.Text(label, size=12, weight=ft.FontWeight.W_600, color=fg),
        bgcolor=bg,
        padding=ft.padding.symmetric(horizontal=10, vertical=4),
        border_radius=12,
    )


def category_chip(name: str, theme: ThemeManager) -> ft.Container:
    """Small colored dot + category name."""
    color = CATEGORY_COLORS.get(name, theme.c["text_muted"])
    return ft.Row(
        [
            ft.Container(width=8, height=8, bgcolor=color, border_radius=4),
            ft.Text(name, size=12, color=theme.c["text_muted"]),
        ],
        spacing=6,
        tight=True,
    )


def show_snack(page: ft.Page, msg: str, error: bool = False):
    """Toast-style notification. Works across Flet versions."""
    snack = ft.SnackBar(
        ft.Text(msg, color="#ffffff"),
        bgcolor="#c44054" if error else "#2e8050",
        duration=2500,
    )
    # 0.84+: SnackBar is a DialogControl, shown via show_dialog / open
    # Older: page.snack_bar = snack; snack.open = True
    if hasattr(page, "show_dialog"):
        try:
            page.show_dialog(snack)
            return
        except Exception:
            pass
    if hasattr(page, "open"):
        try:
            page.open(snack)
            return
        except Exception:
            pass
    # Pre-0.21 fallback
    try:
        page.snack_bar = snack
        snack.open = True
        page.update()
    except Exception:
        pass  # Best effort - snackbar is non-critical
