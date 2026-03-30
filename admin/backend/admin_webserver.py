from flask import Flask, render_template, request, session, redirect, jsonify
from flask_cors import CORS
from jinja2 import FileSystemLoader, ChoiceLoader
from functools import wraps
import requests

# Importar funciones reales del backend
from admin_manager import login_user, is_admin

app = Flask(__name__)
app.secret_key = "clave-super-secreta-123"
CORS(app)

# URL del blockchain API
BC_API = "http://blockchain_api:5004"

# ============================================================
#   PROTECCIÓN DE RUTAS
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
#   LOGIN
# ============================================================
@app.route("/CriptoBendicion/admin/login")
def login_page():
    return render_template("login.html")


@app.route("/CriptoBendicion/admin_login", methods=["POST"])
def admin_login():
    email = request.form.get("email")
    password = request.form.get("password")

    user_id = login_user(email, password)

    if not user_id:
        return "Credenciales incorrectas"

    if not is_admin(user_id):
        return "No eres administrador"

    session["user_id"] = user_id
    return redirect("/CriptoBendicion/admin/")


@app.route("/CriptoBendicion/admin/logout")
def logout():
    session.clear()
    return redirect("/CriptoBendicion/admin/login")

# ============================================================
#   PANEL ADMIN
# ============================================================
@app.route("/CriptoBendicion/admin/")
@require_admin
def admin_dashboard():
    return render_template("admin.html")


@app.route("/CriptoBendicion/admin/mint")
@require_admin
def admin_mint_page():
    return render_template("mint.html")

# ============================================================
#   ENDPOINTS PUENTE PARA MINT (5011 → 5004)
# ============================================================
@app.route("/CriptoBendicion/admin_api/mint/create", methods=["POST"])
@require_admin
def admin_mint_create():
    data = request.get_json(silent=True) or request.form

    address = data.get("address")
    amount = data.get("amount")

    if not address or amount is None:
        return jsonify({"error": "Faltan parámetros"}), 400

    # Convertir amount a número
    try:
        amount = float(amount)
    except:
        return jsonify({"error": "Cantidad inválida"}), 400

    res = requests.post(f"{BC_API}/mint", json={
        "address": address,
        "amount": amount
    })

    try:
        blockchain_json = res.json()
    except ValueError:
        return jsonify({
            "error": "Blockchain devolvió una respuesta no válida",
            "raw": res.text
        }), 500

    return jsonify(blockchain_json), res.status_code


@app.route("/CriptoBendicion/admin_api/mint/commit", methods=["POST"])
@require_admin
def admin_mint_commit():
    res = requests.post(f"{BC_API}/commit")

    try:
        blockchain_json = res.json()
    except ValueError:
        return jsonify({
            "error": "Blockchain devolvió una respuesta no válida",
            "raw": res.text
        }), 500

    return jsonify(blockchain_json), res.status_code

# ============================================================
#   CARGA DE PLANTILLAS (Docker)
# ============================================================
app.jinja_loader = ChoiceLoader([
    FileSystemLoader("/app/frontend")
])

# ============================================================
#   RUTA RAÍZ
# ============================================================
@app.route("/")
def root_redirect():
    return redirect("/CriptoBendicion/admin/login")

# ============================================================
#   INICIAR SERVIDOR
# ============================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5011, debug=True)
