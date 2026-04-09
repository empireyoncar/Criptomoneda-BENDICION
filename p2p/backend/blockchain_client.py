"""HTTP client for blockchain operations used by P2P escrow flows."""

from __future__ import annotations

import os
from typing import Any

import requests

BLOCKCHAIN_URL = os.getenv("BLOCKCHAIN_URL", "http://blockchain_api:5004").rstrip("/")
ESCROW_WALLET = os.getenv("P2P_ESCROW_WALLET", "P2P_ESCROW")
REQUEST_TIMEOUT_SECONDS = float(os.getenv("P2P_BLOCKCHAIN_TIMEOUT_SECONDS", "8"))


class BlockchainError(RuntimeError):
    """Raised when blockchain API call fails or returns unexpected payload."""


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


def hold_in_escrow(from_wallet: str, amount: float, tx_id: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Move funds from seller wallet to escrow wallet."""
    tx_payload = {
        "tx": {
            "from": from_wallet,
            "to": ESCROW_WALLET,
            "amount": float(amount),
            "tx_id": tx_id,
            "metadata": metadata or {},
        }
    }
    send_result = _post_json("/send_tx", tx_payload)
    commit_result = _post_json("/commit", {})
    return {"send": send_result, "commit": commit_result}


def release_from_escrow(to_wallet: str, amount: float, tx_id: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Move funds from escrow wallet to buyer wallet."""
    tx_payload = {
        "tx": {
            "from": ESCROW_WALLET,
            "to": to_wallet,
            "amount": float(amount),
            "tx_id": tx_id,
            "metadata": metadata or {},
        }
    }
    send_result = _post_json("/send_tx", tx_payload)
    commit_result = _post_json("/commit", {})
    return {"send": send_result, "commit": commit_result}


def refund_from_escrow(to_wallet: str, amount: float, tx_id: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Move funds from escrow wallet back to seller wallet."""
    tx_payload = {
        "tx": {
            "from": ESCROW_WALLET,
            "to": to_wallet,
            "amount": float(amount),
            "tx_id": tx_id,
            "metadata": metadata or {},
        }
    }
    send_result = _post_json("/send_tx", tx_payload)
    commit_result = _post_json("/commit", {})
    return {"send": send_result, "commit": commit_result}


def get_connection_status() -> dict[str, Any]:
    """Return blockchain connectivity and basic status for UI/health checks."""
    data = _get_json("/validate")
    return {
        "ok": True,
        "url": BLOCKCHAIN_URL,
        "chain_valid": bool(data.get("valid", False)),
    }
