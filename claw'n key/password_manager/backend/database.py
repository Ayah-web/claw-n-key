"""
backend/database.py
SQLite storage for encrypted entries, feedback, settings
and stale password tracking.

Thread-safe: uses check_same_thread=False + a lock because Flet's
event handlers can fire on any thread.
"""

import sqlite3
import os
import time
import threading

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "vault.db")
DB_FILE = os.path.normpath(DB_FILE)

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

STALE_THRESHOLD = 30 * 24 * 3600  # seconds


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
                id             INTEGER PRIMARY KEY CHECK (id = 1),
                pw_salt        BLOB    NOT NULL,
                password_blob  BLOB    NOT NULL,
                recovery_salt  BLOB    NOT NULL,
                recovery_blob  BLOB    NOT NULL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                service     TEXT    NOT NULL,
                username    TEXT,
                password    BLOB    NOT NULL,
                category    TEXT    DEFAULT 'Personal',
                is_favorite INTEGER NOT NULL DEFAULT 0,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                type       TEXT NOT NULL DEFAULT 'note',
                title      TEXT NOT NULL DEFAULT '',
                content    TEXT NOT NULL,
                created_at REAL NOT NULL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def _migrate(self):
        """Handle schema upgrades for pre-existing vaults."""
        c = self.conn.cursor()

        # entries table — add missing columns
        c.execute("PRAGMA table_info(entries)")
        cols = {row[1] for row in c.fetchall()}
        if "category" not in cols:
            c.execute("ALTER TABLE entries ADD COLUMN category TEXT DEFAULT 'Personal'")
        if "updated_at" not in cols:
            c.execute(
                "ALTER TABLE entries ADD COLUMN updated_at TIMESTAMP "
                "DEFAULT CURRENT_TIMESTAMP"
            )
        if "is_favorite" not in cols:
            c.execute(
                "ALTER TABLE entries ADD COLUMN is_favorite INTEGER NOT NULL DEFAULT 0"
            )

        # master table — migrate old hash/salt schema to new blob schema
        c.execute("PRAGMA table_info(master)")
        master_cols = {row[1] for row in c.fetchall()}
        if "hash" in master_cols and "password_blob" not in master_cols:
            c.execute("DROP TABLE master")
            c.execute("""
                CREATE TABLE master (
                    id             INTEGER PRIMARY KEY CHECK (id = 1),
                    pw_salt        BLOB    NOT NULL,
                    password_blob  BLOB    NOT NULL,
                    recovery_salt  BLOB    NOT NULL,
                    recovery_blob  BLOB    NOT NULL
                )
            """)

        self.conn.commit()

    # ---------- Master ----------

    def master_exists(self):
        with self._lock:
            c = self.conn.cursor()
            c.execute("SELECT COUNT(*) FROM master")
            return c.fetchone()[0] > 0

    def set_master(self, pw_salt: bytes, password_blob: bytes,
                   recovery_salt: bytes, recovery_blob: bytes):
        with self._lock:
            c = self.conn.cursor()
            c.execute(
                "INSERT INTO master "
                "(id, pw_salt, password_blob, recovery_salt, recovery_blob) "
                "VALUES (1, ?, ?, ?, ?)",
                (pw_salt, password_blob, recovery_salt, recovery_blob)
            )
            self.conn.commit()

    def get_pw_meta(self):
        with self._lock:
            c = self.conn.cursor()
            c.execute("SELECT pw_salt, password_blob FROM master WHERE id = 1")
            return c.fetchone()

    def get_recovery_meta(self):
        with self._lock:
            c = self.conn.cursor()
            c.execute("SELECT recovery_salt, recovery_blob FROM master WHERE id = 1")
            return c.fetchone()

    def update_master(self, pw_salt: bytes, password_blob: bytes,
                      recovery_salt: bytes, recovery_blob: bytes):
        with self._lock:
            c = self.conn.cursor()
            c.execute(
                "UPDATE master SET pw_salt = ?, password_blob = ?, "
                "recovery_salt = ?, recovery_blob = ? WHERE id = 1",
                (pw_salt, password_blob, recovery_salt, recovery_blob)
            )
            self.conn.commit()

    # ---------- Entries ----------

    def add_entry(self, service, username, encrypted_password,
                  category=DEFAULT_CATEGORY, is_favorite=0):
        with self._lock:
            c = self.conn.cursor()
            c.execute(
                "INSERT INTO entries "
                "(service, username, password, category, is_favorite) "
                "VALUES (?, ?, ?, ?, ?)",
                (service, username, encrypted_password, category, is_favorite)
            )
            self.conn.commit()

    def list_entries(self):
        with self._lock:
            c = self.conn.cursor()
            c.execute(
                "SELECT id, service, username, category, is_favorite, "
                "created_at, updated_at "
                "FROM entries ORDER BY is_favorite DESC, service COLLATE NOCASE"
            )
            return c.fetchall()

    def get_entry(self, entry_id):
        with self._lock:
            c = self.conn.cursor()
            c.execute(
                "SELECT id, service, username, password, category, "
                "created_at, updated_at, is_favorite "
                "FROM entries WHERE id = ?",
                (entry_id,)
            )
            return c.fetchone()

    def update_entry(self, entry_id, service, username, encrypted_password,
                     category, is_favorite=None):
        with self._lock:
            c = self.conn.cursor()
            if is_favorite is not None:
                c.execute(
                    "UPDATE entries SET service=?, username=?, password=?, "
                    "category=?, is_favorite=?, updated_at=CURRENT_TIMESTAMP "
                    "WHERE id=?",
                    (service, username, encrypted_password, category,
                     is_favorite, entry_id)
                )
            else:
                c.execute(
                    "UPDATE entries SET service=?, username=?, password=?, "
                    "category=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                    (service, username, encrypted_password, category, entry_id)
                )
            self.conn.commit()

    def toggle_favorite(self, entry_id):
        with self._lock:
            c = self.conn.cursor()
            c.execute("SELECT is_favorite FROM entries WHERE id = ?", (entry_id,))
            row = c.fetchone()
            if not row:
                return 0
            new_val = 0 if row[0] else 1
            c.execute(
                "UPDATE entries SET is_favorite = ? WHERE id = ?",
                (new_val, entry_id)
            )
            self.conn.commit()
            return new_val

    def delete_entry(self, entry_id):
        with self._lock:
            c = self.conn.cursor()
            c.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
            self.conn.commit()

    def get_stale_count(self):
        with self._lock:
            c = self.conn.cursor()
            c.execute(
                "SELECT COUNT(*) FROM entries "
                "WHERE julianday('now') - julianday(updated_at) > ?",
                (STALE_THRESHOLD / 86400.0,)
            )
            return c.fetchone()[0]

    def is_entry_stale(self, entry_id):
        with self._lock:
            c = self.conn.cursor()
            c.execute(
                "SELECT julianday('now') - julianday(updated_at) "
                "FROM entries WHERE id = ?",
                (entry_id,)
            )
            row = c.fetchone()
            if not row:
                return False
            return row[0] > (STALE_THRESHOLD / 86400.0)

    # ---------- Feedback ----------

    def add_feedback(self, content, title="", fb_type="note"):
        with self._lock:
            c = self.conn.cursor()
            c.execute(
                "INSERT INTO feedback (type, title, content, created_at) "
                "VALUES (?, ?, ?, ?)",
                (fb_type, title, content, time.time())
            )
            self.conn.commit()
            return c.lastrowid

    def get_feedback(self, fb_type=""):
        with self._lock:
            c = self.conn.cursor()
            if fb_type:
                c.execute(
                    "SELECT id, type, title, content, created_at "
                    "FROM feedback WHERE type = ? ORDER BY created_at DESC",
                    (fb_type,)
                )
            else:
                c.execute(
                    "SELECT id, type, title, content, created_at "
                    "FROM feedback ORDER BY created_at DESC"
                )
            return [
                {"id": r[0], "type": r[1], "title": r[2],
                 "content": r[3], "created_at": r[4]}
                for r in c.fetchall()
            ]

    def delete_feedback(self, fb_id):
        with self._lock:
            c = self.conn.cursor()
            c.execute("DELETE FROM feedback WHERE id = ?", (fb_id,))
            self.conn.commit()

    # ---------- Settings ----------

    def get_setting(self, key, default=""):
        with self._lock:
            c = self.conn.cursor()
            c.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = c.fetchone()
            return row[0] if row else default

    def set_setting(self, key, value):
        with self._lock:
            c = self.conn.cursor()
            c.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, value)
            )
            self.conn.commit()