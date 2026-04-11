"""Fase 2 – seguridad_api: login / me / refresh / logout via HttpOnly cookies."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import sys
import threading
import time
from urllib.parse import urlencode

import bcrypt
import requests as google_requests

from flask import Flask, jsonify, make_response, redirect, request
from flask_cors import CORS

# ── Importar módulo de cryptografía ──────────────────────────────────────────
sys.path.insert(0, "/app/criptografia")
from tokens import generar_jwt, renovar_jwt, revocar_jwt, verificar_jwt  # noqa: E402

# ── Importar helpers de base de datos de usuarios ────────────────────────────
sys.path.insert(0, "/app/usuarios/backend")
from users_db import db_transaction, run_query  # noqa: E402

# ─────────────────────────────────────────────────────────────────────────────
# Configuración
# ─────────────────────────────────────────────────────────────────────────────
COOKIE_NAME = "session_token"
COOKIE_MAX_AGE = 86400           # 24 h en segundos
REFRESH_WINDOW = 3600            # renovar si quedan menos de 1 h
ACCESS_EXPIRY = 86400            # 24 h para el JWT de acceso
REFRESH_EXPIRY = 7 * 86400      # 7 d para el JWT de refresco

MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
LOGIN_WINDOW_SECONDS = int(os.getenv("LOGIN_WINDOW_SECONDS", "300"))
LOGIN_LOCKOUT_SECONDS = int(os.getenv("LOGIN_LOCKOUT_SECONDS", "900"))

SECURE_COOKIE = os.getenv("SECURE_COOKIE", "true").lower() != "false"
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "https://empireyoncar.duckdns.org"
).split(",")


# ── Google OAuth 2.0 config ─────────────────────────────────────────────────
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv(
    "GOOGLE_REDIRECT_URI",
    "https://empireyoncar.duckdns.org/CriptoBendicion/auth/google/callback",
)
APP_BASE_URL = os.getenv("APP_BASE_URL", "https://empireyoncar.duckdns.org")

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
OAUTH_STATE_COOKIE = "oauth_state"


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

_login_attempts: dict[str, dict[str, int]] = {}
_login_attempts_lock = threading.Lock()


# ─────────────────────────────────────────────────────────────────────────────
# Helpers internos
# ─────────────────────────────────────────────────────────────────────────────

def _client_ip() -> str:
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.remote_addr or "unknown"


def _is_legacy_sha256(stored_hash: str) -> bool:
    if len(stored_hash) != 64:
        return False
    return all(char in "0123456789abcdef" for char in stored_hash.lower())


def _lookup_user(email: str) -> dict | None:
    rows = run_query(
        "SELECT id, fullname, email, role, password FROM users "
        "WHERE email = %s LIMIT 1",
        (email,),
    )
    return dict(rows[0]) if rows else None


def _verify_password_and_upgrade_if_needed(user: dict, raw_password: str) -> bool:
    stored_hash = str(user.get("password") or "")
    if not stored_hash:
        return False

    if stored_hash.startswith("$2a$") or stored_hash.startswith("$2b$") or stored_hash.startswith("$2y$"):
        try:
            return bcrypt.checkpw(raw_password.encode("utf-8"), stored_hash.encode("utf-8"))
        except Exception:
            return False

    if not _is_legacy_sha256(stored_hash):
        return False

    import hashlib

    sha_match = hashlib.sha256(raw_password.encode("utf-8")).hexdigest() == stored_hash
    if not sha_match:
        return False

    # Migración transparente a bcrypt tras login válido.
    new_hash = bcrypt.hashpw(raw_password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")
    with db_transaction() as cur:
        cur.execute("UPDATE users SET password = %s WHERE id = %s", (new_hash, str(user["id"])))
    user["password"] = new_hash
    return True


def _attempt_key(email: str, ip: str) -> str:
    return f"{email.lower()}|{ip}"


def _get_lockout_seconds_left(key: str) -> int:
    now = int(time.time())
    with _login_attempts_lock:
        entry = _login_attempts.get(key)
        if not entry:
            return 0
        locked_until = int(entry.get("locked_until", 0))
        if locked_until <= now:
            return 0
        return locked_until - now


def _register_login_failure(key: str) -> None:
    now = int(time.time())
    with _login_attempts_lock:
        entry = _login_attempts.get(key)
        if not entry or now - int(entry.get("first_attempt", now)) > LOGIN_WINDOW_SECONDS:
            entry = {"first_attempt": now, "attempts": 0, "locked_until": 0}
            _login_attempts[key] = entry

        entry["attempts"] = int(entry.get("attempts", 0)) + 1

        if entry["attempts"] >= MAX_LOGIN_ATTEMPTS:
            entry["locked_until"] = now + LOGIN_LOCKOUT_SECONDS
            entry["attempts"] = 0
            entry["first_attempt"] = now


def _reset_login_failures(key: str) -> None:
    with _login_attempts_lock:
        _login_attempts.pop(key, None)


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
    key = _attempt_key(email or "unknown", _client_ip())

    if not email or not password:
        return jsonify({"error": "Email y contraseña requeridos"}), 400

    seconds_left = _get_lockout_seconds_left(key)
    if seconds_left > 0:
        return jsonify({"error": f"Demasiados intentos. Intenta nuevamente en {seconds_left} segundos"}), 429

    user = _lookup_user(email)
    if not user or not _verify_password_and_upgrade_if_needed(user, password):
        _register_login_failure(key)
        # Mismo tiempo de respuesta independientemente del resultado (timing-safe)
        time.sleep(0.3)
        return jsonify({"error": "Credenciales incorrectas"}), 401

    _reset_login_failures(key)

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
# Google OAuth 2.0
# ─────────────────────────────────────────────────────────────────────────────

def _ensure_google_id_column() -> None:
    """Runtime migration: add google_id column if it doesn't exist yet."""
    try:
        with db_transaction() as cur:
            cur.execute(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS "
                "google_id VARCHAR(255) UNIQUE"
            )
    except Exception:
        pass


_ensure_google_id_column()


def _oauth_hmac(state: str) -> str:
    secret = os.getenv("CRIPTO_JWT_SECRET", "default_secret_change_me")
    return hmac.new(secret.encode(), state.encode(), hashlib.sha256).hexdigest()


def _get_or_create_google_user(google_id: str, email: str, name: str) -> dict:
    """Find user by google_id, or by email (and link), or create a new one."""
    rows = run_query(
        "SELECT id, fullname, email, role FROM users WHERE google_id = %s LIMIT 1",
        (google_id,),
    )
    if rows:
        return dict(rows[0])

    # Try to link by e-mail (user already registered with email/password)
    rows = run_query(
        "SELECT id, fullname, email, role FROM users WHERE email = %s LIMIT 1",
        (email,),
    )
    if rows:
        user = dict(rows[0])
        with db_transaction() as cur:
            cur.execute(
                "UPDATE users SET google_id = %s WHERE id = %s",
                (google_id, str(user["id"])),
            )
        return user

    # Create new user (Google-only, no password)
    import uuid
    user_id = str(uuid.uuid4())
    random_password = bcrypt.hashpw(
        secrets.token_urlsafe(32).encode(), bcrypt.gensalt(rounds=12)
    ).decode()
    kyc_default = {
        "id_document": {"file": None, "status": "pending"},
        "address_document": {"file": None, "status": "pending"},
        "selfie": {"file": None, "status": "pending"},
        "phone_verification": {"status": "pending"},
        "overall_status": "pending",
    }
    with db_transaction() as cur:
        cur.execute(
            """
            INSERT INTO users (
                id, fullname, birthdate, country, address, phone,
                email, password, role, wallets, kyc, google_id
            )
            VALUES (%s, %s, NULL, NULL, NULL, NULL, %s, %s, 'user',
                    '[]'::jsonb, %s::jsonb, %s)
            """,
            (
                user_id, name, email, random_password,
                json.dumps(kyc_default), google_id,
            ),
        )
    return {"id": user_id, "fullname": name, "email": email, "role": "user"}


@app.get("/seguridad/auth/google")
def google_auth():
    """Redirects the browser to Google's OAuth2 consent screen."""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return jsonify({"error": "Google OAuth no está configurado en el servidor"}), 503

    state = secrets.token_urlsafe(32)
    sig = _oauth_hmac(state)

    params = urlencode({
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "prompt": "select_account",
    })

    resp = make_response("", 302)
    resp.headers["Location"] = f"{GOOGLE_AUTH_URL}?{params}"
    resp.set_cookie(
        OAUTH_STATE_COOKIE,
        f"{state}.{sig}",
        httponly=True,
        secure=SECURE_COOKIE,
        samesite="Lax",
        max_age=600,
        path="/",
    )
    return resp


@app.get("/seguridad/auth/google/callback")
def google_callback():
    """Handles the Google redirect, issues a JWT session cookie."""
    login_url = f"{APP_BASE_URL}/CriptoBendicion/login"
    home_url = f"{APP_BASE_URL}/CriptoBendicion/home"

    if request.args.get("error"):
        return redirect(f"{login_url}?error=google_denied")

    code = request.args.get("code", "")
    state = request.args.get("state", "")

    # CSRF: verify state against signed cookie
    state_cookie = request.cookies.get(OAUTH_STATE_COOKIE, "")
    parts = state_cookie.rsplit(".", 1)
    if (
        len(parts) != 2
        or parts[0] != state
        or not hmac.compare_digest(_oauth_hmac(state), parts[1])
    ):
        return redirect(f"{login_url}?error=state_mismatch")

    if not code:
        return redirect(f"{login_url}?error=no_code")

    # Exchange authorization code for access token
    try:
        token_resp = google_requests.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
            timeout=10,
        )
        token_resp.raise_for_status()
        access_token = token_resp.json().get("access_token", "")
    except Exception:
        return redirect(f"{login_url}?error=token_exchange")

    if not access_token:
        return redirect(f"{login_url}?error=no_access_token")

    # Get user profile from Google
    try:
        info_resp = google_requests.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        info_resp.raise_for_status()
        info = info_resp.json()
    except Exception:
        return redirect(f"{login_url}?error=userinfo_failed")

    google_id = str(info.get("id", ""))
    email = str(info.get("email", "")).strip().lower()
    name = str(info.get("name", "")).strip() or email.split("@")[0]

    if not google_id or not email:
        return redirect(f"{login_url}?error=missing_google_data")

    # Find or create user in DB
    try:
        user = _get_or_create_google_user(google_id, email, name)
    except Exception:
        return redirect(f"{login_url}?error=db_error")

    # Issue JWT session cookie and redirect home
    user_id = str(user["id"])
    token = generar_jwt(user_id=user_id, expires_in=ACCESS_EXPIRY)

    resp = make_response("", 302)
    resp.headers["Location"] = home_url
    _make_session_cookie(resp, token)
    # Clear the short-lived OAuth state cookie
    resp.set_cookie(OAUTH_STATE_COOKIE, "", max_age=0, expires=0, path="/")
    return resp


# ─────────────────────────────────────────────────────────────────────────────
# Servidor
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5020, debug=False)
