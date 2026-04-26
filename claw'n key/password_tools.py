"""
password_tools.py
Secure password generation and a 4-tier strength checker.
"""

import secrets
import string
import re

SYMBOLS = "!@#$%^&*()-_=+[]{};:,.<>?"

STRENGTH_TIERS = ["Bad", "Not Good", "Good", "Great"]


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
    """Raw numeric score 0-7. Kept separate so gamification can use it later."""
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


def strength_points(label: str) -> int:
    """Points awarded per strength tier. Hook for future pet/reward system."""
    return {"Bad": 0, "Not Good": 1, "Good": 3, "Great": 5}.get(label, 0)
