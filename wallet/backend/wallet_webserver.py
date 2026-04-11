from flask import Flask, abort, render_template, send_file, send_from_directory
from flask_cors import CORS
from jinja2 import FileSystemLoader, ChoiceLoader

app = Flask(__name__)
CORS(app)

VENDOR_FILES = {"elliptic.min.js", "crypto-js.min.js"}


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

# Cargar plantillas desde wallet/frontend
app.jinja_loader = ChoiceLoader([
    FileSystemLoader("/app/frontend")
])

# ============================================================
# Página principal de Wallet
# ============================================================
@app.route("/wallet")
def wallet_page():
    return render_template("wallet.html")

@app.route("/wallet/envio")
def envio_page():
    return render_template("envio.html")

@app.route("/wallet/seguridad/guard.js")
@app.route("/CriptoBendicion/wallet/seguridad/guard.js")
def wallet_security_guard_js():
    return send_file("/app/seguridad/frontend/guard.js", mimetype="application/javascript")


@app.route("/seguridad/vendor/<path:filename>")
@app.route("/CriptoBendicion/seguridad/vendor/<path:filename>")
def wallet_security_vendor_js(filename):
    if filename not in VENDOR_FILES:
        abort(404)
    return send_from_directory("/app/seguridad/frontend/vendor", filename, mimetype="application/javascript")


# ============================================================
# Servidor
# ============================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)
