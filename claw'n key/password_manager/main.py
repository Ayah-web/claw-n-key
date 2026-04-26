"""
main.py
Password Manager — entry point.

Run from this folder:
    pip install -r requirements.txt
    python main.py
"""

import flet as ft

from backend import Api
from ui.theme import ThemeManager
from ui.auth import build_auth_view
from ui.vault import build_vault_view


def main(page: ft.Page):
    page.title = "Password Manager"

    # Window sizing: newer Flet (0.80+) uses page.window.width; older uses
    # page.window_width directly. Try new first, fall back to old.
    if hasattr(page, "window") and page.window is not None:
        page.window.width = 900
        page.window.height = 640
        page.window.min_width = 640
        page.window.min_height = 480
    else:
        try:
            page.window_width = 900
            page.window_height = 640
            page.window_min_width = 640
            page.window_min_height = 480
        except Exception:
            pass  # Pre-0.80 without the old attrs either — skip.

    page.padding = 0

    api = Api()
    theme = ThemeManager(mode="dark")
    theme.apply(page)

    state = {"view": "auth"}  # "auth" | "vault"

    def render():
        page.controls.clear()
        theme.apply(page)

        if state["view"] == "auth":
            mode = "login" if api.master_exists() else "setup"
            view = build_auth_view(page, api, theme, mode, on_auth_success)
        else:
            view = build_vault_view(
                page, api, theme,
                on_logout=on_logout,
                on_theme_toggle=on_theme_toggle,
            )

        page.add(view)
        page.update()

    def on_auth_success():
        state["view"] = "vault"
        render()

    def on_logout():
        api.logout()
        state["view"] = "auth"
        render()

    def on_theme_toggle():
        theme.toggle()
        render()

    render()


if __name__ == "__main__":
    # Flet 0.80+ prefers ft.run(); older uses ft.app(target=main).
    runner = getattr(ft, "run", None)
    if runner is not None:
        runner(main)
    else:
        ft.app(target=main)
