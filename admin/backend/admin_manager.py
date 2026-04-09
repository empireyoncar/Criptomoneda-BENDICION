import json
import os
from hashlib import sha256

import psycopg2
from psycopg2.extras import RealDictCursor

DB_PATH = "/app/database.json"


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
    }


def _migrate_legacy_users_if_needed():
    if not os.path.exists(DB_PATH):
        return

    with _get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS total FROM users")
            total = cur.fetchone()["total"]
            if total > 0:
                return

            with open(DB_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)

            for user in data.get("users", []):
                cur.execute(
                    """
                    INSERT INTO users (
                        id, fullname, birthdate, country, address, phone,
                        email, password, role, wallets, kyc
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (
                        str(user.get("id", "")),
                        user.get("fullname", ""),
                        user.get("birthdate"),
                        user.get("country"),
                        user.get("address"),
                        user.get("phone"),
                        user.get("email", ""),
                        user.get("password", ""),
                        user.get("role", "user"),
                        json.dumps(user.get("wallets") or []),
                        json.dumps(user.get("kyc") or _default_kyc_state()),
                    ),
                )
        conn.commit()

def load_db():
    _migrate_legacy_users_if_needed()
    with _get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, fullname, birthdate, country, address, phone,
                       email, password, role, wallets, kyc
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


def is_admin(user_identifier):
    user = get_user_by_id(user_identifier)
    if not user:
        user = get_user(user_identifier)
    return user and user.get("role") == "admin"


def login_user(email, password):
    user = get_user(email)
    if not user:
        return None

    # La contraseña en tu JSON está hasheada con SHA256
    hashed = sha256(password.encode()).hexdigest()

    if user["password"] != hashed:
        return None

    return user.get("id")
