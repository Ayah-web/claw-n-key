"""
database.py
SQLite storage for master password hash and encrypted entries.

Thread-safe: uses check_same_thread=False + a lock because Flet's event
handlers can fire on any thread.
"""

import sqlite3
import hashlib
import os
import threading

DB_FILE = "vault.db"
PBKDF2_ITERATIONS = 200_000

DEFAULT_CATEGORY = "Personal"
CATEGORIES = [
    "Personal",
    "Work",
    "Finance",
    "Social",
    "Streaming",
    "Shopping",
    "Other",
]


class PasswordDB:
    def __init__(self, path=DB_FILE):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self._lock = threading.Lock()
        self._create_tables()
        self._migrate()

    def _create_tables(self):
        c = self.conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS master (
                id    INTEGER PRIMARY KEY CHECK (id = 1),
                hash  TEXT    NOT NULL,
                salt  TEXT    NOT NULL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                service    TEXT    NOT NULL,
                username   TEXT,
                password   BLOB    NOT NULL,
                category   TEXT    DEFAULT 'Personal',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def _migrate(self):
        """Add columns to pre-existing vaults (from the tkinter draft)."""
        c = self.conn.cursor()
        c.execute("PRAGMA table_info(entries)")
        cols = {row[1] for row in c.fetchall()}
        if "category" not in cols:
            c.execute(
                "ALTER TABLE entries ADD COLUMN category TEXT DEFAULT 'Personal'"
            )
        if "updated_at" not in cols:
            c.execute(
                "ALTER TABLE entries ADD COLUMN updated_at TIMESTAMP "
                "DEFAULT CURRENT_TIMESTAMP"
            )
        self.conn.commit()

    # ---------- Master password ----------

    def master_exists(self):
        with self._lock:
            c = self.conn.cursor()
            c.execute("SELECT COUNT(*) FROM master")
            return c.fetchone()[0] > 0

    def set_master(self, password: str) -> bytes:
        salt = os.urandom(16)
        h = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt, PBKDF2_ITERATIONS
        ).hex()
        with self._lock:
            c = self.conn.cursor()
            c.execute(
                "INSERT INTO master (id, hash, salt) VALUES (1, ?, ?)",
                (h, salt.hex())
            )
            self.conn.commit()
        return salt

    def verify_master(self, password: str) -> bool:
        with self._lock:
            c = self.conn.cursor()
            c.execute("SELECT hash, salt FROM master WHERE id = 1")
            row = c.fetchone()
        if not row:
            return False
        stored_hash, salt_hex = row
        computed = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex), PBKDF2_ITERATIONS
        ).hex()
        return computed == stored_hash

    def get_salt(self) -> bytes:
        with self._lock:
            c = self.conn.cursor()
            c.execute("SELECT salt FROM master WHERE id = 1")
            row = c.fetchone()
        return bytes.fromhex(row[0]) if row else None

    # ---------- Entries ----------

    def add_entry(self, service, username, encrypted_password, category=DEFAULT_CATEGORY):
        with self._lock:
            c = self.conn.cursor()
            c.execute(
                "INSERT INTO entries (service, username, password, category) "
                "VALUES (?, ?, ?, ?)",
                (service, username, encrypted_password, category)
            )
            self.conn.commit()

    def list_entries(self):
        with self._lock:
            c = self.conn.cursor()
            c.execute(
                "SELECT id, service, username, category, created_at "
                "FROM entries ORDER BY service COLLATE NOCASE"
            )
            return c.fetchall()

    def get_entry(self, entry_id):
        with self._lock:
            c = self.conn.cursor()
            c.execute(
                "SELECT id, service, username, password, category, created_at "
                "FROM entries WHERE id = ?",
                (entry_id,)
            )
            return c.fetchone()

    def update_entry(self, entry_id, service, username, encrypted_password, category):
        with self._lock:
            c = self.conn.cursor()
            c.execute(
                "UPDATE entries "
                "SET service = ?, username = ?, password = ?, category = ?, "
                "    updated_at = CURRENT_TIMESTAMP "
                "WHERE id = ?",
                (service, username, encrypted_password, category, entry_id)
            )
            self.conn.commit()

    def delete_entry(self, entry_id):
        with self._lock:
            c = self.conn.cursor()
            c.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
            self.conn.commit()
