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

# -----------------------------
# INICIAR SERVIDOR LOGIN
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
