from flask import Flask, render_template
from flask_cors import CORS
from jinja2 import ChoiceLoader, FileSystemLoader

app = Flask(__name__)
CORS(app)

# -----------------------------------------
# PERMITIR VARIAS CARPETAS DE PLANTILLAS
# -----------------------------------------
# ORDEN CORRECTO:
# 1. templates_web     → Login y páginas del usuario
# 2. templates_ADMIN   → Panel admin
# 3. templates_KYC     → Páginas KYC
app.jinja_loader = ChoiceLoader([
    FileSystemLoader("templates_web"),     # Web pública (PRIMERO)
    FileSystemLoader("templates_ADMIN"),   # Panel admin
    FileSystemLoader("templates_KYC")      # Páginas KYC
])

# -----------------------------
# PÁGINAS PÚBLICAS DEL USUARIO
# -----------------------------

# WALLET (PÁGINA PRINCIPAL)
@app.route("/")
@app.route("/wallet")
@app.route("/wallet.html")
def wallet_page():
    return render_template("wallet.html")

# OPERACIONES (ENVÍO, BALANCE, BLOQUES)
@app.route("/envio")
@app.route("/envio.html")
def envio_page():
    return render_template("envio.html")

# EXPLORADOR DE BLOCKCHAIN
@app.route("/blockchainbendicion")
@app.route("/blockchainbendicion.html")
def blockchain_page():
    return render_template("blockchainbendicion.html")

# REGISTER
@app.route("/register")
@app.route("/register.html")
def register_page():
    return render_template("register.html")

# LOGIN (USUARIO)
@app.route("/login")
@app.route("/login.html")
def login_page():
    return render_template("login.html")

# KYC
@app.route("/kyc")
@app.route("/kyc.html")
def kyc_page():
    return render_template("kyc.html")

# ESTADO KYC
@app.route("/estado_kyc")
@app.route("/estado_kyc.html")
def estado_kyc_page():
    return render_template("estado_kyc.html")

# ADMIN KYC (vista del usuario)
@app.route("/admin_kyc")
@app.route("/admin_kyc.html")
def admin_kyc_page():
    return render_template("admin_kyc.html")

# KYC APROBADO
@app.route("/kyc_aprobado")
@app.route("/KYC_aprobado.html")
def kyc_aprobado_page():
    return render_template("KYC_aprobado.html")

# KYC TELÉFONO
@app.route("/kyc_telefono")
@app.route("/KYCtelefono.html")
def kyc_telefono_page():
    return render_template("KYCtelefono.html")

# -----------------------------
# INICIAR SERVIDOR WEB
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
