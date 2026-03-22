from flask import Flask, render_template
from flask_cors import CORS
from jinja2 import ChoiceLoader, FileSystemLoader

app = Flask(__name__)
CORS(app)

# -----------------------------------------
# PERMITIR VARIAS CARPETAS DE PLANTILLAS
# -----------------------------------------
app.jinja_loader = ChoiceLoader([
    FileSystemLoader("templates_web"),       # Web pública
    FileSystemLoader("templates_ADMIN"),     # Panel admin
    FileSystemLoader("templates_KYC"),       # Páginas KYC
    FileSystemLoader("templates_staking")    # Carpeta staking
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

# -----------------------------
# PÁGINAS DE STAKING
# -----------------------------

@app.route("/staking")
@app.route("/staking.html")
def staking_page():
    return render_template("staking.html")

@app.route("/staking_dashboard")
@app.route("/staking_dashboard.html")
def staking_dashboard_page():
    return render_template("staking_dashboard.html")

# -----------------------------
# INICIAR SERVIDOR WEB
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
