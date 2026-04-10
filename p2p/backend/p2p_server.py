"""REST API server for the P2P marketplace."""

from __future__ import annotations

import threading
import time

from flask import Flask, jsonify, request
from flask_cors import CORS

import p2p
from blockchain_client import BlockchainError, get_connection_status
from p2p_db import health_check

app = Flask(__name__)
CORS(app)

_presence_lock = threading.Lock()
_presence_last_seen: dict[str, float] = {}
_PRESENCE_TTL_SECONDS = 45


def _json_body() -> dict:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError("Payload JSON invalido")
    return data


def _ok(payload: dict, code: int = 200):
    return jsonify(payload), code


def _error(message: str, code: int = 400):
    return jsonify({"success": False, "error": message}), code


def _mark_online(user_id: str) -> None:
    if not isinstance(user_id, str) or not user_id.strip():
        return
    with _presence_lock:
        _presence_last_seen[user_id.strip()] = time.time()


def _is_online(user_id: str) -> bool:
    now = time.time()
    with _presence_lock:
        expired = [key for key, ts in _presence_last_seen.items() if now - ts > _PRESENCE_TTL_SECONDS]
        for key in expired:
            _presence_last_seen.pop(key, None)
        last_seen = _presence_last_seen.get(user_id)
    return bool(last_seen and now - last_seen <= _PRESENCE_TTL_SECONDS)


@app.get("/health")
def api_health():
    blockchain = {"ok": False, "error": "No verificado"}
    try:
        blockchain = get_connection_status()
    except BlockchainError as exc:
        blockchain = {"ok": False, "error": str(exc)}
    return _ok({"success": True, "db": health_check(), "blockchain": blockchain})


@app.get("/health/blockchain")
def api_health_blockchain():
    try:
        status = get_connection_status()
        return _ok({"success": True, "blockchain": status})
    except BlockchainError as exc:
        return _ok({"success": False, "blockchain": {"ok": False, "error": str(exc)}}, 503)


@app.get("/offers")
def api_list_offers():
    side = request.args.get("side")
    asset = request.args.get("asset")
    limit = int(request.args.get("limit", "50"))
    offers = p2p.list_offers(side=side, asset=asset, limit=limit)
    return _ok({"success": True, "offers": offers})


@app.post("/offers")
def api_create_offer():
    try:
        payload = _json_body()
        offer = p2p.create_offer(payload)
        return _ok({"success": True, "offer": offer}, 201)
    except ValueError as exc:
        return _error(str(exc), 400)
    except Exception as exc:
        return _error(f"Error interno al crear oferta: {exc}", 500)


@app.post("/orders/take")
def api_take_offer():
    try:
        payload = _json_body()
        signer_payload = {
            "seller_wallet": payload.get("seller_wallet") or payload.get("wallet_address"),
            "public_key": payload.get("public_key"),
            "signature": payload.get("signature"),
            "nonce": payload.get("nonce"),
        }

        order = p2p.take_offer(
            offer_id=payload.get("offer_id", ""),
            taker_user_id=payload.get("taker_user_id", ""),
            amount=payload.get("amount"),
            current_wallet=payload.get("wallet_address", ""),
            signer_payload=signer_payload,
        )
        return _ok({"success": True, "order": order}, 201)
    except (ValueError, PermissionError) as exc:
        return _error(str(exc), 400)
    except Exception as exc:
        return _error(f"Error interno al tomar oferta: {exc}", 500)


@app.get("/orders/<order_id>")
def api_get_order_detail(order_id: str):
    try:
        order = p2p.get_order_detail(order_id)
        return _ok({"success": True, "order": order})
    except ValueError as exc:
        return _error(str(exc), 404)
    except Exception as exc:
        return _error(f"Error interno al consultar orden: {exc}", 500)


@app.post("/presence/heartbeat")
def api_presence_heartbeat():
    try:
        payload = _json_body()
        user_id = str(payload.get("user_id", "")).strip()
        if not user_id:
            raise ValueError("user_id es requerido")
        _mark_online(user_id)
        return _ok({"success": True, "user_id": user_id, "online": True})
    except ValueError as exc:
        return _error(str(exc), 400)
    except Exception as exc:
        return _error(f"Error interno de presencia: {exc}", 500)


@app.get("/orders/<order_id>/presence")
def api_order_presence(order_id: str):
    try:
        requester_user_id = str(request.args.get("requester_user_id", "")).strip()
        detail = p2p.get_order_detail(order_id)
        if requester_user_id not in {detail["buyer_id"], detail["seller_id"]} and requester_user_id not in {"001"} and not requester_user_id.startswith("admin"):
            raise PermissionError("No tienes acceso a la presencia de esta orden")

        _mark_online(requester_user_id)
        presence = {
            "buyer_id": detail["buyer_id"],
            "buyer_online": _is_online(detail["buyer_id"]),
            "seller_id": detail["seller_id"],
            "seller_online": _is_online(detail["seller_id"]),
        }
        return _ok({"success": True, "presence": presence})
    except (ValueError, PermissionError) as exc:
        return _error(str(exc), 400)
    except Exception as exc:
        return _error(f"Error interno al consultar presencia: {exc}", 500)


@app.get("/orders/online")
def api_orders_online():
    try:
        user_id = str(request.args.get("user_id", "")).strip()
        role = str(request.args.get("role", "seller")).strip() or "seller"
        limit = int(request.args.get("limit", "100"))
        orders = p2p.list_user_orders(user_id=user_id, role=role, limit=limit)
        return _ok({"success": True, "orders": orders})
    except (ValueError, PermissionError) as exc:
        return _error(str(exc), 400)
    except Exception as exc:
        return _error(f"Error interno al cargar ordenes online: {exc}", 500)


@app.get("/orders/online/status")
def api_orders_online_status():
    try:
        user_id = str(request.args.get("user_id", "")).strip()
        orders = p2p.list_user_orders(user_id=user_id, role="participant", limit=100)
        active = [o for o in orders if o.get("status") in {"pending_payment", "paid", "disputed", "released"}]
        color = "gray"
        if any(o.get("status") == "paid" for o in active):
            color = "white"
        elif any(o.get("status") == "pending_payment" for o in active):
            color = "red"
        return _ok({"success": True, "count": len(active), "color": color})
    except Exception as exc:
        return _error(f"Error interno al calcular estado de ordenes online: {exc}", 500)


@app.get("/orders/<order_id>/timeout/status")
def api_timeout_status(order_id: str):
    try:
        requester_user_id = str(request.args.get("requester_user_id", "")).strip()
        status = p2p.get_timeout_status(order_id, requester_user_id)
        return _ok({"success": True, "timeout": status})
    except (ValueError, PermissionError) as exc:
        return _error(str(exc), 400)
    except Exception as exc:
        return _error(f"Error interno al consultar timeout: {exc}", 500)


@app.post("/orders/<order_id>/timeout/vote")
def api_timeout_vote(order_id: str):
    try:
        payload = _json_body()
        status = p2p.submit_timeout_vote(
            order_id=order_id,
            user_id=str(payload.get("user_id", "")).strip(),
            cancel_requested=bool(payload.get("cancel_requested", False)),
        )
        return _ok({"success": True, "timeout": status})
    except (ValueError, PermissionError) as exc:
        return _error(str(exc), 400)
    except Exception as exc:
        return _error(f"Error interno al registrar voto de timeout: {exc}", 500)


@app.post("/orders/<order_id>/pay")
def api_mark_paid(order_id: str):
    try:
        payload = _json_body()
        order = p2p.mark_paid(order_id, payload.get("buyer_id", ""), payload.get("payment_proof_url"))
        return _ok({"success": True, "order": order})
    except (ValueError, PermissionError) as exc:
        return _error(str(exc), 400)
    except Exception as exc:
        return _error(f"Error interno al marcar pago: {exc}", 500)


@app.post("/orders/<order_id>/release")
def api_release_order(order_id: str):
    try:
        payload = _json_body()
        order = p2p.release_order(order_id, payload.get("seller_id", ""))
        return _ok({"success": True, "order": order})
    except (ValueError, PermissionError) as exc:
        return _error(str(exc), 400)
    except Exception as exc:
        return _error(f"Error interno al liberar orden: {exc}", 500)


@app.post("/orders/<order_id>/refund")
def api_refund_order(order_id: str):
    try:
        payload = _json_body()
        order = p2p.refund_order(order_id, payload.get("actor_user_id", ""))
        return _ok({"success": True, "order": order})
    except (ValueError, PermissionError) as exc:
        return _error(str(exc), 400)
    except Exception as exc:
        return _error(f"Error interno al reembolsar orden: {exc}", 500)


@app.post("/orders/<order_id>/dispute")
def api_open_dispute(order_id: str):
    try:
        payload = _json_body()
        dispute = p2p.open_dispute(
            order_id=order_id,
            opened_by_user_id=payload.get("opened_by_user_id", ""),
            reason=payload.get("reason", ""),
            evidence=payload.get("evidence", []),
        )
        return _ok({"success": True, "dispute": dispute}, 201)
    except (ValueError, PermissionError) as exc:
        return _error(str(exc), 400)
    except Exception as exc:
        return _error(f"Error interno al abrir disputa: {exc}", 500)


@app.post("/orders/<order_id>/dispute/resolve")
def api_resolve_dispute(order_id: str):
    try:
        payload = _json_body()
        dispute = p2p.resolve_dispute(
            order_id=order_id,
            admin_id=payload.get("admin_id", ""),
            resolution=payload.get("resolution", ""),
            note=payload.get("note", ""),
        )
        return _ok({"success": True, "dispute": dispute})
    except (ValueError, PermissionError) as exc:
        return _error(str(exc), 400)
    except Exception as exc:
        return _error(f"Error interno al resolver disputa: {exc}", 500)


@app.get("/orders/<order_id>/chat")
def api_chat_history(order_id: str):
    try:
        requester_user_id = request.args.get("requester_user_id", "")
        limit = int(request.args.get("limit", "200"))
        messages = p2p.list_chat_messages(order_id, requester_user_id, limit)
        return _ok({"success": True, "messages": messages})
    except (ValueError, PermissionError) as exc:
        return _error(str(exc), 400)
    except Exception as exc:
        return _error(f"Error interno al cargar chat: {exc}", 500)


@app.post("/orders/<order_id>/chat")
def api_send_chat(order_id: str):
    try:
        payload = _json_body()
        message = p2p.send_chat_message(
            order_id=order_id,
            sender_user_id=payload.get("sender_user_id", ""),
            message=payload.get("message", ""),
            message_type=payload.get("message_type", "text"),
        )
        return _ok({"success": True, "message": message}, 201)
    except (ValueError, PermissionError) as exc:
        return _error(str(exc), 400)
    except Exception as exc:
        return _error(f"Error interno al enviar mensaje: {exc}", 500)


@app.post("/orders/<order_id>/ratings")
def api_rate(order_id: str):
    try:
        payload = _json_body()
        rating = p2p.submit_rating(
            order_id=order_id,
            from_user_id=payload.get("from_user_id", ""),
            score=payload.get("score"),
            comment=payload.get("comment", ""),
        )
        return _ok({"success": True, "rating": rating}, 201)
    except (ValueError, PermissionError) as exc:
        return _error(str(exc), 400)
    except Exception as exc:
        return _error(f"Error interno al registrar rating: {exc}", 500)


@app.get("/users/<user_id>/reputation")
def api_reputation(user_id: str):
    try:
        rep = p2p.get_reputation(user_id)
        return _ok({"success": True, "reputation": rep})
    except ValueError as exc:
        return _error(str(exc), 400)
    except Exception as exc:
        return _error(f"Error interno al consultar reputacion: {exc}", 500)


@app.post("/users/<user_id>/profile")
def api_update_profile(user_id: str):
    try:
        payload = _json_body()
        profile = p2p.update_profile(
            user_id=user_id,
            actor_user_id=payload.get("actor_user_id", ""),
            bio=payload.get("bio", ""),
        )
        return _ok({"success": True, "profile": profile})
    except (ValueError, PermissionError) as exc:
        return _error(str(exc), 400)
    except Exception as exc:
        return _error(f"Error interno al actualizar perfil: {exc}", 500)


@app.get("/disputes")
def api_list_disputes():
    try:
        requester_user_id = str(request.args.get("requester_user_id", "")).strip()
        status = str(request.args.get("status", "open")).strip()
        limit = int(request.args.get("limit", "100"))
        disputes = p2p.list_disputes(requester_user_id=requester_user_id, status=status, limit=limit)
        return _ok({"success": True, "disputes": disputes})
    except (ValueError, PermissionError) as exc:
        return _error(str(exc), 400)
    except Exception as exc:
        return _error(f"Error interno al listar disputas: {exc}", 500)


@app.get("/disputes/<order_id>")
def api_get_dispute(order_id: str):
    try:
        requester_user_id = str(request.args.get("requester_user_id", "")).strip()
        dispute = p2p.get_dispute_detail(order_id=order_id, requester_user_id=requester_user_id)
        return _ok({"success": True, "dispute": dispute})
    except (ValueError, PermissionError) as exc:
        return _error(str(exc), 400)
    except Exception as exc:
        return _error(f"Error interno al cargar disputa: {exc}", 500)


@app.post("/offers/<offer_id>/cancel")
def api_cancel_offer(offer_id: str):
    try:
        payload = _json_body()
        offer = p2p.cancel_offer(offer_id=offer_id, requester_user_id=payload.get("user_id", ""))
        return _ok({"success": True, "offer": offer})
    except (ValueError, PermissionError) as exc:
        return _error(str(exc), 400)
    except Exception as exc:
        return _error(f"Error interno al cancelar oferta: {exc}", 500)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5012, debug=True)
