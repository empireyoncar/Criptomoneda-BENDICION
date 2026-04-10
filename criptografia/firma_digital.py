"""Digital signature utilities for transactions and blocks (ECDSA)."""

from __future__ import annotations

import json
import secrets
import threading
import time
from typing import Any

from ecdsa import BadSignatureError, SECP256k1, SigningKey, VerifyingKey

_NONCE_TTL_SECONDS = 600
_nonce_store: dict[str, float] = {}
_nonce_lock = threading.Lock()


def _canonical_json(data: dict[str, Any]) -> bytes:
    """Serialize dictionaries in stable canonical form for deterministic signing."""
    if not isinstance(data, dict):
        raise ValueError("data must be a dictionary")
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


def firmar_transaccion(tx_data: dict[str, Any], private_key: str) -> str:
    """Sign transaction payload with PEM private key using ECDSA."""
    if not isinstance(private_key, str) or not private_key.strip():
        raise ValueError("private_key must be a non-empty PEM string")

    try:
        try:
            sk = SigningKey.from_pem(private_key)
        except Exception:
            # Backward compatibility: wallet module stores raw secp256k1 hex keys.
            sk = SigningKey.from_string(bytes.fromhex(private_key), curve=SECP256k1)
        signature = sk.sign(_canonical_json(tx_data))
        return signature.hex()
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("No se pudo firmar la transaccion") from exc


def verificar_firma(tx_data: dict[str, Any], firma: str, public_key: str) -> bool:
    """Verify transaction signature against public PEM key."""
    if not isinstance(firma, str) or not firma:
        return False
    if not isinstance(public_key, str) or not public_key.strip():
        return False

    try:
        try:
            vk = VerifyingKey.from_pem(public_key)
        except Exception:
            # Backward compatibility: wallet module stores raw secp256k1 hex keys.
            vk = VerifyingKey.from_string(bytes.fromhex(public_key), curve=SECP256k1)
        return vk.verify(bytes.fromhex(firma), _canonical_json(tx_data))
    except (BadSignatureError, ValueError):
        return False
    except Exception:
        return False


def firmar_bloque(block_data: dict[str, Any], private_key: str) -> str:
    """Sign block payload with the same ECDSA strategy as transactions."""
    return firmar_transaccion(block_data, private_key)


def generar_nonce() -> str:
    """Create one-time nonce and register it with expiration for replay protection."""
    nonce = secrets.token_urlsafe(24)
    now = time.time()

    with _nonce_lock:
        _cleanup_expired(now)
        _nonce_store[nonce] = now

    return nonce


def _cleanup_expired(now: float) -> None:
    """Remove expired nonces from memory store."""
    expired = [k for k, created_at in _nonce_store.items() if now - created_at > _NONCE_TTL_SECONDS]
    for key in expired:
        _nonce_store.pop(key, None)


def verificar_nonce(nonce: str) -> bool:
    """Validate nonce existence and consume it to prevent reuse."""
    if not isinstance(nonce, str) or len(nonce) < 16:
        return False

    now = time.time()
    with _nonce_lock:
        _cleanup_expired(now)
        if nonce not in _nonce_store:
            return False

        # Consume nonce immediately for one-time semantics.
        _nonce_store.pop(nonce, None)
        return True
