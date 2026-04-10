from flask import Flask, render_template, send_file
from flask_cors import CORS
from jinja2 import FileSystemLoader, ChoiceLoader

app = Flask(__name__)
CORS(app)

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


# ============================================================
# Servidor
# ============================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)
