# Claw'n Key 🐾🔑

A desktop password manager with a virtual cat that lives in your sidebar.

## Features

### Security
- Master password hashed with PBKDF2-SHA256 (200k iterations, unique salt per install)
- One-time recovery key (`RKEY-XXXX-XXXX-XXXX-XXXX-XXXX`) generated at setup so you can reset your master password without losing your vault
- Passwords encrypted with Fernet (AES-128-CBC + HMAC-SHA256)
- Password generator built on Python's `secrets` module
- 4-tier strength checker: Bad / Not Good / Good / Great with live tips as you type
- Auto-lock after configurable idle time (1 min up to 30 min or never)
- `Ctrl+Shift+K` brings the window to front from anywhere

### Vault
- Add / edit / delete / view entries
- 7 categories with colored card stripes
- Favorites with a filter toggle
- Entries not touched in 30+ days get an ⏰ badge and a warning when opened
- Search by service or username
- One-click copy to clipboard
- Dark and light themes with 3 light color variants: blue / pink / purple

### The cat
- Pixel-art sprite rendered at 12fps on a `flet.canvas` using a custom sprite engine called `catode` — no PNG encoding
- Mood (Happy / Neutral / Sad / Miserable) driven by Hunger / Happiness / Energy stats that decay over real time
- Stale passwords in your vault lower its happiness
- Earn points by saving passwords. Stronger passwords earn more
- Spend points to feed or play with it
- XP and level system with item drops every 5 "Great" passwords or when you fix a stale one
- Drops are Common / Rare / Legendary outfits, toys and food with a full inventory view
- Speech bubble reacts to what you do and idles with random lines when left alone
- Shows up sleeping on the splash screen and wakes up during the intro

### First launch
- Sleeping cat on the splash screen
- Typewriter intro where the cat wakes up and asks you to name it
- Master password setup with recovery key display

### Notes
- Simple in-app notes for logging bugs, ideas or anything else
- Filterable by type: Note / Feedback / Bug Report

### Status bar
- Always visible at the bottom: encryption status, stale count, pet level, points and session timer
- Timer goes orange under 2 minutes and red under 1 minute

---

## Setup

```bash
pip install -r requirements.txt
python main.py