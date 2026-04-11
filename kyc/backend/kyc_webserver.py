"""Web server for KYC frontend pages."""

from flask import Flask, render_template, request, send_file
from flask_cors import CORS
from jinja2 import ChoiceLoader, FileSystemLoader

app = Flask(__name__)
CORS(app)


@app.after_request
def set_security_headers(response):
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' data: https:; "
        "connect-src 'self' https: http: ws: wss:; "
        "object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

app.jinja_loader = ChoiceLoader([
    FileSystemLoader("/app/kyc/fronttend"),
])


def _get_client_ip():
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.remote_addr or ""

@app.route("/kyc")
@app.route("/kyc/")
def kyc_home():
    return render_template("kyc.html")


@app.route("/kyc/estado")
def kyc_estado():
    return render_template("estado_kyc.html")


@app.route("/kyc/aprobado")
def kyc_aprobado():
    return render_template("KYC_aprobado.html")


@app.route("/kyc/rechazado")
@app.route("/kyc/rechzado")
def kyc_rechazado():
    return render_template("kyc_rechzado.html")


@app.route("/kyc/telefono")
def kyc_telefono():
    return render_template("KYCtelefono.html")


@app.route("/kyc/admin")
def admin_kyc_page():
    client_ip = _get_client_ip()
    if not client_ip.startswith("192.168."):
        return "Acceso permitido solo desde la red interna", 403
    return render_template("admin_kyc.html")


@app.route("/kyc/seguridad/guard.js")
@app.route("/CriptoBendicion/kyc/seguridad/guard.js")
def kyc_security_guard_js():
    return send_file("/app/seguridad/frontend/guard.js", mimetype="application/javascript")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5016, debug=True)
