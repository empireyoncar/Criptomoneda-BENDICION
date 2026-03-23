from flask import Flask, request, jsonify
from wallet_manager import create_wallet_for_user, load_wallets, load_db
from wallet import generate_wallet

app = Flask(__name__)


# ============================================================
# 1) Obtener wallet asociada a un usuario
# ============================================================
@app.get("/user_wallet/<user_id>")
def get_user_wallet(user_id):
    db = load_db()

    # Buscar usuario
    for u in db["users"]:
        if str(u["id"]) == str(user_id):
            # Si no tiene wallets asociadas
            if not u.get("wallets") or len(u["wallets"]) == 0:
                return jsonify({"wallet": None})
            # Devolver la primera wallet asociada
            return jsonify({"wallet": u["wallets"][0]})

    return jsonify({"error": "Usuario no encontrado"}), 404


# ============================================================
# 2) Obtener información completa de una wallet por address
# ============================================================
@app.get("/wallet_info/<address>")
def wallet_info(address):
    wallets = load_wallets()

    for w in wallets["wallets"]:
        if w["address"] == address:
            return jsonify({
                "address": w["address"],
                "public_key": w["public_key"],
                "private_key": w["private_key"]
            })

    return jsonify({"error": "Wallet no encontrada"}), 404


# ============================================================
# 3) Crear una wallet y asignarla a un usuario
# ============================================================
@app.post("/generate_wallet")
def api_generate_wallet():
    data = request.get_json()

    if not data or "user_id" not in data:
        return jsonify({"error": "Falta user_id"}), 400

    user_id = data["user_id"]

    # Crear wallet real y guardarla
    wallet = create_wallet_for_user(user_id)

    return jsonify(wallet)


# ============================================================
# Servidor
# ============================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
