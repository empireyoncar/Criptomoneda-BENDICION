from flask import Flask, render_template
from flask_cors import CORS
from jinja2 import FileSystemLoader, ChoiceLoader

app = Flask(__name__)
CORS(app)

# Cargar plantillas desde Blockchain/frontend
app.jinja_loader = ChoiceLoader([
    FileSystemLoader("/app/frontend")
])

# ============================================================
#   PÁGINA PRINCIPAL DEL EXPLORADOR
# ============================================================
@app.route("/CriptoBendicion/blockchain")
def blockchain_page():
    return render_template("blockchainbendicion.html")

# ============================================================
#   SERVIDOR
# ============================================================
if __name__ == "__main__":
    print("Explorador Blockchain iniciado en http://0.0.0.0:5005")
    app.run(host="0.0.0.0", port=5005, debug=True)
