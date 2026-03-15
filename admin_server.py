from flask import Flask, request, jsonify, render_template, session, redirect
from flask_cors import CORS
from database import load_db, save_db, is_admin, login_user
from node import blockchain
from functools import wraps

app = Flask(__name__, template_folder="templates_ADMIN")
app.secret_key = "clave-super-secreta-123"   # Necesario para sesiones
CORS(app)

# -----------------------------
# DECORADOR PARA VERIFICAR ADMIN
# -----------------------------
def require_admin(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user_id = session.get("user_id")

        if not is_admin(user_id):
            return redirect("/login")

        return func(*args, **kwargs)
    return wrapper


# -----------------------------
# LOGIN VISUAL
# -----------------------------
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

    # Guardar sesión
    session["user_id"] = user_id

    # Redirigir al panel admin
    return redirect("/admin")


# -----------------------------
# LOGOUT
# -----------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# -----------------------------
# PANEL ADMIN
# -----------------------------
@app.route("/admin")
@require_admin
def admin_panel():
    return render_template("admin.html")


# -----------------------------
# LISTA DE USUARIOS
# -----------------------------
@app.route("/admin/users", methods=["GET"])
@require_admin
def admin_users():
    db = load_db()
    return jsonify(db["users"])


# -----------------------------
# TRANSACCIONES
# -----------------------------
@app.route("/admin/transactions", methods=["GET"])
@require_admin
def admin_transactions():
    txs = []
    for block in blockchain.chain:
        for tx in block.transactions:
            txs.append(tx)
    return jsonify(txs)


# -----------------------------
# BLOQUES
# -----------------------------
@app.route("/admin/blocks", methods=["GET"])
@require_admin
def admin_blocks():
    return jsonify([{
        "index": b.index,
        "timestamp": b.timestamp,
        "transactions": b.transactions,
        "previous_hash": b.previous_hash,
        "hash": b.hash
    } for b in blockchain.chain])


# -----------------------------
# APROBAR KYC
# -----------------------------
@app.route("/admin/kyc/approve", methods=["POST"])
@require_admin
def admin_approve_kyc():
    data = request.json
    user_id = data.get("user_id")

    db = load_db()
    for u in db["users"]:
        if u["id"] == user_id:
            u["kyc"]["status"] = "approved"
            save_db(db)
            return jsonify({"message": "KYC aprobado"})

    return jsonify({"error": "Usuario no encontrado"}), 404


# -----------------------------
# RECHAZAR KYC
# -----------------------------
@app.route("/admin/kyc/reject", methods=["POST"])
@require_admin
def admin_reject_kyc():
    data = request.json
    user_id = data.get("user_id")

    db = load_db()
    for u in db["users"]:
        if u["id"] == user_id:
            u["kyc"]["status"] = "rejected"
            save_db(db)
            return jsonify({"message": "KYC rechazado"})

    return jsonify({"error": "Usuario no encontrado"}), 404


# -----------------------------
# INICIAR SERVIDOR ADMIN
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8888, debug=True)
