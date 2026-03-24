from flask import Flask, render_template
from flask_cors import CORS
from jinja2 import FileSystemLoader, ChoiceLoader

app = Flask(__name__)
CORS(app)

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

# ============================================================
# Servidor
# ============================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=True)
