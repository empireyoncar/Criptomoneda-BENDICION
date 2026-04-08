"""WebSocket chat server for P2P order rooms."""

from __future__ import annotations

import json
import os
import threading
from collections import defaultdict
from typing import Any

import jwt
from flask import Flask, request
from flask_cors import CORS
from flask_sock import Sock

import p2p

app = Flask(__name__)
CORS(app)
sock = Sock(app)

_rooms: dict[str, set[Any]] = defaultdict(set)
_rooms_lock = threading.Lock()


def _decode_token(token: str) -> dict[str, Any]:
    secret = os.getenv("P2P_JWT_SECRET", "")
    if not secret:
        raise ValueError("P2P_JWT_SECRET no configurado")
    return jwt.decode(token, secret, algorithms=["HS256"])


def _resolve_user_id() -> str:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        payload = _decode_token(auth.split(" ", 1)[1])
        user_id = str(payload.get("sub", "")).strip()
        if not user_id:
            raise ValueError("Token sin sub")
        return user_id

    # Fallback local dev.
    user_id = str(request.args.get("user_id", "")).strip()
    if not user_id:
        raise ValueError("Falta autenticacion")
    return user_id


def _broadcast(room: str, payload: dict[str, Any]) -> None:
    text = json.dumps(payload)
    with _rooms_lock:
        sockets = list(_rooms.get(room, set()))

    for ws in sockets:
        try:
            ws.send(text)
        except Exception:
            with _rooms_lock:
                _rooms[room].discard(ws)


@sock.route("/ws/order/<order_id>")
def ws_order_chat(ws, order_id: str):
    room = f"order:{order_id}"

    try:
        user_id = _resolve_user_id()
        if not p2p.is_order_participant(order_id, user_id) and not user_id.startswith("admin"):
            ws.send(json.dumps({"type": "error", "error": "No autorizado para esta orden"}))
            ws.close()
            return
    except Exception as exc:
        ws.send(json.dumps({"type": "error", "error": str(exc)}))
        ws.close()
        return

    with _rooms_lock:
        _rooms[room].add(ws)

    ws.send(json.dumps({"type": "connected", "order_id": order_id, "user_id": user_id}))

    try:
        while True:
            raw = ws.receive()
            if raw is None:
                break

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                ws.send(json.dumps({"type": "error", "error": "Payload JSON invalido"}))
                continue

            text = str(data.get("message", "")).strip()
            if not text:
                ws.send(json.dumps({"type": "error", "error": "Mensaje vacio"}))
                continue

            saved = p2p.send_chat_message(order_id, user_id, text)
            _broadcast(room, {"type": "message", "message": saved})

    finally:
        with _rooms_lock:
            _rooms[room].discard(ws)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5014, debug=True)
