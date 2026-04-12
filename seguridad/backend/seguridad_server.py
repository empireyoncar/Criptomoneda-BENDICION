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
import uuid
from pathlib import Path
from urllib.parse import urlencode

import bcrypt
import pyotp
import requests as google_requests
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from flask import Flask, jsonify, make_response, redirect, request
from flask_cors import CORS

# ── Importar módulo de cryptografía ──────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR / "criptografia"))
sys.path.insert(0, "/app/criptografia")
from tokens import generar_jwt, renovar_jwt, revocar_jwt, verificar_jwt  # noqa: E402

# ── Importar helpers de base de datos de usuarios ────────────────────────────
sys.path.insert(0, str(ROOT_DIR / "usuarios" / "backend"))
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
DEVICE_COOKIE = "device_token"
DEVICE_TOKEN_MAX_AGE = 365 * 86400  # 1 año

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
        "SELECT id, fullname, email, role, password, twofa_enabled, twofa_secret FROM users "
        "WHERE email = %s LIMIT 1",
        (email,),
    )
    return dict(rows[0]) if rows else None


def _lookup_user_by_id(user_id: str) -> dict | None:
    rows = run_query(
        "SELECT id, fullname, email, role, twofa_enabled, twofa_secret "
        "FROM users WHERE id = %s LIMIT 1",
        (user_id,),
    )
    return dict(rows[0]) if rows else None


def _verify_totp(secret: str, code: str) -> bool:
    if not secret or not code:
        return False
    # 6-8 dígitos habituales; permite ventana de +-1 paso para tolerar desfase horario.
    if not code.isdigit() or len(code) < 6 or len(code) > 8:
        return False
    try:
        return bool(pyotp.TOTP(secret).verify(code, valid_window=1))
    except Exception:
        return False


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
    Body JSON: { "email": str, "password": str, "otp": str opcional }
    """
    body = request.get_json(silent=True) or {}
    email = str(body.get("email", "")).strip().lower()
    password = str(body.get("password", ""))
    otp = str(body.get("otp", "")).strip()
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

    # Si el usuario tiene 2FA activo, exigir código TOTP antes de emitir sesión.
    if bool(user.get("twofa_enabled")):
        if not otp:
            return jsonify({"error": "Código 2FA requerido", "requires_2fa": True}), 401
        if not _verify_totp(str(user.get("twofa_secret") or ""), otp):
            _register_login_failure(key)
            time.sleep(0.3)
            return jsonify({"error": "Código 2FA inválido", "requires_2fa": True}), 401

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
        "SELECT id, fullname, email, role, twofa_enabled, ssh_public_key, "
        "google_id, birthdate, country, phone, kyc "
        "FROM users WHERE id = %s LIMIT 1",
        (user_id,),
    )
    if not rows:
        return jsonify({"error": "Usuario no encontrado"}), 404

    user = dict(rows[0])

    twofa_enabled = bool(user.get("twofa_enabled"))
    ssh_configured = bool(user.get("ssh_public_key"))
    device_trusted = _is_device_trusted(user_id)

    # KYC approval
    kyc = user.get("kyc") or {}
    if isinstance(kyc, str):
        try:
            kyc = json.loads(kyc)
        except Exception:
            kyc = {}
    kyc_approved = kyc.get("overall_status") == "approved"

    # Account is fully activated when 2FA + SSH + KYC are all done
    is_activated = twofa_enabled and ssh_configured and kyc_approved

    # Google users who haven't completed their profile
    is_google_user = bool(user.get("google_id"))
    needs_profile = is_google_user and not all([
        user.get("birthdate"), user.get("country"), user.get("phone")
    ])

    resp_data = {
        "user_id": str(user["id"]),
        "fullname": user.get("fullname", ""),
        "email": user.get("email", ""),
        "role": user.get("role", "user"),
        "twofa_enabled": twofa_enabled,
        "ssh_configured": ssh_configured,
        "device_trusted": device_trusted,
        "kyc_approved": kyc_approved,
        "is_activated": is_activated,
        "needs_profile": needs_profile,
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


def _ensure_2fa_columns() -> None:
    """Runtime migration: add 2FA columns if they don't exist yet."""
    try:
        with db_transaction() as cur:
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS twofa_secret TEXT")
            cur.execute(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS twofa_enabled "
                "BOOLEAN NOT NULL DEFAULT FALSE"
            )
    except Exception:
        pass


_ensure_google_id_column()
_ensure_2fa_columns()


# ─────────────────────────────────────────────────────────────────────────────
# SSH Key – helpers y migración
# ─────────────────────────────────────────────────────────────────────────────

def _ensure_ssh_tables() -> None:
    """Runtime migration: add ssh_public_key column and device_tokens table."""
    try:
        with db_transaction() as cur:
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS ssh_public_key TEXT")
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS device_tokens (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    token VARCHAR(255) NOT NULL UNIQUE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    expires_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '365 days')
                )
                """
            )
    except Exception:
        pass


_ensure_ssh_tables()


def _make_device_cookie(response, token: str) -> None:
    response.set_cookie(
        DEVICE_COOKIE,
        token,
        httponly=True,
        secure=SECURE_COOKIE,
        samesite="Lax",
        max_age=DEVICE_TOKEN_MAX_AGE,
        path="/",
    )


def _is_device_trusted(user_id: str) -> bool:
    token = request.cookies.get(DEVICE_COOKIE, "")
    if not token:
        return False
    rows = run_query(
        "SELECT id FROM device_tokens WHERE user_id = %s AND token = %s "
        "AND expires_at > NOW() LIMIT 1",
        (user_id, token),
    )
    return bool(rows)


def _extract_public_key_pem(private_key_pem: bytes) -> str | None:
    """Extract the PEM public key from a PEM private key. Returns None on error."""
    try:
        private_key = serialization.load_pem_private_key(
            private_key_pem, password=None, backend=default_backend()
        )
        return private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# SSH Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/seguridad/ssh/status")
def ssh_status():
    payload, err = _require_auth()
    if err:
        return err
    user_id = str(payload.get("sub", ""))
    rows = run_query(
        "SELECT ssh_public_key FROM users WHERE id = %s LIMIT 1", (user_id,)
    )
    if not rows:
        return jsonify({"error": "Usuario no encontrado"}), 404
    configured = bool(rows[0]["ssh_public_key"])
    trusted = _is_device_trusted(user_id)
    return jsonify({"configured": configured, "device_trusted": trusted}), 200


@app.post("/seguridad/ssh/generate")
def ssh_generate():
    """Generate a new RSA 2048 key pair. Stores public key in DB, returns private key once."""
    payload, err = _require_auth()
    if err:
        return err
    user_id = str(payload.get("sub", ""))
    rows = run_query("SELECT id FROM users WHERE id = %s LIMIT 1", (user_id,))
    if not rows:
        return jsonify({"error": "Usuario no encontrado"}), 404

    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()

    # Store public key, invalidate all existing device tokens for security
    with db_transaction() as cur:
        cur.execute("UPDATE users SET ssh_public_key = %s WHERE id = %s", (public_pem, user_id))
        cur.execute("DELETE FROM device_tokens WHERE user_id = %s", (user_id,))

    return jsonify({"private_key": private_pem}), 200


@app.post("/seguridad/ssh/verify")
def ssh_verify():
    """
    Verify uploaded private key against stored public key.
    On success, issues a long-lived device_token cookie for this device.
    Accepts: multipart file field 'private_key'  OR  JSON {'private_key': '<PEM>'}
    """
    payload, err = _require_auth()
    if err:
        return err
    user_id = str(payload.get("sub", ""))

    # Accept from multipart or JSON
    if request.files.get("private_key"):
        private_key_pem = request.files["private_key"].read(64 * 1024)  # max 64 KB
    elif request.is_json:
        body = request.get_json(silent=True) or {}
        raw = str(body.get("private_key", ""))
        private_key_pem = raw.encode()
    else:
        return jsonify({"error": "Clave privada requerida"}), 400

    if not private_key_pem:
        return jsonify({"error": "Clave privada vacía"}), 400

    rows = run_query(
        "SELECT ssh_public_key FROM users WHERE id = %s LIMIT 1", (user_id,)
    )
    if not rows:
        return jsonify({"error": "Usuario no encontrado"}), 404

    stored_public_pem = str(rows[0]["ssh_public_key"] or "").strip()
    if not stored_public_pem:
        return jsonify({"error": "No tienes clave SSH configurada"}), 400

    derived_public_pem = _extract_public_key_pem(private_key_pem)
    if not derived_public_pem:
        return jsonify({"error": "Clave privada inválida o no se pudo leer"}), 400

    if derived_public_pem.strip() != stored_public_pem:
        return jsonify({"error": "La clave privada no corresponde a tu clave registrada"}), 401

    # Grant device trust
    device_token = secrets.token_urlsafe(48)
    with db_transaction() as cur:
        cur.execute(
            "INSERT INTO device_tokens (user_id, token) VALUES (%s, %s)",
            (user_id, device_token),
        )

    resp = make_response(jsonify({"verified": True}))
    _make_device_cookie(resp, device_token)
    return resp, 200


# ─────────────────────────────────────────────────────────────────────────────
# Admin – reset user security features
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/seguridad/admin/reset-security/<user_id>")
def admin_reset_security(user_id: str):
    """
    Admin-only: reset 2FA, SSH, and/or KYC for a user so they can reconfigure.
    Requires the calling session to belong to a user with role='admin'.
    """
    payload, err = _require_auth()
    if err:
        return err

    caller_id = str(payload.get("sub", ""))
    caller_rows = run_query("SELECT role FROM users WHERE id = %s LIMIT 1", (caller_id,))
    if not caller_rows or str(caller_rows[0]["role"]) != "admin":
        return jsonify({"error": "Acceso denegado"}), 403

    body = request.get_json(silent=True) or {}
    reset_2fa = bool(body.get("reset_2fa"))
    reset_ssh = bool(body.get("reset_ssh"))
    reset_kyc = bool(body.get("reset_kyc"))

    if not any([reset_2fa, reset_ssh, reset_kyc]):
        return jsonify({"error": "Debes indicar qué resetear"}), 400

    target_rows = run_query("SELECT id FROM users WHERE id = %s LIMIT 1", (user_id,))
    if not target_rows:
        return jsonify({"error": "Usuario no encontrado"}), 404

    with db_transaction() as cur:
        if reset_2fa:
            cur.execute(
                "UPDATE users SET twofa_enabled = FALSE, twofa_secret = NULL WHERE id = %s",
                (user_id,),
            )
        if reset_ssh:
            cur.execute("UPDATE users SET ssh_public_key = NULL WHERE id = %s", (user_id,))
            cur.execute("DELETE FROM device_tokens WHERE user_id = %s", (user_id,))
        if reset_kyc:
            kyc_default = json.dumps({
                "id_document": {"file": None, "status": "pending"},
                "address_document": {"file": None, "status": "pending"},
                "selfie": {"file": None, "status": "pending"},
                "phone_verification": {"status": "pending"},
                "overall_status": "pending",
            })
            cur.execute(
                "UPDATE users SET kyc = %s::jsonb WHERE id = %s",
                (kyc_default, user_id),
            )

    return jsonify({"ok": True, "reset_2fa": reset_2fa, "reset_ssh": reset_ssh, "reset_kyc": reset_kyc}), 200
def twofa_status():
    payload, err = _require_auth()
    if err:
        return err

    user_id = str(payload.get("sub", ""))
    user = _lookup_user_by_id(user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    enabled = bool(user.get("twofa_enabled"))
    has_secret = bool(user.get("twofa_secret"))
    return jsonify({
        "enabled": enabled,
        "has_secret": has_secret,
    }), 200


@app.post("/seguridad/2fa/setup")
def twofa_setup():
    payload, err = _require_auth()
    if err:
        return err

    user_id = str(payload.get("sub", ""))
    user = _lookup_user_by_id(user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    if bool(user.get("twofa_enabled")):
        return jsonify({"error": "2FA ya está activado"}), 400

    secret = pyotp.random_base32()
    issuer = os.getenv("APP_ISSUER", "CriptoBendicion")
    account_name = str(user.get("email") or f"user-{user_id}")
    otpauth_url = pyotp.TOTP(secret).provisioning_uri(
        name=account_name,
        issuer_name=issuer,
    )

    with db_transaction() as cur:
        cur.execute(
            "UPDATE users SET twofa_secret = %s, twofa_enabled = FALSE WHERE id = %s",
            (secret, user_id),
        )

    return jsonify({
        "secret": secret,
        "otpauth_url": otpauth_url,
        "issuer": issuer,
        "account": account_name,
    }), 200


@app.post("/seguridad/2fa/enable")
def twofa_enable():
    payload, err = _require_auth()
    if err:
        return err

    body = request.get_json(silent=True) or {}
    code = str(body.get("code", "")).strip()

    user_id = str(payload.get("sub", ""))
    user = _lookup_user_by_id(user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    secret = str(user.get("twofa_secret") or "")
    if not secret:
        return jsonify({"error": "Primero debes generar la configuración 2FA"}), 400

    if not _verify_totp(secret, code):
        return jsonify({"error": "Código inválido"}), 400

    with db_transaction() as cur:
        cur.execute("UPDATE users SET twofa_enabled = TRUE WHERE id = %s", (user_id,))

    return jsonify({"enabled": True}), 200


@app.post("/seguridad/2fa/disable")
def twofa_disable():
    payload, err = _require_auth()
    if err:
        return err

    body = request.get_json(silent=True) or {}
    code = str(body.get("code", "")).strip()

    user_id = str(payload.get("sub", ""))
    user = _lookup_user_by_id(user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    if not bool(user.get("twofa_enabled")):
        return jsonify({"error": "2FA no está activado"}), 400

    secret = str(user.get("twofa_secret") or "")
    if not _verify_totp(secret, code):
        return jsonify({"error": "Código inválido"}), 400

    with db_transaction() as cur:
        cur.execute(
            "UPDATE users SET twofa_enabled = FALSE, twofa_secret = NULL WHERE id = %s",
            (user_id,),
        )

    return jsonify({"enabled": False}), 200


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
