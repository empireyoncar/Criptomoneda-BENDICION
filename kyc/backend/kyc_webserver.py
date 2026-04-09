import os
from pathlib import Path

from flask import Flask, abort, render_template, request
from flask_cors import CORS
from jinja2 import FileSystemLoader, ChoiceLoader

app = Flask(__name__)
CORS(app)

# ============================================================
# Cargar plantillas desde kyc/frontend
# ============================================================
FRONTEND_DIR = Path(
    os.getenv("KYC_FRONTEND_DIR", str(Path(__file__).resolve().parents[1] / "fronttend"))
)
ALLOWED_ADMIN_IP = os.getenv("KYC_ADMIN_ALLOWED_IP", "192.168.1.178").strip()

app.jinja_loader = ChoiceLoader([
    FileSystemLoader(str(FRONTEND_DIR)),
])


def _client_ip() -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return (request.remote_addr or "").strip()


def _ensure_internal_admin_access() -> None:
    ip = _client_ip()
    normalized = ip.replace("::ffff:", "")
    if normalized != ALLOWED_ADMIN_IP:
        abort(403)

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


@app.route("/kyc/rechazado")
@app.route("/kyc/rechzado")
def kyc_rechazado_page():
    return render_template("kyc_rechzado.html")

@app.route("/kyc/telefono")
def kyc_telefono_page():
    return render_template("KYCtelefono.html")

@app.route("/kyc/admin")
def admin_kyc_page():
    _ensure_internal_admin_access()
    return render_template("admin_kyc.html")

# ============================================================
# Servidor
# ============================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5016, debug=True)
