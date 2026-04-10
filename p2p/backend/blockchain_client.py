"""HTTP client for blockchain operations used by P2P escrow flows."""

from __future__ import annotations

import json
import os
from hashlib import sha256
from typing import Any

import requests
from ecdsa import SECP256k1, SigningKey
from ecdsa.util import sigencode_string

BLOCKCHAIN_URL = os.getenv("BLOCKCHAIN_URL", "http://blockchain_api:5004").rstrip("/")
ESCROW_PRIVATE_KEY = os.getenv("P2P_ESCROW_PRIVATE_KEY", "").strip().lower()
ESCROW_PUBLIC_KEY = os.getenv("P2P_ESCROW_PUBLIC_KEY", "").strip().lower()
ESCROW_WALLET = os.getenv("P2P_ESCROW_WALLET", "").strip().lower()
REQUEST_TIMEOUT_SECONDS = float(os.getenv("P2P_BLOCKCHAIN_TIMEOUT_SECONDS", "8"))


class BlockchainError(RuntimeError):
    """Raised when blockchain API call fails or returns unexpected payload."""


def _canonical_json(data: dict[str, Any]) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sign_payload(private_key_hex: str, payload: dict[str, Any]) -> str:
    digest = sha256(_canonical_json(payload)).digest()
    signer = SigningKey.from_string(bytes.fromhex(private_key_hex), curve=SECP256k1)
    return signer.sign_digest_deterministic(digest, sigencode=sigencode_string).hex()


def _resolve_escrow_credentials() -> tuple[str, str, str]:
    if not ESCROW_PRIVATE_KEY:
        raise BlockchainError("Falta configurar P2P_ESCROW_PRIVATE_KEY")

    signer = SigningKey.from_string(bytes.fromhex(ESCROW_PRIVATE_KEY), curve=SECP256k1)
    public_key = ESCROW_PUBLIC_KEY or signer.get_verifying_key().to_string().hex()
    wallet_address = sha256(public_key.encode()).hexdigest()

    if ESCROW_WALLET and ESCROW_WALLET != wallet_address:
        raise BlockchainError("P2P_ESCROW_WALLET no coincide con la clave configurada")

    return wallet_address, public_key, ESCROW_PRIVATE_KEY


def _get_wallet_nonce(address: str) -> int:
    data = _get_json(f"/wallet/{address}/nonce")
    return int(data.get("nonce", 0))


def _send_signed_escrow_tx(to_wallet: str, amount: float, tx_id: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    escrow_wallet, escrow_public_key, escrow_private_key = _resolve_escrow_credentials()
    nonce = _get_wallet_nonce(escrow_wallet)
    tx = {
        "from": escrow_wallet,
        "to": to_wallet,
        "amount": float(amount),
        "tx_id": tx_id,
        "metadata": metadata or {},
        "nonce": nonce,
    }
    # Sign first, then add public_key/signature to payload for transmission
    signature = _sign_payload(escrow_private_key, tx)
    tx["public_key"] = escrow_public_key
    tx["signature"] = signature

    send_result = _post_json("/send_tx", {"tx": tx})
    commit_result = _post_json("/commit", {})
    return {"send": send_result, "commit": commit_result}


def _get_json(path: str) -> dict[str, Any]:
    url = f"{BLOCKCHAIN_URL}{path}"
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        raise BlockchainError(f"No se pudo conectar a blockchain: {exc}") from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise BlockchainError("Respuesta invalida de blockchain") from exc

    if response.status_code >= 400:
        message = str(data.get("error") or data.get("message") or "Error de blockchain")
        raise BlockchainError(message)

    return data


def _post_json(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    url = f"{BLOCKCHAIN_URL}{path}"
    try:
        response = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        raise BlockchainError(f"No se pudo conectar a blockchain: {exc}") from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise BlockchainError("Respuesta invalida de blockchain") from exc

    if response.status_code >= 400:
        message = str(data.get("error") or data.get("message") or "Error de blockchain")
        raise BlockchainError(message)

    return data


def hold_in_escrow(
    from_wallet: str,
    amount: float,
    tx_id: str,
    metadata: dict[str, Any] | None = None,
    public_key: str | None = None,
    signature: str | None = None,
    nonce: int | None = None,
) -> dict[str, Any]:
    """Move funds from seller wallet to escrow wallet."""
    tx = {
        "from": from_wallet,
        "to": ESCROW_WALLET,
        "amount": float(amount),
        "tx_id": tx_id,
        "metadata": metadata or {},
    }
    if public_key:
        tx["public_key"] = public_key
    if signature:
        tx["signature"] = signature
    if nonce is not None:
        tx["nonce"] = int(nonce)

    tx_payload = {"tx": tx}
    send_result = _post_json("/send_tx", tx_payload)
    commit_result = _post_json("/commit", {})
    return {"send": send_result, "commit": commit_result}


def release_from_escrow(to_wallet: str, amount: float, tx_id: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Move funds from escrow wallet to buyer wallet."""
    return _send_signed_escrow_tx(to_wallet=to_wallet, amount=amount, tx_id=tx_id, metadata=metadata)


def refund_from_escrow(to_wallet: str, amount: float, tx_id: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Move funds from escrow wallet back to seller wallet."""
    return _send_signed_escrow_tx(to_wallet=to_wallet, amount=amount, tx_id=tx_id, metadata=metadata)


def get_connection_status() -> dict[str, Any]:
    """Return blockchain connectivity and basic status for UI/health checks."""
    data = _get_json("/validate")
    return {
        "ok": True,
        "url": BLOCKCHAIN_URL,
        "chain_valid": bool(data.get("valid", False)),
    }
