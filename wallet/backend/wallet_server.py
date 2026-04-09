from flask import Flask, request, jsonify
from wallet_manager import create_wallet_for_user, get_user_wallet as get_user_wallet_address, get_wallet_by_address

app = Flask(__name__)


# ============================================================
# 1) Obtener wallet asociada a un usuario
# ============================================================
@app.get("/user_wallet/<user_id>")
def get_user_wallet(user_id):
    wallet = get_user_wallet_address(user_id)
    if not wallet:
        return jsonify({"wallet": None})
    return jsonify({"wallet": wallet})


# ============================================================
# 2) Obtener información completa de una wallet por address
# ============================================================
@app.get("/wallet_info/<address>")
def wallet_info(address):
    wallet = get_wallet_by_address(address)
    if wallet:
        return jsonify({
            "address": wallet["address"],
            "public_key": wallet["public_key"]
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
    try:
        wallet = create_wallet_for_user(user_id)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 409

    return jsonify({
        "address": wallet["address"],
        "public_key": wallet["public_key_hex"],
        "private_key": wallet["private_key_hex"]
    })


# ============================================================
# Servidor
# ============================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)