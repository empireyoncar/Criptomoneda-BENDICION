import json
import os
import time
import logging

import psycopg2
from psycopg2.extras import RealDictCursor

from wallet import generate_wallet
from wallet_db import ensure_schema, run_execute, run_query

logger = logging.getLogger(__name__)

LEGACY_USERS_FILE = os.path.join("/app/database.json")
LEGACY_WALLETS_FILE = os.path.join("/app/wallets.json")

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


def _migrate_legacy_users_if_needed():
    if not os.path.exists(LEGACY_USERS_FILE):
        return

    with _get_users_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS total FROM users")
            total = cur.fetchone()["total"]
            if total > 0:
                return

            with open(LEGACY_USERS_FILE, "r", encoding="utf-8") as f:
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
                        json.dumps(user.get("kyc") or {}),
                    ),
                )
        conn.commit()

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
    _migrate_legacy_users_if_needed()
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
    _migrate_legacy_users_if_needed()
    with _get_users_connection() as conn:
        with conn.cursor() as cur:
            for user in data.get("users", []):
                cur.execute(
                    "UPDATE users SET wallets = %s::jsonb WHERE id = %s",
                    (json.dumps(user.get("wallets") or []), str(user.get("id"))),
                )
        conn.commit()


def _read_legacy_wallets():
    if not os.path.exists(LEGACY_WALLETS_FILE):
        return []

    with open(LEGACY_WALLETS_FILE, "r") as f:
        data = json.load(f)

    return data.get("wallets", [])


def migrate_legacy_wallets() -> None:
    rows = run_query("SELECT COUNT(*) AS total FROM wallets")
    if rows and rows[0]["total"] > 0:
        return

    for wallet in _read_legacy_wallets():
        public_key = wallet.get("public_key") or wallet.get("public_key_hex")
        address = wallet.get("address")
        user_id = wallet.get("user_id")

        if not user_id or not address or not public_key:
            continue

        run_execute(
            """
            INSERT INTO wallets (user_id, address, public_key)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id)
            DO UPDATE SET address = EXCLUDED.address, public_key = EXCLUDED.public_key
            """,
            (str(user_id), address, public_key),
        )


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
    _migrate_legacy_users_if_needed()
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
    _migrate_legacy_users_if_needed()
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


try:
    migrate_legacy_wallets()
except Exception as exc:
    logger.warning("migrate_legacy_wallets at startup failed (non-fatal): %s", exc)
