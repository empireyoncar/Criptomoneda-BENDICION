import json
import os
import hashlib
import uuid

DB_FILE = os.path.join("/app/db", "database.json")

# Crear archivo si no existe
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f:
        json.dump({"users": []}, f)


def load_db():
    with open(DB_FILE, "r") as f:
        return json.load()


def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)


# -----------------------------
# REGISTRO NIVEL 3
# -----------------------------
def register_user(fullname, birthdate, country, address, phone, email, password):
    db = load_db()

    # Verificar si ya existe el email
    for u in db["users"]:
        if u["email"] == email:
            return None

    user_id = str(uuid.uuid4())
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    # Crear wallet automáticamente
    wallet_id = hashlib.sha256((user_id + email).encode()).hexdigest()

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

    db["users"].append(new_user)
    save_db(db)

    return user_id


# -----------------------------
# LOGIN
# -----------------------------
def login_user(email, password):
    db = load_db()
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    for u in db["users"]:
        if u["email"] == email and u["password"] == password_hash:
            return u["id"]

    return None


# -----------------------------
# ASOCIAR WALLET (solo 1)
# -----------------------------
def add_wallet_to_user(user_id, address):
    db = load_db()

    for u in db["users"]:
        if u["id"] == user_id:
            if len(u["wallets"]) == 0:
                u["wallets"].append(address)
                save_db(db)
                return True
            else:
                return False  # ya tiene una wallet

    return False

def load_db():
    print("USANDO DATABASE.PY DESDE:", os.path.abspath(__file__))
    with open(DB_FILE, "r") as f:
        return json.load(f)


# -----------------------------
# OBTENER WALLET DEL USUARIO
# -----------------------------
def get_user_wallet(user_id):
    db = load_db()
    for u in db["users"]:
        if u["id"] == user_id:
            if len(u["wallets"]) > 0:
                return u["wallets"][0]
            return None
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
    db = load_db()

    for u in db["users"]:
        if u["id"] == user_id:
            if doc_type in u["kyc"]:
                u["kyc"][doc_type]["file"] = filename
                u["kyc"][doc_type]["status"] = "submitted"
                save_db(db)
                return True

    return False


# -----------------------------
# VERIFICAR SI ES ADMIN
# -----------------------------
def is_admin(user_id):
    db = load_db()
    for u in db["users"]:
        if u["id"] == user_id and u.get("role") == "admin":
            return True
    return False
