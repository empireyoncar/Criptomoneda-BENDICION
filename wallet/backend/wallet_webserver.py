from flask import Flask, render_template
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

@app.route("/envio")
def envio_page():
    return render_template("envio.html")

# ============================================================
# Servidor
# ============================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)
