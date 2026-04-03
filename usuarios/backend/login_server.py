from flask import Flask, request, jsonify
from flask_cors import CORS

# Importar funciones de la base de datos JSON
from database import (
    login_user,
    register_user 
)

app = Flask(__name__)
CORS(app)

# -----------------------------
# API LOGIN (POST)
# -----------------------------
@app.post("/login")
def login_api():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    user_id = login_user(email, password)

    if user_id:
        return jsonify({"user_id": user_id})

    return jsonify({"error": "Credenciales incorrectas"}), 401

#usuarios total

@app.get("/users/count")
def get_users_count():
    from database import load_db
    db = load_db()
    return jsonify({"count": len(db["users"])})

@app.get("/users")
def get_users():
    from database import load_db
    db = load_db()
    return jsonify(db["users"])

# -----------------------------
# API REGISTER (POST)
# -----------------------------
@app.post("/register")
def register_api():
    data = request.get_json()

    fullname = data.get("fullname")
    birthdate = data.get("birthdate")
    country = data.get("country")
    address = data.get("address")
    phone = data.get("phone")
    email = data.get("email")
    password = data.get("password")

    user_id = register_user(fullname, birthdate, country, address, phone, email, password)

    if user_id is None:
        return jsonify({"error": "El email ya está registrado"}), 400

    return jsonify({"user_id": user_id})
from database import get_user_data, get_user_by_id

#  API 1 — Obtener usuario por ID
@app.get("/user/<user_id>")
def api_get_user(user_id):
    user = get_user_data(user_id)
    if not user:
        return jsonify({"exists": False, "error": "Usuario no encontrado"}), 404
    return jsonify({"exists": True, "user": user})
from database import get_user_wallet

#API 2 — Obtener wallet del usuario

@app.get("/wallet/user/<user_id>")
def api_get_user_wallet(user_id):
    wallet = get_user_wallet(user_id)
    if not wallet:
        return jsonify({"wallet": None, "error": "El usuario no tiene wallet asociada"}), 404
    return jsonify({"wallet": wallet})

# API 3 — Verificar si el usuario existe
from database import user_exists

@app.get("/user/<user_id>/exists")
def api_user_exists(user_id):
    exists = user_exists(user_id)
    return jsonify({"exists": exists})

# -----------------------------
# INICIAR SERVIDOR LOGIN
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
