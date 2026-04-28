"""
crypto.py
Symmetric encryption for stored passwords.

Architecture:
  - A random Fernet key is generated once at vault creation.
  - That key is "wrapped" (encrypted) by the master password via PBKDF2.
  - The same key is also wrapped by a one-time recovery key.
  - Either path can unwrap the Fernet key for vault operations.
"""

import base64
import secrets
import string
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

PBKDF2_ITERATIONS = 200_000


def _derive_wrapping_key(passphrase: str, salt: bytes) -> bytes:
    """Derive a Fernet-compatible wrapping key from a passphrase + salt."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))


def generate_fernet_key() -> bytes:
    """Generate a random Fernet key. Called once at vault creation."""
    return Fernet.generate_key()


def wrap_key(fernet_key: bytes, passphrase: str, salt: bytes) -> bytes:
    """Encrypt (wrap) the Fernet key using a passphrase-derived wrapping key."""
    wrapping_key = _derive_wrapping_key(passphrase, salt)
    return Fernet(wrapping_key).encrypt(fernet_key)


def unwrap_key(blob: bytes, passphrase: str, salt: bytes) -> bytes | None:
    """
    Decrypt (unwrap) the Fernet key from a blob using a passphrase.
    Returns the Fernet key on success, None on failure.
    """
    wrapping_key = _derive_wrapping_key(passphrase, salt)
    try:
        return Fernet(wrapping_key).decrypt(blob)
    except Exception:
        return None


def generate_recovery_key() -> str:
    """Generate a human-readable recovery key like RKEY-XXXX-XXXX-XXXX-XXXX-XXXX."""
    chars = string.ascii_uppercase + string.digits
    segments = [
        "".join(secrets.choice(chars) for _ in range(4))
        for _ in range(5)
    ]
    return "RKEY-" + "-".join(segments)


class CryptoManager:
    """Holds the unwrapped Fernet key and provides encrypt/decrypt for vault entries."""

    def __init__(self, fernet_key: bytes):
        self.cipher = Fernet(fernet_key)

    def encrypt(self, plaintext: str) -> bytes:
        return self.cipher.encrypt(plaintext.encode())

    def decrypt(self, ciphertext: bytes) -> str:
        return self.cipher.decrypt(ciphertext).decode()