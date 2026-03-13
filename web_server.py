from flask import Flask, render_template, redirect, url_for
from flask_cors import CORS

# Usamos un directorio de plantillas separado del admin
app = Flask(__name__, template_folder="templates_web")
CORS(app)

# -----------------------------
# REDIRECCIÓN AUTOMÁTICA A LOGIN
# -----------------------------
@app.route("/")
def root_redirect():
    return redirect(url_for("login_page"))

# -----------------------------
# PÁGINAS PÚBLICAS DEL USUARIO
# -----------------------------

# INDEX (si quieres mantenerlo accesible manualmente)
@app.route("/index")
@app.route("/index.html")
def home_page():
    return render_template("index.html")

# REGISTER
@app.route("/register")
@app.route("/register.html")
def register_page():
    return render_template("register.html")

# LOGIN
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
