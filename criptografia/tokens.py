"""JWT token management for admin and service authentication."""

from __future__ import annotations

import hashlib
import os
import threading
import time
import uuid
from typing import Any

import jwt

JWT_ALGORITHM = "HS256"
_DEFAULT_EXPIRATION = 86400

_revoked_tokens: set[str] = set()
_revoked_lock = threading.Lock()


def _get_secret() -> str:
    """Read JWT secret from environment and enforce minimum strength."""
    secret = os.getenv("CRIPTO_JWT_SECRET", "")
    if len(secret) < 32:
        raise RuntimeError("CRIPTO_JWT_SECRET must be set with at least 32 characters")
    return secret


def _token_fingerprint(token: str) -> str:
    """Generate stable token fingerprint for revocation list storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generar_jwt(user_id: str, expires_in: int = _DEFAULT_EXPIRATION) -> str:
    """Generate a signed JWT token for a user."""
    if not isinstance(user_id, str) or not user_id.strip():
        raise ValueError("user_id must be a non-empty string")
    if not isinstance(expires_in, int) or expires_in <= 0:
        raise ValueError("expires_in must be a positive integer")

    now = int(time.time())
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + expires_in,
        "jti": str(uuid.uuid4()),
        "type": "access",
    }

    try:
        return jwt.encode(payload, _get_secret(), algorithm=JWT_ALGORITHM)
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("JWT generation failed") from exc


def verificar_jwt(token: str) -> dict[str, Any]:
    """Verify JWT signature, expiration and revocation state."""
    if not isinstance(token, str) or not token.strip():
        return {"valido": False, "error": "Token invalido"}

    fingerprint = _token_fingerprint(token)
    with _revoked_lock:
        if fingerprint in _revoked_tokens:
            return {"valido": False, "error": "Token revocado"}

    try:
        payload = jwt.decode(token, _get_secret(), algorithms=[JWT_ALGORITHM])
        payload["valido"] = True
        return payload
    except jwt.ExpiredSignatureError:
        return {"valido": False, "error": "Token expirado"}
    except jwt.InvalidTokenError:
        return {"valido": False, "error": "Token invalido"}
    except Exception as exc:  # pragma: no cover
        return {"valido": False, "error": f"Error interno: {exc}"}


def renovar_jwt(old_token: str) -> str:
    """Renew a valid JWT and revoke the previous token for session hardening."""
    verified = verificar_jwt(old_token)
    if not verified.get("valido"):
        raise ValueError(verified.get("error", "Token no valido"))

    user_id = str(verified.get("sub", "")).strip()
    if not user_id:
        raise ValueError("Token sin sujeto valido")

    revocar_jwt(old_token)
    return generar_jwt(user_id=user_id)


def revocar_jwt(token: str) -> bool:
    """Revoke a token by fingerprint so future validations fail."""
    if not isinstance(token, str) or not token.strip():
        return False

    with _revoked_lock:
        _revoked_tokens.add(_token_fingerprint(token))
    return True
