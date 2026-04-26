# Password Manager (Flet)

Desktop password manager. Python-only, runs as a package with `python main.py`, opens in a native window — not a browser, not an `.exe`.

## What's included

**Mandatory features (from the brief)**
- Master password (PBKDF2-SHA256, 200k iterations, per-install salt)
- Password storage (Fernet / AES-128 + HMAC, key derived from master password)
- Password generation (cryptographically secure via `secrets` module)
- Password strength checking — 4 tiers: Bad / Not Good / Good / Great
- User-entered passwords with live strength feedback
- Desktop app, runs as a Python package

**Foundation features for the extras list**
- Categories (Personal / Work / Finance / Social / Streaming / Shopping / Other) with colored stripes on each card
- Search across service name and username
- Category filter
- Dark galaxy theme + light pastel theme, toggle in toolbar
- Edit entries (not just add/delete)
- Strength-based points hook (`strength_points()` in `backend/password_tools.py`) ready for the future pet/reward system
- `created_at` / `updated_at` timestamps on entries, ready for the "time to change password" reminder feature

## File layout

```
password_manager/
├── main.py                  # Entry point + auth/vault state machine
├── requirements.txt
├── .gitignore
├── backend/
│   ├── __init__.py
│   ├── api.py               # High-level API, called by UI
│   ├── database.py          # SQLite + thread-safe lock, auto-migrates
│   ├── crypto.py            # Fernet encryption, PBKDF2 key derivation
│   └── password_tools.py    # Generator + strength + points
└── ui/
    ├── __init__.py
    ├── theme.py             # Color tokens: dark galaxy, light pastel
    ├── widgets.py           # Strength badge, category chip, Flet compat shims
    ├── auth.py              # Login/setup screen
    ├── vault.py             # Main view: toolbar, search, filter, list
    └── dialogs.py           # Add/edit, view, generator dialogs
```

## Running

```bash
pip install -r requirements.txt
python main.py
```

First launch asks you to create a master password. Subsequent launches ask you to unlock.

## Team workflow (useful for the project management report)

The module split gives you clean ownership lines for parallel work:

- **Backend team** owns `backend/`. Can write unit tests against `PasswordDB`, `CryptoManager`, and the password tools without touching any UI code.
- **Frontend team** owns `ui/`. Each view/dialog lives in its own file, so two people can work on Vault and Dialogs simultaneously without merge conflicts.
- **Integration point** is `backend/api.py` — adding any new feature usually means one new method here plus its caller in the UI. Good formal interface to document in your design specification.
- **Theme changes** are centralized in `ui/theme.py`. Future styling work edits one file.

## Security notes (for the report)

- The master password is **never** stored. Only a PBKDF2-SHA256 hash with a random 16-byte salt and 200,000 iterations.
- Stored passwords are encrypted with Fernet (AES-128-CBC + HMAC-SHA256). The encryption key is derived from `master_password + salt` via PBKDF2-SHA256 (200k iterations, 32-byte output).
- Salt is stored in the local SQLite database; the master password lives in memory only while the vault is unlocked and is cleared on lock/logout.
- SQLite file `vault.db` is created next to `main.py` on first run. Back it up, it's your actual password store.

## Next-up features (backlog for later sprints)

Rough priority order from your extras list:

1. **Password-change reminders** — the `updated_at` column is already there; just needs a UI flag on stale entries.
2. **Session auto-lock** after N minutes idle — requires re-entering master password to resume.
3. **Pet / gamification** — `strength_points()` already returns the numeric score per entry; a separate `pet.db` table plus a small Flet view can read from it.
4. **Import / export** — CSV from Bitwarden, 1Password, LastPass.
5. **Cloud backup** — the DB is already encrypted at rest, so syncing `vault.db` to a cloud folder is safe.
6. **Global hotkey** to open/focus the app — `keyboard` or `pynput`.
7. **Biometric login** — Windows Hello (`pywin32`) or macOS Touch ID (Keychain).
8. **Memorization helper** — mnemonic generator from a passphrase.

## Why Flet (vs the PyWebView + React alternative)

We evaluated both. Short version: Flet wins on team velocity because nobody needs to context-switch between Python and JavaScript, the Material component library gives us polished visuals without writing CSS, and there's one stack to debug instead of two. PyWebView + React would have given higher aesthetic ceiling but at the cost of a second toolchain (npm, Vite, build step) and a known class of threading bugs at the Python/JS bridge.

(This paragraph is worth expanding into a "Tools Evaluation" section of the project report. The fact that you considered both and made a deliberate choice based on team capability, schedule, and risk is exactly the kind of reasoning the brief's evaluation criteria are looking for.)

## Known Flet version compatibility

Flet's API has churned between versions — dialog open/close and clipboard methods have been renamed multiple times. `ui/widgets.py` contains compatibility shims (`open_dialog`, `close_dialog`, `set_clipboard`, `show_snack`) that try the newest API first and fall back to older ones, so the app runs on Flet 0.21 through 0.84+. If you hit an issue, first try `pip install --upgrade flet`.
