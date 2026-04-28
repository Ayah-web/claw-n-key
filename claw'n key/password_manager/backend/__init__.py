"""
backend/__init__.py
High-level API used by the UI layer. Wraps database + crypto so the UI
doesn't need to know about either.
"""

import os
from .database import PasswordDB, CATEGORIES, DEFAULT_CATEGORY
from .crypto import (
    CryptoManager,
    generate_fernet_key,
    generate_recovery_key,
    wrap_key,
    unwrap_key,
)
from .password_tools import (
    generate_password,
    check_strength,
    strength_points,
    strength_tier,
)


class Api:
    def __init__(self):
        self.db = PasswordDB()
        self.crypto = None

    # ---------- Master password ----------

    def master_exists(self):
        return self.db.master_exists()

    def setup_master(self, password):
        """First-time vault creation. Returns recovery key on success."""
        if self.db.master_exists():
            return {"ok": False, "error": "Master password already set."}
        if not password or len(password) < 8:
            return {"ok": False, "error": "Master password must be at least 8 characters."}

        fernet_key = generate_fernet_key()

        pw_salt = os.urandom(16)
        password_blob = wrap_key(fernet_key, password, pw_salt)

        recovery_key = generate_recovery_key()
        recovery_salt = os.urandom(16)
        recovery_blob = wrap_key(fernet_key, recovery_key, recovery_salt)

        self.db.set_master(pw_salt, password_blob, recovery_salt, recovery_blob)
        self.crypto = CryptoManager(fernet_key)

        return {"ok": True, "recovery_key": recovery_key}

    def login(self, password):
        """Normal login with master password."""
        meta = self.db.get_pw_meta()
        if not meta:
            return {"ok": False, "error": "No vault found."}

        pw_salt, password_blob = meta
        fernet_key = unwrap_key(password_blob, password, pw_salt)

        if fernet_key is None:
            return {"ok": False, "error": "Incorrect master password."}

        self.crypto = CryptoManager(fernet_key)
        return {"ok": True}

    def recover_with_key(self, recovery_key, new_password):
        """Forgot-password flow: use recovery key to set a new master password."""
        if not new_password or len(new_password) < 8:
            return {"ok": False, "error": "New password must be at least 8 characters."}

        meta = self.db.get_recovery_meta()
        if not meta:
            return {"ok": False, "error": "No recovery data found."}

        recovery_salt, recovery_blob = meta
        fernet_key = unwrap_key(recovery_blob, recovery_key, recovery_salt)
        if fernet_key is None:
            return {"ok": False, "error": "Invalid recovery key."}

        new_pw_salt = os.urandom(16)
        new_password_blob = wrap_key(fernet_key, new_password, new_pw_salt)

        new_recovery_key = generate_recovery_key()
        new_recovery_salt = os.urandom(16)
        new_recovery_blob = wrap_key(fernet_key, new_recovery_key, new_recovery_salt)

        self.db.update_master(
            new_pw_salt, new_password_blob,
            new_recovery_salt, new_recovery_blob,
        )
        self.crypto = CryptoManager(fernet_key)

        return {"ok": True, "new_recovery_key": new_recovery_key}

    def logout(self):
        self.crypto = None

    # ---------- Entries ----------

    def add_entry(self, service, username, password,
                  category=DEFAULT_CATEGORY, is_favorite=0):
        if not self.crypto:
            return {"ok": False, "error": "Not logged in."}
        if not service or not password:
            return {"ok": False, "error": "Service and password are required."}
        encrypted = self.crypto.encrypt(password)
        self.db.add_entry(service, username, encrypted, category, is_favorite)
        label = check_strength(password)
        return {
            "ok": True,
            "strength": label,
            "strength_tier": strength_tier(password),
            "points": strength_points(label),
        }

    def list_entries(self):
        if not self.crypto:
            return {"ok": False, "error": "Not logged in.", "entries": []}
        rows = self.db.list_entries()
        return {
            "ok": True,
            "entries": [
                {
                    "id": r[0],
                    "service": r[1],
                    "username": r[2],
                    "category": r[3] or DEFAULT_CATEGORY,
                    "is_favorite": r[4],
                    "created_at": r[5],
                    "updated_at": r[6],
                    "is_stale": self.db.is_entry_stale(r[0]),
                }
                for r in rows
            ],
        }

    def get_entry(self, entry_id):
        if not self.crypto:
            return {"ok": False, "error": "Not logged in."}
        row = self.db.get_entry(entry_id)
        if not row:
            return {"ok": False, "error": "Entry not found."}
        try:
            password = self.crypto.decrypt(row[3])
        except Exception:
            return {"ok": False, "error": "Could not decrypt entry."}
        label = check_strength(password)
        return {
            "ok": True,
            "entry": {
                "id": row[0],
                "service": row[1],
                "username": row[2],
                "password": password,
                "category": row[4] or DEFAULT_CATEGORY,
                "created_at": row[5],
                "updated_at": row[6],
                "is_favorite": row[7],
                "is_stale": self.db.is_entry_stale(row[0]),
                "strength": label,
                "strength_tier": strength_tier(password),
                "points": strength_points(label),
            },
        }

    def update_entry(self, entry_id, service, username, password,
                     category, is_favorite=None):
        if not self.crypto:
            return {"ok": False, "error": "Not logged in."}
        if not service or not password:
            return {"ok": False, "error": "Service and password are required."}
        was_stale = self.db.is_entry_stale(entry_id)
        encrypted = self.crypto.encrypt(password)
        self.db.update_entry(entry_id, service, username, encrypted,
                             category, is_favorite)
        label = check_strength(password)
        return {
            "ok": True,
            "was_stale": was_stale,
            "strength": label,
            "strength_tier": strength_tier(password),
            "points": strength_points(label),
        }

    def delete_entry(self, entry_id):
        if not self.crypto:
            return {"ok": False, "error": "Not logged in."}
        self.db.delete_entry(entry_id)
        return {"ok": True}

    def toggle_favorite(self, entry_id):
        if not self.crypto:
            return {"ok": False, "error": "Not logged in."}
        new_val = self.db.toggle_favorite(entry_id)
        return {"ok": True, "is_favorite": new_val}

    # ---------- Stale detection ----------

    def get_stale_count(self):
        return self.db.get_stale_count()

    # ---------- Feedback ----------

    def add_feedback(self, content, title="", fb_type="note"):
        return self.db.add_feedback(content, title, fb_type)

    def get_feedback(self, fb_type=""):
        return self.db.get_feedback(fb_type)

    def delete_feedback(self, fb_id):
        self.db.delete_feedback(fb_id)

    # ---------- Settings ----------

    def get_setting(self, key, default=""):
        return self.db.get_setting(key, default)

    def set_setting(self, key, value):
        self.db.set_setting(key, value)

    # ---------- Utilities ----------

    def generate_password(self, length=16, use_symbols=True):
        return generate_password(int(length), bool(use_symbols))

    def check_strength(self, password):
        return check_strength(password)

    def strength_tier(self, password):
        return strength_tier(password)

    def categories(self):
        return list(CATEGORIES)