from flask import Flask, request, jsonify, session, redirect
from flask_cors import CORS
from admin_manager import (
    get_safe_user_by_id,
    is_admin,
    load_db,
    login_user,
    save_db,
    update_user_info,
    update_user_password,
)
from functools import wraps
import requests
import json

app = Flask(__name__)
app.secret_key = "clave-super-secreta-123"
CORS(app, supports_credentials=True)

# URL de la blockchain real
BC_API = "https://empireyoncar.duckdns.org/CriptoBendicion/blockchain"

# ============================================================
#   DECORADOR PARA VERIFICAR ADMIN
# ============================================================
def require_admin(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user_id = session.get("user_id")
        if not is_admin(user_id):
            return redirect("/CriptoBendicion/admin/login")
        return func(*args, **kwargs)
    return wrapper

# ============================================================
#   LISTA DE USUARIOS
# ============================================================
@app.route("/CriptoBendicion/admin_api/users", methods=["GET"])
@require_admin
def admin_users():
    db = load_db()
    return jsonify(db["users"])


@app.route("/CriptoBendicion/admin_api/users/<user_id>", methods=["GET"])
@require_admin
def admin_user_by_id(user_id):
    user = get_safe_user_by_id(user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    return jsonify(user)


@app.route("/CriptoBendicion/admin_api/users/<user_id>/password", methods=["PUT"])
@require_admin
def admin_user_password(user_id):
    payload = request.get_json(silent=True) or {}
    new_password = str(payload.get("password", ""))

    try:
        updated = update_user_password(user_id, new_password)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    if not updated:
        return jsonify({"error": "Usuario no encontrado"}), 404
    return jsonify({"ok": True, "message": "Contraseña actualizada"})


@app.route("/CriptoBendicion/admin_api/users/<user_id>/info", methods=["PUT"])
@require_admin
def admin_user_info(user_id):
    payload = request.get_json(silent=True) or {}

    try:
        user = update_user_info(user_id, payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    return jsonify({"ok": True, "user": user})

# ============================================================
#   BLOQUES (desde blockchain real)
# ============================================================
@app.route("/CriptoBendicion/admin_api/blocks", methods=["GET"])
@require_admin
def admin_blocks():
    res = requests.get(f"{BC_API}/chain")
    return jsonify(res.json())

# ============================================================
#   TRANSACCIONES (desde blockchain real)
# ============================================================
@app.route("/CriptoBendicion/admin_api/transactions", methods=["GET"])
@require_admin
def admin_transactions():
    chain = requests.get(f"{BC_API}/chain").json()
    txs = [tx for block in chain for tx in block["transactions"]]
    return jsonify(txs)

# ============================================================
#   TRANSACCIONES POR WALLET
# ============================================================
@app.route("/CriptoBendicion/admin_api/transactions/<address>", methods=["GET"])
@require_admin
def admin_transactions_by_address(address):
    res = requests.get(f"{BC_API}/wallet/{address}/history")
    return jsonify(res.json())

# ============================================================
#   INICIAR SERVIDOR
# ============================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5010, debug=True)
