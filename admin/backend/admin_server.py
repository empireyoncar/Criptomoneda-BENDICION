from flask import Flask, request, jsonify, render_template, session, redirect
from flask_cors import CORS
from usuarios.backend.database import load_db, save_db, is_admin, login_user
from functools import wraps
import requests
import json

app = Flask(__name__, template_folder="templates_ADMIN")
app.secret_key = "clave-super-secreta-123"
CORS(app)

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
            return redirect("/login")
        return func(*args, **kwargs)
    return wrapper


# ============================================================
#   LOGIN
# ============================================================
@app.route("/login")
def login_page():
    return render_template("login.html")


@app.route("/admin_login", methods=["POST"])
def admin_login():
    email = request.form.get("email")
    password = request.form.get("password")

    user_id = login_user(email, password)

    if not user_id:
        return "Credenciales incorrectas"

    if not is_admin(user_id):
        return "No eres administrador"

    session["user_id"] = user_id
    return redirect("/admin")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ============================================================
#   PANEL ADMIN
# ============================================================
@app.route("/admin")
@require_admin
def admin_panel():
    return render_template("admin.html")


# ============================================================
#   LISTA DE USUARIOS
# ============================================================
@app.route("/CriptoBendicion/admin_api/users", methods=["GET"])
@require_admin
def admin_users():
    db = load_db()
    return jsonify(db["users"])


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
#   MINT (usa blockchain real)
# ============================================================
@app.route("/admin/mint")
@require_admin
def admin_mint_page():
    return render_template("mint.html")


@app.route("/CriptoBendicion/adminbackend/mint/create", methods=["POST"])
@require_admin
def admin_mint_create():
    data = request.json
    address = data.get("address")
    amount = data.get("amount")

    res = requests.post(f"{BC_API}/mint", json={
        "address": address,
        "amount": amount
    })

    return jsonify(res.json())


@app.route("/CriptoBendicion/adminbackend/mint/commit", methods=["POST"])
@require_admin
def admin_mint_commit():
    res = requests.post(f"{BC_API}/commit")
    return jsonify(res.json())


# ============================================================
#   INICIAR SERVIDOR
# ============================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5010, debug=True)
