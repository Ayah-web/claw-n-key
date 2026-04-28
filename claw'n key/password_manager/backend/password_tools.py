"""
password_tools.py
Secure password generation and a 4-tier strength checker.
Now includes numeric tier for gamification integration.
"""

import secrets
import string
import re

SYMBOLS = "!@#$%^&*()-_=+[]{};:,.<>?"

STRENGTH_TIERS = ["Bad", "Not Good", "Good", "Great"]

# Tier colors for UI badges
TIER_COLORS = {
    0: "#c44054",   # Bad - red
    1: "#b87518",   # Not Good - orange
    2: "#2e8050",   # Good - green
    3: "#6a3fb5",   # Great - purple
}

TIER_LABELS = {
    0: "Bad",
    1: "Not Good",
    2: "Good",
    3: "Great",
}


def generate_password(length: int = 16, use_symbols: bool = True) -> str:
    if length < 4:
        raise ValueError("Password length must be at least 4.")

    pool = string.ascii_letters + string.digits
    if use_symbols:
        pool += SYMBOLS

    required = [
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.digits),
    ]
    if use_symbols:
        required.append(secrets.choice(SYMBOLS))

    remaining = [secrets.choice(pool) for _ in range(length - len(required))]
    pwd_chars = required + remaining
    secrets.SystemRandom().shuffle(pwd_chars)
    return "".join(pwd_chars)


def _score(password: str) -> int:
    """Raw numeric score 0-7."""
    if not password:
        return 0
    s = 0
    if len(password) >= 8:  s += 1
    if len(password) >= 12: s += 1
    if len(password) >= 16: s += 1
    if re.search(r"[a-z]", password):        s += 1
    if re.search(r"[A-Z]", password):        s += 1
    if re.search(r"\d",    password):        s += 1
    if re.search(r"[^a-zA-Z0-9]", password): s += 1
    return s


def check_strength(password: str) -> str:
    """Return one of: Bad / Not Good / Good / Great."""
    s = _score(password)
    if s <= 2: return "Bad"
    if s <= 4: return "Not Good"
    if s <= 5: return "Good"
    return "Great"


def strength_tier(password: str) -> int:
    """
    Return numeric tier: 0=Bad, 1=Not Good, 2=Good, 3=Great.
    Used by the pet/reward system.
    """
    label = check_strength(password)
    return {"Bad": 0, "Not Good": 1, "Good": 2, "Great": 3}.get(label, 0)


def strength_points(label: str) -> int:
    """Points awarded per strength tier."""
    return {"Bad": 0, "Not Good": 1, "Good": 3, "Great": 5}.get(label, 0)


def strength_tips(password: str) -> list:
    """Return list of tips to improve password strength."""
    tips = []
    if not password:
        return ["Enter a password"]
    if len(password) < 8:
        tips.append("Use at least 8 characters")
    if len(password) < 12:
        tips.append("Try 12+ characters for better security")
    if len(password) < 16:
        tips.append("16+ characters is ideal")
    if not re.search(r"[a-z]", password):
        tips.append("Add lowercase letters")
    if not re.search(r"[A-Z]", password):
        tips.append("Add uppercase letters")
    if not re.search(r"\d", password):
        tips.append("Add numbers")
    if not re.search(r"[^a-zA-Z0-9]", password):
        tips.append("Add special characters (!@#$...)")
    if len(password) >= 16 and not tips:
        tips.append("Excellent password!")
    return tips