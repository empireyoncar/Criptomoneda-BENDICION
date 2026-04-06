import json
from pathlib import Path
from hashlib import sha256

DB_PATH = Path("/app/database.json")

def load_db():
    with open(DB_PATH, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_PATH, "w") as f:
        json.dump(data, f, indent=4)

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
