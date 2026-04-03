from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# URLs internas de Docker (o tus hosts reales)
LOGIN_SERVER = "http://login_server:5001"
BLOCKCHAIN_SERVER = "http://blockchain_api:5004"


@app.post("/staking/validate")
def validate_staking():
    data = request.get_json()

    user_id = data.get("user_id")
    wallet_address = data.get("wallet_address")
    amount = float(data.get("amount", 0))

    # ---------------------------------------------------
    # 1. VALIDAR USUARIO (login_server)
    # ---------------------------------------------------
    try:
        user_res = requests.get(f"{LOGIN_SERVER}/user/{user_id}")
    except:
        return jsonify({"error": "No se pudo conectar con login_server"}), 500

    if user_res.status_code != 200:
        return jsonify({"error": "Usuario no existe"}), 400

    user_data = user_res.json().get("user")

    # ---------------------------------------------------
    # 2. VALIDAR WALLET (login_server)
    # ---------------------------------------------------
    try:
        wallet_res = requests.get(f"{LOGIN_SERVER}/wallet/user/{user_id}")
    except:
        return jsonify({"error": "No se pudo conectar con login_server (wallet)"}), 500

    if wallet_res.status_code != 200:
        return jsonify({"error": "El usuario no tiene wallet asociada"}), 400

    real_wallet = wallet_res.json().get("wallet")

    if real_wallet != wallet_address:
        return jsonify({"error": "La wallet no pertenece al usuario"}), 400

    # ---------------------------------------------------
    # 3. VALIDAR SALDO REAL (blockchain_server)
    # ---------------------------------------------------
    try:
        bc_res = requests.get(f"{BLOCKCHAIN_SERVER}/wallet/{wallet_address}")
    except:
        return jsonify({"error": "No se pudo conectar con blockchain_server"}), 500

    if bc_res.status_code != 200:
        return jsonify({"error": "No se pudo obtener saldo de la blockchain"}), 400

    bc_data = bc_res.json()
    balance = float(bc_data.get("balance", 0))
    locked = float(bc_data.get("locked", 0))
    available = balance - locked

    if available < amount:
        return jsonify({
            "error": "Saldo insuficiente",
            "balance": balance,
            "locked": locked,
            "available": available
        }), 400

    # ---------------------------------------------------
    # VALIDACIÓN COMPLETA
    # ---------------------------------------------------
    return jsonify({
        "status": "validated",
        "message": "Validación correcta. Procediendo a crear staking.",
        "available_balance": available
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5010, debug=True)
