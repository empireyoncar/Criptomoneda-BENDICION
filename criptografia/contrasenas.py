"""Password hashing and strength validation helpers."""

from __future__ import annotations

import re
import secrets
import string
from typing import Any

import bcrypt


def hashear_bcrypt(password: str, rounds: int = 12) -> str:
    """Hash a password using bcrypt with configurable cost factor."""
    if not isinstance(password, str) or not password:
        raise ValueError("password must be a non-empty string")
    if not isinstance(rounds, int) or rounds < 4 or rounds > 16:
        raise ValueError("rounds must be an integer between 4 and 16")

    try:
        salt = bcrypt.gensalt(rounds=rounds)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("bcrypt hashing failed") from exc


def verificar_bcrypt(password: str, hash_value: str) -> bool:
    """Verify a password against a bcrypt hash."""
    if not isinstance(password, str) or not isinstance(hash_value, str):
        return False

    try:
        return bcrypt.checkpw(password.encode("utf-8"), hash_value.encode("utf-8"))
    except Exception:
        return False


def validar_fortaleza(password: str) -> dict[str, Any]:
    """Evaluate password strength using basic production-ready controls."""
    if not isinstance(password, str):
        raise ValueError("password must be a string")

    errors: list[str] = []
    score = 0

    if len(password) < 12:
        errors.append("Debe tener al menos 12 caracteres")
    else:
        score += 1

    if re.search(r"[a-z]", password):
        score += 1
    else:
        errors.append("Debe incluir minusculas")

    if re.search(r"[A-Z]", password):
        score += 1
    else:
        errors.append("Debe incluir mayusculas")

    if re.search(r"\d", password):
        score += 1
    else:
        errors.append("Debe incluir numeros")

    if re.search(r"[^\w\s]", password):
        score += 1
    else:
        errors.append("Debe incluir simbolos")

    common = {"password", "123456", "qwerty", "admin", "bendicion"}
    if password.lower() in common:
        errors.append("Password demasiado comun")
        score = max(score - 2, 0)

    return {
        "valida": len(errors) == 0,
        "puntuacion": min(score, 5),
        "nivel": "alta" if score >= 5 else "media" if score >= 3 else "baja",
        "errores": errors,
    }


def generar_password_temporal() -> str:
    """Generate a temporary password with strong entropy and mixed character sets."""
    alphabet_lower = string.ascii_lowercase
    alphabet_upper = string.ascii_uppercase
    alphabet_digits = string.digits
    alphabet_symbols = "!@#$%^&*()-_=+"

    # Force at least one character from each class, then shuffle securely.
    raw = [
        secrets.choice(alphabet_lower),
        secrets.choice(alphabet_upper),
        secrets.choice(alphabet_digits),
        secrets.choice(alphabet_symbols),
    ]

    full_alphabet = alphabet_lower + alphabet_upper + alphabet_digits + alphabet_symbols
    raw.extend(secrets.choice(full_alphabet) for _ in range(12))
    secrets.SystemRandom().shuffle(raw)

    return "".join(raw)
