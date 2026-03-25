"""
Password hashing / verification helpers.

Uses PBKDF2-HMAC-SHA256 from the Python stdlib (no extra dependencies).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from dataclasses import dataclass


DEFAULT_ITERATIONS = 200_000
DKLEN = 32


@dataclass(frozen=True)
class PasswordHash:
    salt_b64: str
    hash_b64: str
    iterations: int = DEFAULT_ITERATIONS


def hash_password(password: str, *, iterations: int = DEFAULT_ITERATIONS) -> PasswordHash:
    if not isinstance(password, str) or not password:
        raise ValueError("Password must be a non-empty string")

    salt = secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations, dklen=DKLEN)
    return PasswordHash(
        salt_b64=base64.b64encode(salt).decode("ascii"),
        hash_b64=base64.b64encode(derived).decode("ascii"),
        iterations=int(iterations),
    )


def verify_password(password: str, stored: PasswordHash) -> bool:
    if not isinstance(password, str):
        return False
    try:
        salt = base64.b64decode(stored.salt_b64.encode("ascii"))
        expected = base64.b64decode(stored.hash_b64.encode("ascii"))
    except Exception:
        return False

    derived = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, int(stored.iterations), dklen=len(expected)
    )
    return hmac.compare_digest(derived, expected)

