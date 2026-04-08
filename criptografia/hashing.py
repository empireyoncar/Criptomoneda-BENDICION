"""Hashing utilities for token integrity and audit pipelines."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets


def _to_bytes(data: str) -> bytes:
    """Encode text input to UTF-8 bytes with strict validation."""
    if not isinstance(data, str) or not data:
        raise ValueError("data must be a non-empty string")
    return data.encode("utf-8")


def hash_sha256(data: str) -> str:
    """Return the SHA-256 hex digest for a string."""
    return hashlib.sha256(_to_bytes(data)).hexdigest()


def hash_sha512(data: str) -> str:
    """Return the SHA-512 hex digest for a string."""
    return hashlib.sha512(_to_bytes(data)).hexdigest()


def verify_hash(data: str, hash_value: str) -> bool:
    """Verify a digest against SHA-256 or SHA-512 in constant time."""
    if not isinstance(hash_value, str) or not hash_value:
        return False

    try:
        candidate_256 = hash_sha256(data)
        candidate_512 = hash_sha512(data)
    except (TypeError, ValueError):
        return False

    return hmac.compare_digest(candidate_256, hash_value) or hmac.compare_digest(
        candidate_512, hash_value
    )


def generate_salt() -> str:
    """Generate a cryptographically secure random salt as URL-safe base64."""
    return base64.urlsafe_b64encode(secrets.token_bytes(16)).decode("ascii")
