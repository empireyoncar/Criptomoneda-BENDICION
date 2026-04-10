import hashlib
import uuid

from psycopg2.extras import Json

from users_db import db_transaction, run_query


def _default_kyc_state():
    return {
        "id_document": {"file": None, "status": "pending"},
        "address_document": {"file": None, "status": "pending"},
        "selfie": {"file": None, "status": "pending"},
        "phone_verification": {"status": "pending"},
        "overall_status": "pending",
    }


def _normalize_user(user):
    return {
        "id": str(user.get("id", "")),
        "fullname": user.get("fullname", ""),
        "birthdate": user.get("birthdate"),
        "country": user.get("country"),
        "address": user.get("address"),
        "phone": user.get("phone"),
        "email": user.get("email", ""),
        "password": user.get("password", ""),
        "role": user.get("role", "user"),
        "wallets": list(user.get("wallets") or []),
        "kyc": user.get("kyc") if isinstance(user.get("kyc"), dict) else _default_kyc_state(),
    }


def _row_to_user(row):
    return _normalize_user(row)


def _upsert_user(cur, user):
    normalized = _normalize_user(user)
    cur.execute(
        """
        INSERT INTO users (
            id, fullname, birthdate, country, address, phone,
            email, password, role, wallets, kyc
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id)
        DO UPDATE SET
            fullname = EXCLUDED.fullname,
            birthdate = EXCLUDED.birthdate,
            country = EXCLUDED.country,
            address = EXCLUDED.address,
            phone = EXCLUDED.phone,
            email = EXCLUDED.email,
            password = EXCLUDED.password,
            role = EXCLUDED.role,
            wallets = EXCLUDED.wallets,
            kyc = EXCLUDED.kyc
        """,
        (
            normalized["id"],
            normalized["fullname"],
            normalized["birthdate"],
            normalized["country"],
            normalized["address"],
            normalized["phone"],
            normalized["email"],
            normalized["password"],
            normalized["role"],
            Json(normalized["wallets"]),
            Json(normalized["kyc"]),
        ),
    )


def _replace_all_users(users):
    normalized_users = [_normalize_user(user) for user in users]
    ids = [user["id"] for user in normalized_users if user.get("id")]

    with db_transaction() as cur:
        if ids:
            cur.execute("DELETE FROM users WHERE NOT (id = ANY(%s))", (ids,))
        else:
            cur.execute("DELETE FROM users")

        for user in normalized_users:
            _upsert_user(cur, user)


# -----------------------------
# CARGAR Y GUARDAR BASE DE DATOS
# -----------------------------
def save_db(data):
    _replace_all_users(data.get("users", []))


# -----------------------------
# REGISTRO NIVEL 3
# -----------------------------
def register_user(fullname, birthdate, country, address, phone, email, password):
    rows = run_query("SELECT id FROM users WHERE email = %s LIMIT 1", (email,))
    if rows:
        return None

    user_id = str(uuid.uuid4())
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    new_user = {
        "id": user_id,
        "fullname": fullname,
        "birthdate": birthdate,
        "country": country,
        "address": address,
        "phone": phone,
        "email": email,
        "password": password_hash,
        "role": "user",
        "wallets": [],

        # 🔥 NUEVA ESTRUCTURA KYC
        "kyc": {
            "id_document": {
                "file": None,
                "status": "pending"
            },
            "address_document": {
                "file": None,
                "status": "pending"
            },
            "selfie": {
                "file": None,
                "status": "pending"
            },
            "phone_verification": {
                "status": "pending"
            },
            "overall_status": "pending"
        }
    }

    with db_transaction() as cur:
        _upsert_user(cur, new_user)

    return user_id


# -----------------------------
# LOGIN
# -----------------------------
def login_user(email, password):
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    rows = run_query(
        "SELECT id FROM users WHERE email = %s AND password = %s LIMIT 1",
        (email, password_hash),
    )
    if rows:
        return rows[0]["id"]

    return None


# -----------------------------
# ASOCIAR WALLET (solo 1)
# -----------------------------
def add_wallet_to_user(user_id, address):
    user = get_user_by_id(user_id)
    if user:
        wallets = list(user.get("wallets") or [])
        if len(wallets) == 0:
            wallets.append(address)
            user["wallets"] = wallets
            with db_transaction() as cur:
                _upsert_user(cur, user)
            return True
        return False
    return False

def load_db():
    rows = run_query(
        """
        SELECT id, fullname, birthdate, country, address, phone,
               email, password, role, wallets, kyc
        FROM users
        ORDER BY created_at ASC, id ASC
        """
    )
    return {"users": [_row_to_user(row) for row in rows]}

# -----------------------------
# OBTENER USUARIO POR ID
# -----------------------------
def get_user_by_id(user_id):
    rows = run_query(
        """
        SELECT id, fullname, birthdate, country, address, phone,
               email, password, role, wallets, kyc
        FROM users
        WHERE id = %s
        LIMIT 1
        """,
        (str(user_id),),
    )
    return _row_to_user(rows[0]) if rows else None


# -----------------------------
# VERIFICAR SI USUARIO EXISTE
# -----------------------------
def user_exists(user_id):
    return get_user_by_id(user_id) is not None


# -----------------------------
# OBTENER DATOS COMPLETOS DEL USUARIO
# -----------------------------
def get_user_data(user_id):
    user = get_user_by_id(user_id)
    if not user:
        return None

    # No devolvemos password por seguridad
    safe_user = user.copy()
    safe_user.pop("password", None)
    return safe_user

# -----------------------------
# OBTENER WALLET DEL USUARIO
# -----------------------------
def get_user_wallet(user_id):
    user = get_user_by_id(user_id)
    if user and len(user.get("wallets") or []) > 0:
        return user["wallets"][0]
    return None


# -----------------------------
# GUARDAR DOCUMENTO KYC
# -----------------------------
def save_kyc_document(user_id, doc_type, filename):
    """
    doc_type debe ser uno de:
    - id_document
    - address_document
    - selfie
    """
    user = get_user_by_id(user_id)
    if user:
        if doc_type in user["kyc"]:
            user["kyc"][doc_type]["file"] = filename
            user["kyc"][doc_type]["status"] = "submitted"
            with db_transaction() as cur:
                _upsert_user(cur, user)
            return True

    return False


# -----------------------------
# VERIFICAR SI ES ADMIN
# -----------------------------
def is_admin(user_id):
    user = get_user_by_id(user_id)
    return bool(user and user.get("role") == "admin")

