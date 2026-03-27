import json
from pathlib import Path

DB_PATH = Path("/app/database.json")

def load_db():
    with open(DB_PATH, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_PATH, "w") as f:
        json.dump(data, f, indent=4)

def get_user(username):
    db = load_db()
    return db["usuarios"].get(username)

def is_admin(username):
    user = get_user(username)
    return user and user.get("role") == "admin"

def login_user(username, password):
    user = get_user(username)
    if not user:
        return None
    if user["password"] != password:
        return None
    return user
