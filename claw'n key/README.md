# Claw'n Key 🐾🔑

Desktop password manager with a virtual cat companion. Python-only, runs with `python main.py`, opens in a native window — not a browser, not an `.exe`.

## What's included

**Core security features**
- Master password (PBKDF2-SHA256, 200k iterations, per-install salt)
- Recovery key system — a one-time `RKEY-XXXX-XXXX-XXXX-XXXX-XXXX` key generated at vault creation; lets you reset your master password without losing your data
- Password storage (Fernet / AES-128-CBC + HMAC-SHA256, key derived from master password)
- Password generation (cryptographically secure via `secrets` module)
- Password strength checking — 4 tiers: Bad / Not Good / Good / Great
- Live strength feedback with improvement tips while typing
- Session auto-lock — configurable idle timeout (1 min → 30 min → Never), resets on any keyboard activity
- Global hotkey `Ctrl+Shift+K` brings the app to front from anywhere

**Vault features**
- Add, edit, delete, view password entries
- Categories: Personal / Work / Finance / Social / Streaming / Shopping / Other — colored stripes per card
- Favorites — star any entry, filter to favorites only
- Stale password detection — entries not updated in 30+ days get an ⏰ badge and a warning on open
- Search across service name and username
- Category filter dropdown
- Copy password to clipboard with one click
- Dark galaxy theme + light pastel theme, toggle in toolbar

**Pet / gamification system**
- Virtual cat companion (Whiskers by default, renameable) rendered with a pixel-art sprite engine (`backend/catode/`)
- Cat animates in real time at 12 fps using `flet.canvas` — no PNG encoding
- Mood system: Happy / Neutral / Sad / Miserable based on average of Hunger, Happiness, Energy stats
- Time-based stat decay — pet gets sadder the longer you ignore it
- Stale passwords apply a happiness penalty to the pet
- Points earned per password added/updated (stronger = more points)
- Points spent on Feed (Kibble / Treat / Fancy Feast) and Play (Yarn Ball / Laser Pointer / Catnip Mouse) actions
- XP + level system — levels up automatically, with happiness bonus on level-up
- Item drop system — every 5 "Great" passwords or on updating a stale password, rolls for a Common / Rare / Legendary item drop (outfits, toys, food)
- Inventory dialog shows all collected items grouped by rarity
- Pet panel in the vault sidebar: stat bars, XP bar, points display, mood, feed/play/pet buttons, inventory
- Speech bubble above cat reacts to actions and idles with random chatter
- Cat widget also appears on the splash screen (sleeping) and intro screen

**First-run onboarding**
- Splash screen with sleeping cat
- Animated intro sequence with typewriter dialogue — cat introduces itself and asks to be named
- Setup flow for master password + recovery key display

**Feedback & Notes**
- In-app notes system — log bug reports, feedback, or personal notes
- Filter by type (Note / Feedback / Bug Report)
- Stored locally in `vault.db`

**Status bar**
- Always-visible bottom bar: AES-256 indicator, stale password count, pet level, points, session timer
- Session timer colour-codes to orange (<2 min) and red (<1 min) before auto-lock

