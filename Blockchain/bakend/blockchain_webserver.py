from flask import Flask, render_template, send_file
from flask_cors import CORS
from jinja2 import FileSystemLoader, ChoiceLoader

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

# Cargar plantillas desde blockchain/frontend
app.jinja_loader = ChoiceLoader([
    FileSystemLoader("/app/frontend")
])

# ============================================================
# Página principal del Explorador Blockchain
# ============================================================
@app.route("/blockchainweb")
def blockchain_page():
    return render_template("blockchain.html")

# ============================================================
# Página secundaria (si quieres agregar más vistas)
# ============================================================
@app.route("/CriptoBendicion/blockchainweb/bendicion")
def bendicion_page():
    return render_template("blockchainbendicion.html")

@app.route("/blockchain/seguridad/guard.js")
@app.route("/CriptoBendicion/blockchain/seguridad/guard.js")
def blockchain_security_guard_js():
    return send_file("/app/seguridad/frontend/guard.js", mimetype="application/javascript")


# ============================================================
# Servidor
# ============================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=True)
