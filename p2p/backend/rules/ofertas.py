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


def require_positive_integer_amount(value: Any, field_name: str) -> int:
    amount = require_positive(value, field_name)
    if not float(amount).is_integer():
        raise ValueError(f"{field_name} debe ser entero en satichis")
    return int(amount)


def _ensure_dict(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} debe ser un objeto JSON")
    return value


def create_offer(payload: dict[str, Any]) -> dict[str, Any]:
    user_id = require_non_empty(payload.get("user_id", ""), "user_id")
    side = require_non_empty(payload.get("side", ""), "side").lower()
    if side not in {"buy", "sell"}:
        raise ValueError("side debe ser buy o sell")

    amount_total = require_positive_integer_amount(payload.get("amount_total"), "amount_total")
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
        "wallet_address": require_non_empty(payload.get("wallet_address", ""), "wallet_address"),
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

    # En ofertas de venta, bloqueamos el saldo en escrow desde el inicio.
    if side == "sell":
        hold_metadata = _ensure_dict(payload.get("metadata"), "metadata")
        hold_tx_id = require_non_empty(payload.get("tx_id", ""), "tx_id")

        if hold_metadata.get("source") != "p2p_create_offer_sell":
            raise ValueError("metadata.source invalido para crear oferta de venta")
        if str(hold_metadata.get("offer_creator_id", "")) != user_id:
            raise ValueError("metadata.offer_creator_id no coincide con user_id")
        if str(hold_metadata.get("asset", "")).upper() != ASSET_CODE:
            raise ValueError("metadata.asset invalido")
        if require_positive_integer_amount(hold_metadata.get("amount"), "metadata.amount") != amount_total:
            raise ValueError("metadata.amount no coincide con amount_total")

        signer_public_key = require_non_empty(payload.get("public_key", ""), "public_key")
        signer_signature = require_non_empty(payload.get("signature", ""), "signature")
        signer_nonce = payload.get("nonce")
        if signer_nonce is None:
            raise ValueError("nonce es requerido para bloquear saldo en ofertas de venta")

        try:
            hold_in_escrow(
                from_wallet=data["wallet_address"],
                amount=amount_total,
                tx_id=hold_tx_id,
                metadata=hold_metadata,
                public_key=signer_public_key,
                signature=signer_signature,
                nonce=int(signer_nonce),
            )
        except BlockchainError as exc:
            raise ValueError(f"No se pudo bloquear saldo en blockchain al crear oferta: {exc}") from exc

        data["escrow_locked"] = True
        data["escrow_lock_tx_id"] = hold_tx_id
    else:
        data["escrow_locked"] = False
        data["escrow_lock_tx_id"] = None

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


def take_offer(offer_id: str, taker_user_id: str, amount: float, current_wallet: str, signer_payload: dict[str, Any] | None = None) -> dict[str, Any]:
    offer_id = require_non_empty(offer_id, "offer_id")
    taker_user_id = require_non_empty(taker_user_id, "taker_user_id")
    amount = require_positive_integer_amount(amount, "amount")

    offer = repo.get_offer(offer_id)
    if not offer:
        raise ValueError("Oferta no encontrada")
    if offer["status"] != "active":
        raise ValueError("La oferta no esta activa")
    if offer["user_id"] == taker_user_id:
        raise ValueError("No puedes tomar tu propia oferta")
    if float(offer["amount_available"]) < amount:
        raise ValueError("Cantidad insuficiente en oferta")

    current_wallet = require_non_empty(current_wallet, "wallet_address")

    signer_payload = signer_payload or {}
    seller_id = offer["user_id"] if offer["side"] == "sell" else taker_user_id
    buyer_wallet = current_wallet if offer["side"] == "sell" else str(offer.get("wallet_address") or "")
    seller_wallet = str(offer.get("wallet_address") or "") if offer["side"] == "sell" else ""

    # Oferta sell: saldo ya bloqueado por el creador al publicar.
    if offer["side"] == "sell":
        if not bool(offer.get("escrow_locked")):
            raise ValueError("La oferta de venta no tiene saldo bloqueado en escrow")
    else:
        # Oferta buy: el vendedor es el taker, por eso requiere firma del taker al tomar.
        seller_wallet = signer_payload.get("seller_wallet")
        if not seller_wallet:
            raise ValueError("Debes indicar seller_wallet para bloquear saldo")

        signer_public_key = signer_payload.get("public_key")
        signer_signature = signer_payload.get("signature")
        signer_nonce = signer_payload.get("nonce")
        hold_tx_id = signer_payload.get("tx_id")
        hold_metadata = signer_payload.get("metadata")
        if not signer_public_key or not signer_signature or signer_nonce is None or not hold_tx_id:
            raise ValueError("Faltan public_key, signature, nonce o tx_id para bloquear saldo")

        hold_metadata = _ensure_dict(hold_metadata, "metadata")
        if hold_metadata.get("source") != "p2p_take_offer_buy":
            raise ValueError("metadata.source invalido para tomar oferta de compra")
        if str(hold_metadata.get("offer_id", "")) != offer_id:
            raise ValueError("metadata.offer_id no coincide")
        if str(hold_metadata.get("seller_id", "")) != seller_id:
            raise ValueError("metadata.seller_id no coincide")
        if str(hold_metadata.get("taker_user_id", "")) != taker_user_id:
            raise ValueError("metadata.taker_user_id no coincide")
        if str(hold_metadata.get("asset", "")).upper() != ASSET_CODE:
            raise ValueError("metadata.asset invalido")
        if require_positive_integer_amount(hold_metadata.get("amount"), "metadata.amount") != amount:
            raise ValueError("metadata.amount no coincide con amount")

        try:
            hold_in_escrow(
                from_wallet=str(seller_wallet),
                amount=amount,
                tx_id=str(hold_tx_id),
                metadata=hold_metadata,
                public_key=str(signer_public_key),
                signature=str(signer_signature),
                nonce=int(signer_nonce),
            )
        except BlockchainError as exc:
            raise ValueError(f"No se pudo bloquear saldo en blockchain: {exc}") from exc

    try:
        return repo.take_offer(offer_id, taker_user_id, amount, buyer_wallet=buyer_wallet, seller_wallet=seller_wallet)
    except Exception as exc:
        # Solo hacemos rollback automatico cuando el hold se hizo en take_offer (side=buy).
        if offer["side"] == "buy":
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
                refund_from_escrow(str(seller_wallet), amount, tx_id=rollback_tx_id, metadata=rollback_metadata)
            except BlockchainError:
                pass
        raise


def cancel_offer(offer_id: str, requester_user_id: str) -> dict[str, Any]:
    offer_id = require_non_empty(offer_id, "offer_id")
    requester_user_id = require_non_empty(requester_user_id, "requester_user_id")
    offer = repo.get_offer(offer_id)
    if not offer:
        raise ValueError("Oferta no encontrada")

    # Si era una oferta de venta con fondos en escrow, devolvemos el remanente al vendedor.
    if offer.get("side") == "sell" and bool(offer.get("escrow_locked")):
        remaining = float(offer.get("amount_available") or 0)
        if remaining > 0:
            metadata = {
                "source": "p2p_cancel_offer_refund",
                "offer_id": offer_id,
                "seller_id": offer.get("user_id"),
                "remaining": remaining,
            }
            tx_id = sha256(json.dumps(metadata, sort_keys=True).encode()).hexdigest()
            try:
                refund_from_escrow(str(offer.get("wallet_address") or offer.get("user_id")), remaining, tx_id=tx_id, metadata=metadata)
            except BlockchainError as exc:
                raise ValueError(f"No se pudo devolver saldo al cancelar oferta: {exc}") from exc

    return repo.cancel_offer(offer_id, requester_user_id)
