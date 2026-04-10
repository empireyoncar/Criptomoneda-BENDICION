"""Fase 2 – seguridad_api: login / me / refresh / logout via HttpOnly cookies."""

from __future__ import annotations

import hashlib
import os
import sys
import time
import uuid

from flask import Flask, jsonify, make_response, request
from flask_cors import CORS

# ── Importar módulo de cryptografía ──────────────────────────────────────────
sys.path.insert(0, "/app/criptografia")
from tokens import generar_jwt, renovar_jwt, revocar_jwt, verificar_jwt  # noqa: E402

# ── Importar helpers de base de datos de usuarios ────────────────────────────
sys.path.insert(0, "/app/usuarios/backend")
from users_db import run_query  # noqa: E402

# ─────────────────────────────────────────────────────────────────────────────
# Configuración
# ─────────────────────────────────────────────────────────────────────────────
COOKIE_NAME = "session_token"
COOKIE_MAX_AGE = 86400           # 24 h en segundos
REFRESH_WINDOW = 3600            # renovar si quedan menos de 1 h
ACCESS_EXPIRY = 86400            # 24 h para el JWT de acceso
REFRESH_EXPIRY = 7 * 86400      # 7 d para el JWT de refresco

SECURE_COOKIE = os.getenv("SECURE_COOKIE", "true").lower() != "false"
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "https://empireyoncar.duckdns.org"
).split(",")


def _get_allowed_admins() -> set[str]:
    """Administradores que jamás deben eliminarse."""
    env = os.getenv("ALLOWED_ADMIN_IDS", "001,jonatan salazar")
    return {a.strip().lower() for a in env.split(",") if a.strip()}


app = Flask(__name__)
CORS(
    app,
    origins=ALLOWED_ORIGINS,
    supports_credentials=True,
    allow_headers=["Content-Type"],
    methods=["GET", "POST", "OPTIONS"],
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers internos
# ─────────────────────────────────────────────────────────────────────────────

def _hash_password(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _lookup_user(email: str, password_hash: str) -> dict | None:
    rows = run_query(
        "SELECT id, fullname, email, role FROM users "
        "WHERE email = %s AND password = %s LIMIT 1",
        (email, password_hash),
    )
    return dict(rows[0]) if rows else None


def _make_session_cookie(response, token: str) -> None:
    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        secure=SECURE_COOKIE,
        samesite="Lax",
        max_age=COOKIE_MAX_AGE,
        path="/",
    )


def _clear_session_cookie(response) -> None:
    response.set_cookie(
        COOKIE_NAME,
        "",
        httponly=True,
        secure=SECURE_COOKIE,
        samesite="Lax",
        max_age=0,
        path="/",
        expires=0,
    )


def _get_token_from_request() -> str | None:
    # 1º desde cookie HttpOnly
    token = request.cookies.get(COOKIE_NAME)
    if token:
        return token
    # 2º fallback: Authorization: Bearer <token>
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:].strip()
    return None


def _require_auth() -> tuple[dict | None, tuple | None]:
    """
    Verifica el token de sesión.
    Devuelve (payload, None) si válido, o (None, error_response) si no.
    """
    token = _get_token_from_request()
    if not token:
        return None, (jsonify({"error": "No autenticado"}), 401)

    result = verificar_jwt(token)
    if not result.get("valido"):
        return None, (jsonify({"error": result.get("error", "Token inválido")}), 401)

    return result, None


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/seguridad/login")
def login():
    """
    Autentica al usuario y emite un JWT en una cookie HttpOnly.
    Body JSON: { "email": str, "password": str }
    """
    body = request.get_json(silent=True) or {}
    email = str(body.get("email", "")).strip().lower()
    password = str(body.get("password", ""))

    if not email or not password:
        return jsonify({"error": "Email y contraseña requeridos"}), 400

    user = _lookup_user(email, _hash_password(password))
    if not user:
        # Mismo tiempo de respuesta independientemente del resultado (timing-safe)
        time.sleep(0.3)
        return jsonify({"error": "Credenciales incorrectas"}), 401

    user_id = str(user["id"])
    token = generar_jwt(user_id=user_id, expires_in=ACCESS_EXPIRY)

    resp = make_response(jsonify({
        "user_id": user_id,
        "fullname": user.get("fullname", ""),
        "email": user.get("email", ""),
        "role": user.get("role", "user"),
    }))
    _make_session_cookie(resp, token)
    return resp, 200


@app.get("/seguridad/me")
def me():
    """
    Devuelve los datos del usuario autenticado.
    Renueva la cookie automáticamente si el token está próximo a expirar.
    """
    payload, err = _require_auth()
    if err:
        return err

    user_id = str(payload.get("sub", ""))
    rows = run_query(
        "SELECT id, fullname, email, role FROM users WHERE id = %s LIMIT 1",
        (user_id,),
    )
    if not rows:
        return jsonify({"error": "Usuario no encontrado"}), 404

    user = dict(rows[0])
    resp_data = {
        "user_id": str(user["id"]),
        "fullname": user.get("fullname", ""),
        "email": user.get("email", ""),
        "role": user.get("role", "user"),
    }

    resp = make_response(jsonify(resp_data))

    # Auto-renovar si quedan menos de REFRESH_WINDOW segundos
    exp = int(payload.get("exp", 0))
    if exp - int(time.time()) < REFRESH_WINDOW:
        token = _get_token_from_request()
        try:
            new_token = renovar_jwt(token)
            _make_session_cookie(resp, new_token)
        except Exception:
            pass  # silenciar: la cookie vieja aún es válida

    return resp, 200


@app.post("/seguridad/refresh")
def refresh():
    """
    Rota el JWT actual por uno nuevo y actualiza la cookie.
    No requiere body.
    """
    payload, err = _require_auth()
    if err:
        return err

    token = _get_token_from_request()
    try:
        new_token = renovar_jwt(token)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 401

    resp = make_response(jsonify({"refreshed": True}))
    _make_session_cookie(resp, new_token)
    return resp, 200


@app.post("/seguridad/logout")
def logout():
    """
    Revoca el JWT y limpia la cookie de sesión.
    """
    token = _get_token_from_request()
    if token:
        revocar_jwt(token)

    resp = make_response(jsonify({"logged_out": True}))
    _clear_session_cookie(resp)
    return resp, 200


# ─────────────────────────────────────────────────────────────────────────────
# Servidor
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5020, debug=False)
