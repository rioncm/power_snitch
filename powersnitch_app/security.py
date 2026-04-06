from __future__ import annotations

import hashlib
import hmac
import secrets
from typing import Any


PBKDF2_ROUNDS = 480_000


def hash_password(password: str, salt: str | None = None) -> str:
    actual_salt = salt or secrets.token_hex(16)
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        actual_salt.encode("utf-8"),
        PBKDF2_ROUNDS,
    )
    return f"pbkdf2_sha256${PBKDF2_ROUNDS}${actual_salt}${derived.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, rounds, salt, digest = encoded.split("$", 3)
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    candidate = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        int(rounds),
    )
    return hmac.compare_digest(candidate.hex(), digest)


def require_admin(session: dict[str, Any]) -> bool:
    return bool(session.get("is_admin"))

