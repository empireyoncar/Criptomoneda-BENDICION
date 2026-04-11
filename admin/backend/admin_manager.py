import os
from hashlib import sha256

import bcrypt
import psycopg2
from psycopg2.extras import RealDictCursor


MIN_PASSWORD_LENGTH = 20
ALLOWED_ROLES = {"user", "admin"}

def _default_kyc_state():
    return {
        "id_document": {"file": None, "status": "pending"},
        "address_document": {"file": None, "status": "pending"},
        "selfie": {"file": None, "status": "pending"},
        "phone_verification": {"status": "pending"},
        "overall_status": "pending",
    }


def _db_config(name, default):
    return os.getenv(name, default)


def _get_connection():
    return psycopg2.connect(
        host=_db_config("USERS_DB_HOST", "localhost"),
        port=int(_db_config("USERS_DB_PORT", "5546")),
        dbname=_db_config("USERS_DB_NAME", "users_db"),
        user=_db_config("USERS_DB_USER", "users_user"),
        password=_db_config("USERS_DB_PASSWORD", "users_password"),
        cursor_factory=RealDictCursor,
    )


def _row_to_user(row):
    return {
        "id": str(row.get("id", "")),
        "fullname": row.get("fullname", ""),
        "birthdate": row.get("birthdate"),
        "country": row.get("country"),
        "address": row.get("address"),
        "phone": row.get("phone"),
        "email": row.get("email", ""),
        "password": row.get("password", ""),
        "role": row.get("role", "user"),
        "wallets": list(row.get("wallets") or []),
        "kyc": row.get("kyc") if isinstance(row.get("kyc"), dict) else _default_kyc_state(),
        "twofa_enabled": bool(row.get("twofa_enabled")),
        "ssh_public_key": bool(row.get("ssh_public_key")),
    }


def load_db():
    with _get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, fullname, birthdate, country, address, phone,
                       email, password, role, wallets, kyc,
                       twofa_enabled, ssh_public_key
                FROM users
                ORDER BY created_at ASC, id ASC
                """
            )
            return {"users": [_row_to_user(dict(row)) for row in cur.fetchall()]}

def save_db(data):
    raise NotImplementedError("admin_manager.save_db no se usa tras la migracion a PostgreSQL")

def get_user(email):
    db = load_db()
    for user in db.get("users", []):
        if user.get("email") == email:
            return user
    return None


def get_user_by_id(user_id):
    db = load_db()
    for user in db.get("users", []):
        if user.get("id") == user_id:
            return user
    return None


def get_safe_user_by_id(user_id):
    user = get_user_by_id(user_id)
    if not user:
        return None
    safe_user = dict(user)
    safe_user.pop("password", None)
    return safe_user


def is_admin(user_identifier):
    user = get_user_by_id(user_identifier)
    if not user:
        user = get_user(user_identifier)
    return user and user.get("role") == "admin"


def login_user(email, password):
    user = get_user(email)
    if not user:
        return None

    stored_hash = str(user.get("password") or "")
    if not _verify_password(password, stored_hash):
        return None

    return user.get("id")


def _verify_password(password, stored_hash):
    if stored_hash.startswith("$2a$") or stored_hash.startswith("$2b$") or stored_hash.startswith("$2y$"):
        try:
            return bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
        except Exception:
            return False
    return sha256(password.encode()).hexdigest() == stored_hash


def _hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def update_user_password(user_id, new_password):
    if not isinstance(new_password, str) or len(new_password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"La contraseña debe tener al menos {MIN_PASSWORD_LENGTH} caracteres")

    with _get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET password = %s WHERE id = %s",
                (_hash_password(new_password), str(user_id)),
            )
            updated = cur.rowcount
        conn.commit()
    return updated > 0


def update_user_info(user_id, payload):
    current = get_user_by_id(user_id)
    if not current:
        return None

    merged = {
        "fullname": str(payload.get("fullname", current.get("fullname") or "")).strip(),
        "birthdate": str(payload.get("birthdate", current.get("birthdate") or "")).strip(),
        "country": str(payload.get("country", current.get("country") or "")).strip(),
        "address": str(payload.get("address", current.get("address") or "")).strip(),
        "phone": str(payload.get("phone", current.get("phone") or "")).strip(),
        "email": str(payload.get("email", current.get("email") or "")).strip().lower(),
        "role": str(payload.get("role", current.get("role") or "user")).strip().lower(),
    }

    if not merged["fullname"] or not merged["birthdate"] or not merged["country"] or not merged["address"] or not merged["email"]:
        raise ValueError("fullname, birthdate, country, address y email son obligatorios")

    if merged["role"] not in ALLOWED_ROLES:
        raise ValueError("Rol inválido")

    try:
        with _get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE users
                    SET fullname = %s,
                        birthdate = %s,
                        country = %s,
                        address = %s,
                        phone = %s,
                        email = %s,
                        role = %s
                    WHERE id = %s
                    """,
                    (
                        merged["fullname"],
                        merged["birthdate"],
                        merged["country"],
                        merged["address"],
                        merged["phone"] or None,
                        merged["email"],
                        merged["role"],
                        str(user_id),
                    ),
                )
                updated = cur.rowcount
            conn.commit()
    except psycopg2.IntegrityError as exc:
        raise ValueError("El email ya está registrado") from exc

    if not updated:
        return None
    return get_safe_user_by_id(user_id)


def reset_user_security(user_id: str, reset_2fa: bool = False, reset_ssh: bool = False, reset_kyc: bool = False) -> None:
    """Reset 2FA, SSH key, and/or KYC for a user so they can reconfigure."""
    import json

    if not any([reset_2fa, reset_ssh, reset_kyc]):
        raise ValueError("Debes indicar qué resetear")

    with _get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE id = %s LIMIT 1", (str(user_id),))
            if not cur.fetchone():
                raise ValueError("Usuario no encontrado")

            if reset_2fa:
                cur.execute(
                    "UPDATE users SET twofa_enabled = FALSE, twofa_secret = NULL WHERE id = %s",
                    (str(user_id),),
                )
            if reset_ssh:
                cur.execute("UPDATE users SET ssh_public_key = NULL WHERE id = %s", (str(user_id),))
                cur.execute("DELETE FROM device_tokens WHERE user_id = %s", (str(user_id),))
            if reset_kyc:
                kyc_default = _default_kyc_state()
                cur.execute(
                    "UPDATE users SET kyc = %s::jsonb WHERE id = %s",
                    (json.dumps(kyc_default), str(user_id)),
                )
        conn.commit()
