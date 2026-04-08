"""REST API server for the P2P marketplace."""

from __future__ import annotations

from flask import Flask, jsonify, request
from flask_cors import CORS

import p2p
from p2p_db import health_check

app = Flask(__name__)
CORS(app)


def _json_body() -> dict:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError("Payload JSON invalido")
    return data


def _ok(payload: dict, code: int = 200):
    return jsonify(payload), code


def _error(message: str, code: int = 400):
    return jsonify({"success": False, "error": message}), code


@app.get("/health")
def api_health():
    return _ok({"success": True, "db": health_check()})


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
        order = p2p.take_offer(
            offer_id=payload.get("offer_id", ""),
            taker_user_id=payload.get("taker_user_id", ""),
            amount=payload.get("amount"),
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


@app.post("/demo/create-example-order")
def api_demo_create_example_order():
    """Create a demo offer and immediately take it to produce a valid order."""
    try:
        payload = _json_body()
        seller_id = payload.get("seller_id", "seller_demo")
        buyer_id = payload.get("buyer_id", "buyer_demo")

        offer = p2p.create_offer(
            {
                "user_id": seller_id,
                "country": payload.get("country", "Espana"),
                "side": "sell",
                "asset": "BEN",
                "fiat_currency": payload.get("fiat_currency", "EUR"),
                "payment_method": payload.get("payment_method", "Bizum"),
                "payment_provider": payload.get("payment_provider", "BBVA"),
                "account_reference": payload.get("account_reference", "600123456"),
                "account_holder": payload.get("account_holder", "Titular Demo"),
                "price": float(payload.get("price", 1.0)),
                "amount_total": float(payload.get("amount_total", 100.0)),
                "min_limit": float(payload.get("min_limit", 10.0)),
                "max_limit": float(payload.get("max_limit", 300.0)),
                "completion_time_minutes": int(payload.get("completion_time_minutes", 30)),
                "terms": payload.get("terms", "Demo de orden P2P BEN"),
            }
        )

        order = p2p.take_offer(offer["id"], buyer_id, float(payload.get("take_amount", 25.0)))
        return _ok({"success": True, "offer": offer, "order": order}, 201)
    except Exception as exc:
        return _error(f"No se pudo crear la orden de ejemplo: {exc}", 500)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5012, debug=True)
