from flask import Flask, render_template
from flask_cors import CORS
from jinja2 import FileSystemLoader, ChoiceLoader

app = Flask(__name__)
CORS(app)

# ============================================================
# Cargar plantillas desde kyc/frontend
# ============================================================
app.jinja_loader = ChoiceLoader([
    FileSystemLoader(r"C:\Users\empir\Documents\GitHub\Criptomoneda-BENDICION\kyc\fronttend")
])

# ============================================================
#   PÁGINAS DEL SISTEMA KYC
# ============================================================

@app.route("/kyc")
def kyc_page():
    return render_template("kyc.html")

@app.route("/kyc/estado")
def estado_kyc_page():
    return render_template("estado_kyc.html")

@app.route("/kyc/aprobado")
def kyc_aprobado_page():
    return render_template("KYC_aprobado.html")

@app.route("/kyc/telefono")
def kyc_telefono_page():
    return render_template("KYCtelefono.html")

@app.route("/kyc/admin")
def admin_kyc_page():
    return render_template("admin_kyc.html")

# ============================================================
# Servidor
# ============================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5009, debug=True)
