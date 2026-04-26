"""
api.py
High-level API used by the UI layer. Wraps database + crypto so the UI
doesn't need to know about either.
"""

from .database import PasswordDB, CATEGORIES, DEFAULT_CATEGORY
from .crypto import CryptoManager
from .password_tools import generate_password, check_strength, strength_points


class Api:
    def __init__(self):
        self.db = PasswordDB()
        self.crypto = None

    # ---------- Master password ----------

    def master_exists(self):
        return self.db.master_exists()

    def setup_master(self, password):
        if self.db.master_exists():
            return {"ok": False, "error": "Master password already set."}
        if not password or len(password) < 8:
            return {"ok": False, "error": "Master password must be at least 8 characters."}
        salt = self.db.set_master(password)
        self.crypto = CryptoManager(password, salt)
        return {"ok": True}

    def login(self, password):
        if not self.db.verify_master(password):
            return {"ok": False, "error": "Incorrect master password."}
        salt = self.db.get_salt()
        self.crypto = CryptoManager(password, salt)
        return {"ok": True}

    def logout(self):
        self.crypto = None
        return {"ok": True}

    def is_logged_in(self):
        return self.crypto is not None

    # ---------- Entries ----------

    def add_entry(self, service, username, password, category=DEFAULT_CATEGORY):
        if not self.crypto:
            return {"ok": False, "error": "Not logged in."}
        if not service or not password:
            return {"ok": False, "error": "Service and password are required."}
        encrypted = self.crypto.encrypt(password)
        self.db.add_entry(service, username, encrypted, category)
        strength = check_strength(password)
        return {"ok": True, "strength": strength, "points": strength_points(strength)}

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
                    "created_at": r[4],
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
        return {
            "ok": True,
            "entry": {
                "id": row[0],
                "service": row[1],
                "username": row[2],
                "password": password,
                "category": row[4] or DEFAULT_CATEGORY,
                "created_at": row[5],
                "strength": check_strength(password),
            },
        }

    def update_entry(self, entry_id, service, username, password, category):
        if not self.crypto:
            return {"ok": False, "error": "Not logged in."}
        if not service or not password:
            return {"ok": False, "error": "Service and password are required."}
        encrypted = self.crypto.encrypt(password)
        self.db.update_entry(entry_id, service, username, encrypted, category)
        return {"ok": True}

    def delete_entry(self, entry_id):
        if not self.crypto:
            return {"ok": False, "error": "Not logged in."}
        self.db.delete_entry(entry_id)
        return {"ok": True}

    # ---------- Utilities ----------

    def generate_password(self, length=16, use_symbols=True):
        return generate_password(int(length), bool(use_symbols))

    def check_strength(self, password):
        return check_strength(password)

    def categories(self):
        return list(CATEGORIES)
