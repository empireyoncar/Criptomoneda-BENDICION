import json
import time
import logging

import psycopg2
from psycopg2.extras import RealDictCursor

from wallet import generate_wallet
from wallet_db import ensure_schema, run_execute, run_query

logger = logging.getLogger(__name__)

ensure_schema()


def _users_db_config(name, default):
    return os.getenv(name, default)


def _get_users_connection():
    for attempt in range(1, 11):
        try:
            return psycopg2.connect(
                host=_users_db_config("USERS_DB_HOST", "localhost"),
                port=int(_users_db_config("USERS_DB_PORT", "5546")),
                dbname=_users_db_config("USERS_DB_NAME", "users_db"),
                user=_users_db_config("USERS_DB_USER", "users_user"),
                password=_users_db_config("USERS_DB_PASSWORD", "users_password"),
                cursor_factory=RealDictCursor,
            )
        except Exception as exc:
            logger.warning("users_db connection attempt %d/10 failed: %s", attempt, exc)
            if attempt == 10:
                raise
            time.sleep(3)


def load_wallets():
    rows = run_query(
        """
        SELECT user_id, public_key, address, created_at
        FROM wallets
        ORDER BY created_at ASC
        """
    )
    return {"wallets": rows}

def load_db():
    with _get_users_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, wallets FROM users ORDER BY created_at ASC, id ASC")
            users = []
            for row in cur.fetchall():
                users.append({
                    "id": str(row["id"]),
                    "wallets": list(row.get("wallets") or []),
                })
            return {"users": users}

def save_db(data):
    with _get_users_connection() as conn:
        with conn.cursor() as cur:
            for user in data.get("users", []):
                cur.execute(
                    "UPDATE users SET wallets = %s::jsonb WHERE id = %s",
                    (json.dumps(user.get("wallets") or []), str(user.get("id"))),
                )
        conn.commit()


def get_wallet_by_user_id(user_id):
    rows = run_query(
        """
        SELECT user_id, address, public_key, created_at
        FROM wallets
        WHERE user_id = %s
        LIMIT 1
        """,
        (str(user_id),),
    )
    return rows[0] if rows else None


def get_user_wallet(user_id):
    with _get_users_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT wallets FROM users WHERE id = %s LIMIT 1", (str(user_id),))
            row = cur.fetchone()
            if not row:
                return None
            wallets = list(row.get("wallets") or [])
            return wallets[0] if wallets else None


def get_wallet_by_address(address):
    rows = run_query(
        """
        SELECT user_id, address, public_key, created_at
        FROM wallets
        WHERE address = %s
        LIMIT 1
        """,
        (address,),
    )
    return rows[0] if rows else None

def create_wallet_for_user(user_id):
    existing_wallet = get_wallet_by_user_id(user_id)
    if existing_wallet:
        raise ValueError("El usuario ya tiene una wallet asociada")

    db = load_db()
    user_found = any(str(u.get("id")) == str(user_id) for u in db["users"])
    if not user_found:
        raise ValueError("Usuario no encontrado")

    # Generar wallet real
    wallet = generate_wallet()

    run_execute(
        """
        INSERT INTO wallets (user_id, address, public_key)
        VALUES (%s, %s, %s)
        """,
        (str(user_id), wallet["address"], wallet["public_key_hex"]),
    )

    # Guardar address en users_db
    db = load_db()
    for u in db["users"]:
        if str(u["id"]) == str(user_id):
            wallets = u.setdefault("wallets", [])
            if wallet["address"] not in wallets:
                wallets.append(wallet["address"])
            break
    save_db(db)

    return wallet
