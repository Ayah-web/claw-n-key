"""
session.py
Session auto-lock for Claw'n Key.
Tracks idle time; locks vault after configurable timeout.
"""

import time
import threading


class SessionManager:
    """
    Monitors user activity and triggers a lock callback
    when the idle timeout is reached.

    Usage:
        session = SessionManager(timeout_seconds=300)
        session.start(on_lock=my_lock_callback)
        # call session.touch() on any user interaction
        # call session.stop() when locking or closing
    """

    def __init__(self, timeout_seconds: int = 300):
        self._timeout = timeout_seconds
        self._last_activity = time.time()
        self._on_lock = None
        self._timer = None
        self._active = False
        self._lock = threading.Lock()

    @property
    def timeout(self):
        return self._timeout

    @property
    def idle_seconds(self):
        return time.time() - self._last_activity

    @property
    def remaining_seconds(self):
        """Seconds until auto-lock. Returns 0 if already expired."""
        remaining = self._timeout - self.idle_seconds
        return max(0, remaining)

    @property
    def is_active(self):
        return self._active

    def set_timeout(self, seconds: int):
        """Update the timeout duration. Takes effect on next check cycle."""
        with self._lock:
            self._timeout = max(30, seconds)  # minimum 30 seconds

    def start(self, on_lock=None):
        """Start monitoring idle time."""
        with self._lock:
            if on_lock:
                self._on_lock = on_lock
            self._active = True
            self._last_activity = time.time()
            self._schedule_check()

    def stop(self):
        """Stop monitoring. Call when locking or closing the app."""
        with self._lock:
            self._active = False
            if self._timer:
                self._timer.cancel()
                self._timer = None

    def touch(self):
        """Reset the idle timer. Call on any user interaction."""
        self._last_activity = time.time()

    def _schedule_check(self):
        """Schedule the next idle check."""
        if not self._active:
            return
        # Check every 10 seconds
        self._timer = threading.Timer(10.0, self._check)
        self._timer.daemon = True
        self._timer.start()

    def _check(self):
        """Check if idle timeout has been reached."""
        if not self._active:
            return
        if self.idle_seconds >= self._timeout:
            self._active = False
            if self._on_lock:
                try:
                    self._on_lock()
                except Exception as e:
                    print(f"[Session] Lock callback error: {e}")
        else:
            self._schedule_check()