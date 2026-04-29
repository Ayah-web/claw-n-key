"""
main.py
Password Manager entry point.

Run from this folder:
    pip install -r requirements.txt
    python main.py
"""

import os
import threading
import flet as ft

from backend import Api
from backend.pet import PetState
from backend.session import SessionManager
from backend.database import DB_FILE
from ui.theme import ThemeManager
from ui.auth import build_auth_view
from ui.vault import build_vault_view
from ui.intro import build_intro_view
from ui.splash import build_splash_view


def main(page: ft.Page):
    page.title = "Claw'n Key"

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

    # --- Session manager (auto-lock) ---
    session_mgr = SessionManager(timeout_seconds=300)
    saved_timeout = api.get_setting("auto_lock_timeout", "300")
    try:
        timeout_val = int(saved_timeout)
        session_mgr.set_timeout(timeout_val)
    except ValueError:
        pass

    state = {"view": "init"}

    # --- Global hotkey: Ctrl+Shift+K brings app to front ---
    def _bring_to_front():
        """Bring the app window to front. Called from hotkey thread."""
        try:
            if hasattr(page, "window") and page.window is not None:
                page.window.minimized = False
                page.window.focused = True
            else:
                try:
                    page.window_minimized = False
                except Exception:
                    pass
            page.update()
        except Exception as e:
            print(f"[Hotkey] Could not bring to front: {e}")

    def _register_hotkey():
        """Register the global hotkey in a background thread."""
        try:
            import keyboard
            keyboard.add_hotkey("ctrl+shift+k", _bring_to_front)
            keyboard.wait()  # Blocks this thread, keeping hotkey alive
        except ImportError:
            print("[Hotkey] 'keyboard' library not installed — hotkey disabled.")
        except Exception as e:
            print(f"[Hotkey] Registration failed: {e}")

    # Start hotkey listener in a daemon thread so it dies with the app
    hotkey_thread = threading.Thread(target=_register_hotkey, daemon=True)
    hotkey_thread.start()

    def on_reset_account():
        """
        Wipe everything — vault.db + pet_save.json — and restart from splash.
        Used by the 'Delete Account' option in settings.
        """
        nonlocal api, pet

        session_mgr.stop()
        api.logout()

        # Close the database connection BEFORE deleting!
        try:
            api.db.conn.close()
        except Exception as e:
            print(f"[Reset] Could not close DB connection: {e}")

        # Delete vault database
        try:
            if os.path.exists(DB_FILE):
                os.remove(DB_FILE)
                print(f"[Reset] Deleted {DB_FILE}")
            else:
                print(f"[Reset] vault.db not found at {DB_FILE}")
        except Exception as e:
            print(f"[Reset] Could not delete vault.db: {e}")

        # Delete pet save file
        from backend.pet import _PET_FILE
        try:
            if os.path.exists(_PET_FILE):
                os.remove(_PET_FILE)
                print(f"[Reset] Deleted {_PET_FILE}")
            else:
                print(f"[Reset] pet_save.json not found at {_PET_FILE}")
        except Exception as e:
            print(f"[Reset] Could not delete pet_save.json: {e}")

        # Re-initialize everything fresh
        api = Api()
        pet = PetState()

        state["view"] = "splash"
        render()

    def render():
        page.controls.clear()
        theme.apply(page)

        if state["view"] == "splash":
            view = build_splash_view(
                page, theme,
                on_complete=on_splash_complete,
                on_theme_toggle=on_theme_toggle,
            )
        elif state["view"] == "intro":
            view = build_intro_view(page, pet, theme, on_intro_complete)
        elif state["view"] == "auth":
            mode = "login" if api.master_exists() else "setup"
            view = build_auth_view(page, api, theme, mode, on_auth_success)
        else:
            view = build_vault_view(
                page, api, theme,
                on_logout=on_logout,
                on_theme_toggle=on_theme_toggle,
                on_reset_account=on_reset_account,
                pet=pet,
                session_mgr=session_mgr,
            )

        page.add(view)
        page.update()

    def on_splash_complete():
        """Splash → Intro."""
        state["view"] = "intro"
        render()

    def on_intro_complete():
        """Intro → Auth (master password setup)."""
        state["view"] = "auth"
        render()

    def on_auth_success():
        pet.apply_decay()
        if session_mgr.timeout > 0:
            session_mgr.start(on_lock=on_logout)
        state["view"] = "vault"
        render()

    def on_logout():
        pet.save()
        session_mgr.stop()
        api.logout()
        state["view"] = "auth"
        render()

    def on_theme_toggle():
        theme.toggle()
        render()

    # Decide starting view
    if pet.is_first_launch:
        state["view"] = "splash"
    else:
        state["view"] = "auth"

    render()

if __name__ == "__main__":
    runner = getattr(ft, "run", None)
    if runner is not None:
        runner(main)