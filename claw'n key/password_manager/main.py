"""
main.py
Password Manager entry point.

Run from this folder:
    pip install -r requirements.txt
    python main.py
"""

import flet as ft

from backend import Api
from backend.pet import PetState
from ui.theme import ThemeManager
from ui.auth import build_auth_view
from ui.vault import build_vault_view
from ui.intro import build_intro_view


def main(page: ft.Page):
    page.title = "Claw & Key"

    if hasattr(page, "window") and page.window is not None:
        page.window.width = 1100
        page.window.height = 700
        page.window.min_width = 800
        page.window.min_height = 520
    else:
        try:
            page.window_width = 1100
            page.window_height = 700
            page.window_min_width = 800
            page.window_min_height = 520
        except Exception:
            pass

    page.padding = 0

    api = Api()
    pet = PetState()
    theme = ThemeManager(mode="dark")
    theme.apply(page)

    state = {"view": "init"}

    def render():
        page.controls.clear()
        theme.apply(page)

        if state["view"] == "intro":
            view = build_intro_view(page, pet, theme, on_intro_complete)
        elif state["view"] == "auth":
            mode = "login" if api.master_exists() else "setup"
            view = build_auth_view(page, api, theme, mode, on_auth_success)
        else:
            view = build_vault_view(
                page, api, theme,
                on_logout=on_logout,
                on_theme_toggle=on_theme_toggle,
                pet=pet,
            )

        page.add(view)
        page.update()

    def on_intro_complete():
        """Called after user names the cat - proceed to master password setup."""
        state["view"] = "auth"
        render()

    def on_auth_success():
        pet.apply_decay()
        state["view"] = "vault"
        render()

    def on_logout():
        pet.save()
        api.logout()
        state["view"] = "auth"
        render()

    def on_theme_toggle():
        theme.toggle()
        render()

    # Decide starting view - only check pet, not vault
    if pet.is_first_launch:
        state["view"] = "intro"
    else:
        state["view"] = "auth"

    render()


if __name__ == "__main__":
    runner = getattr(ft, "run", None)
    if runner is not None:
        runner(main)
    else:
        ft.app(target=main)