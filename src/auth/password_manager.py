"""Secure password hashing and verification using bcrypt."""

from __future__ import annotations

import re
import bcrypt
from typing import Tuple


class PasswordManager:
    """Enterprise password hashing, salt management, and strength validation."""

    BCRYPT_ROUNDS = 12

    @classmethod
    def hash_password(cls, plain_password: str) -> str:
        """Generate a secure salted bcrypt hash for the provided plaintext password."""
        if not plain_password:
            raise ValueError("Password cannot be empty.")
        salt = bcrypt.gensalt(rounds=cls.BCRYPT_ROUNDS)
        hashed_bytes = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
        return hashed_bytes.decode("utf-8")

    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        """Verify whether a plaintext password matches the stored bcrypt hash."""
        if not plain_password or not hashed_password:
            return False
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8"),
            )
        except Exception:
            return False

    @classmethod
    def validate_password_strength(cls, password: str) -> Tuple[bool, str]:
        """Validate corporate password complexity requirements."""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long."
        if not re.search(r"[A-Za-z]", password):
            return False, "Password must contain at least one letter."
        if not re.search(r"\d", password):
            return False, "Password must contain at least one digit."
        return True, "Password meets security requirements."

