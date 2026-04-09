from __future__ import annotations

from hashlib import sha256
import json
from typing import Any

from blockchain_client import BlockchainError, hold_in_escrow, refund_from_escrow
import p2p_repository as repo
from p2p_common import require_non_empty, require_positive

ASSET_CODE = "BEN"
ASSET_NAME = "BENDICION"
ALLOWED_COMPLETION_MINUTES = {10, 15, 30, 60}


def create_offer(payload: dict[str, Any]) -> dict[str, Any]:
    user_id = require_non_empty(payload.get("user_id", ""), "user_id")
    side = require_non_empty(payload.get("side", ""), "side").lower()
    if side not in {"buy", "sell"}:
        raise ValueError("side debe ser buy o sell")

    amount_total = require_positive(payload.get("amount_total"), "amount_total")
    price = require_positive(payload.get("price"), "price")

    min_limit = float(payload.get("min_limit") or 0)
    max_limit = float(payload.get("max_limit") or 0)
    if min_limit < 0 or max_limit < 0:
        raise ValueError("min_limit y max_limit no pueden ser negativos")
    if max_limit > 0 and min_limit > max_limit:
        raise ValueError("min_limit no puede ser mayor que max_limit")

    completion_time_minutes = int(payload.get("completion_time_minutes") or 15)
    if completion_time_minutes not in ALLOWED_COMPLETION_MINUTES:
        raise ValueError("completion_time_minutes debe ser 10, 15, 30 o 60")

    data = {
        "user_id": user_id,
        "country": require_non_empty(payload.get("country", ""), "country"),
        "side": side,
        "asset": require_non_empty(payload.get("asset", ASSET_CODE), "asset").upper(),
        "fiat_currency": require_non_empty(payload.get("fiat_currency", "USD"), "fiat_currency").upper(),
        "payment_method": require_non_empty(payload.get("payment_method", "TRANSFER"), "payment_method"),
        "payment_provider": require_non_empty(payload.get("payment_provider", ""), "payment_provider"),
        "account_reference": require_non_empty(payload.get("account_reference", ""), "account_reference"),
        "account_holder": require_non_empty(payload.get("account_holder", ""), "account_holder"),
        "price": price,
        "amount_total": amount_total,
        "min_limit": min_limit,
        "max_limit": max_limit,
        "completion_time_minutes": completion_time_minutes,
        "terms": str(payload.get("terms") or "").strip(),
    }

    if data["asset"] != ASSET_CODE:
        raise ValueError(f"Solo se permite {ASSET_NAME} ({ASSET_CODE}) en este mercado")

    return repo.create_offer(data)


def list_offers(side: str | None = None, asset: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    if limit <= 0:
        limit = 50
    if limit > 200:
        limit = 200

    norm_side = side.lower() if isinstance(side, str) and side else None
    norm_asset = ASSET_CODE
    if isinstance(asset, str) and asset and asset.upper() != ASSET_CODE:
        return []
    return repo.list_active_offers(norm_side, norm_asset, limit)


def take_offer(offer_id: str, taker_user_id: str, amount: float) -> dict[str, Any]:
    offer_id = require_non_empty(offer_id, "offer_id")
    taker_user_id = require_non_empty(taker_user_id, "taker_user_id")
    amount = require_positive(amount, "amount")

    offer = repo.get_offer(offer_id)
    if not offer:
        raise ValueError("Oferta no encontrada")
    if offer["status"] != "active":
        raise ValueError("La oferta no esta activa")
    if offer["user_id"] == taker_user_id:
        raise ValueError("No puedes tomar tu propia oferta")
    if float(offer["amount_available"]) < amount:
        raise ValueError("Cantidad insuficiente en oferta")

    seller_id = offer["user_id"] if offer["side"] == "sell" else taker_user_id
    hold_metadata = {
        "source": "p2p_take_offer",
        "offer_id": offer_id,
        "seller_id": seller_id,
        "taker_user_id": taker_user_id,
        "amount": float(amount),
        "asset": ASSET_CODE,
    }
    hold_tx_id = sha256(json.dumps(hold_metadata, sort_keys=True).encode()).hexdigest()

    try:
        hold_in_escrow(seller_id, amount, tx_id=hold_tx_id, metadata=hold_metadata)
    except BlockchainError as exc:
        raise ValueError(f"No se pudo bloquear saldo en blockchain: {exc}") from exc

    try:
        return repo.take_offer(offer_id, taker_user_id, amount)
    except Exception as exc:
        rollback_metadata = {
            "source": "p2p_take_offer_rollback",
            "offer_id": offer_id,
            "seller_id": seller_id,
            "taker_user_id": taker_user_id,
            "amount": float(amount),
            "reason": str(exc),
        }
        rollback_tx_id = sha256(json.dumps(rollback_metadata, sort_keys=True).encode()).hexdigest()
        try:
            refund_from_escrow(seller_id, amount, tx_id=rollback_tx_id, metadata=rollback_metadata)
        except BlockchainError:
            pass
        raise


def cancel_offer(offer_id: str, requester_user_id: str) -> dict[str, Any]:
    offer_id = require_non_empty(offer_id, "offer_id")
    requester_user_id = require_non_empty(requester_user_id, "requester_user_id")
    return repo.cancel_offer(offer_id, requester_user_id)
