from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from jinja2 import ChoiceLoader, FileSystemLoader

# Importar funciones de la base de datos JSON
from database import login_user, register_user, get_user_wallet, add_wallet_to_user

app = Flask(__name__)
CORS(app)

# -----------------------------------------
# PERMITIR VARIAS CARPETAS DE PLANTILLAS
# -----------------------------------------
app.jinja_loader = ChoiceLoader([
    FileSystemLoader("templates_web"),     # Web pública
    FileSystemLoader("templates_ADMIN"),   # Panel admin
    FileSystemLoader("templates_KYC")      # Páginas KYC
])

# -----------------------------
# PÁGINAS PÚBLICAS DEL USUARIO
# -----------------------------

@app.route("/")
@app.route("/wallet")
@app.route("/wallet.html")
def wallet_page():
    return render_template("wallet.html")

@app.route("/envio")
@app.route("/envio.html")
def envio_page():
    return render_template("envio.html")

@app.route("/blockchainbendicion")
@app.route("/blockchainbendicion.html")
def blockchain_page():
    return render_template("blockchainbendicion.html")

@app.route("/register")
@app.route("/register.html")
def register_page():
    return render_template("register.html")

@app.route("/login")
@app.route("/login.html")
def login_page():
    return render_template("login.html")

@app.route("/kyc")
@app.route("/kyc.html")
def kyc_page():
    return render_template("kyc.html")

@app.route("/estado_kyc")
@app.route("/estado_kyc.html")
def estado_kyc_page():
    return render_template("estado_kyc.html")

@app.route("/admin_kyc")
@app.route("/admin_kyc.html")
def admin_kyc_page():
    return render_template("admin_kyc.html")

@app.route("/kyc_aprobado")
@app.route("/KYC_aprobado.html")
def kyc_aprobado_page():
    return render_template("KYC_aprobado.html")

@app.route("/kyc_telefono")
@app.route("/KYCtelefono.html")
def kyc_telefono_page():
    return render_template("KYCtelefono.html")

@app.route("/home")
@app.route("/home.html")
def home_page():
    return render_template("home.html")

@app.route("/staking")
@app.route("/staking.html")
def staking_page():
    return render_template("staking.html")

# -----------------------------
# API LOGIN (POST)
# -----------------------------
@app.post("/login")
def login_api():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    # Validar usuario en database.json
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
# INICIAR SERVIDOR WEB
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
