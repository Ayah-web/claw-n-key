"""
status_bar.py
Bottom status bar for Claw'n Key.
Shows encryption status, session timer, stale password count, pet level, and coins.
"""

import flet as ft
import asyncio
from .theme import ThemeManager


def build_status_bar(page, api, pet, theme: ThemeManager, session_mgr=None):
    """
    Build the bottom status bar.
    Returns (container, refresh_fn).
    """

    encryption_text = ft.Text(
        "\U0001f512 AES-256",
        size=11,
        color="#66BB6A",
        weight=ft.FontWeight.W_600,
    )

    session_text = ft.Text(
        "",
        size=11,
        color=theme.c["text_muted"],
    )

    stale_text = ft.Text(
        "",
        size=11,
        color=theme.c["text_muted"],
    )

    pet_level_text = ft.Text(
        "",
        size=11,
        color=theme.c["primary"],
        weight=ft.FontWeight.W_600,
    )

    coins_text = ft.Text(
        "",
        size=11,
        color="#e5c14a",
        weight=ft.FontWeight.W_600,
    )

    points_text = ft.Text(
        "",
        size=11,
        color=theme.c["text_muted"],
    )

    bar = ft.Container(
        content=ft.Row(
            [
                encryption_text,
                ft.VerticalDivider(width=1, color=theme.c["border"]),
                stale_text,
                ft.Container(expand=True),
                pet_level_text,
                ft.VerticalDivider(width=1, color=theme.c["border"]),
                coins_text,
                ft.VerticalDivider(width=1, color=theme.c["border"]),
                points_text,
                ft.VerticalDivider(width=1, color=theme.c["border"]),
                session_text,
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
        ),
        height=32,
        bgcolor=theme.c["surface"],
        border=ft.border.only(top=ft.BorderSide(1, theme.c["border"])),
        padding=ft.padding.symmetric(horizontal=16, vertical=0),
    )

    def refresh():
        """Update all status bar values."""
        # Stale password count
        stale_count = api.get_stale_count()
        if stale_count > 0:
            stale_text.value = f"\u23f0 {stale_count} stale"
            stale_text.color = "#FFA726"
        else:
            stale_text.value = "\u2705 All fresh"
            stale_text.color = "#66BB6A"

        # Pet info
        if pet:
            pet_level_text.value = f"\U0001f43e Lv.{pet.level}"
            coins_text.value = f"\U0001fa99 {pet.coins}"
            points_text.value = f"\u2b50 {pet.points} pts"
        else:
            pet_level_text.value = ""
            coins_text.value = ""
            points_text.value = ""

        # Session timer
        if session_mgr and session_mgr.is_active:
            remaining = int(session_mgr.remaining_seconds)
            if remaining > 0:
                mins = remaining // 60
                secs = remaining % 60
                session_text.value = f"\U0001f552 {mins}:{secs:02d}"
                # Color warning when < 60 seconds
                if remaining < 60:
                    session_text.color = "#FF4444"
                elif remaining < 120:
                    session_text.color = "#FFA726"
                else:
                    session_text.color = theme.c["text_muted"]
            else:
                session_text.value = "\U0001f552 Locking..."
                session_text.color = "#FF4444"
        elif session_mgr and not session_mgr.is_active:
            session_text.value = "\U0001f513 No auto-lock"
            session_text.color = theme.c["text_muted"]
        else:
            session_text.value = ""

    # --- Auto-refresh timer using async ---
    _running = {"value": False}

    async def _tick_loop():
        """Update session timer every 5 seconds."""
        while _running["value"]:
            try:
                refresh()
                page.update()
            except Exception:
                pass
            await asyncio.sleep(5)

    def start():
        """Start the status bar auto-refresh."""
        if _running["value"]:
            return
        _running["value"] = True
        if hasattr(page, "run_task"):
            page.run_task(_tick_loop)

    def stop():
        """Stop the auto-refresh."""
        _running["value"] = False

    # Initial refresh
    refresh()

    return bar, refresh, start, stop