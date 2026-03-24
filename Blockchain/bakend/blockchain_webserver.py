from flask import Flask, render_template, send_from_directory
from flask_cors import CORS
from jinja2 import FileSystemLoader, ChoiceLoader
import os

app = Flask(__name__)
CORS(app)

# Ruta real del frontend dentro del contenedor
FRONTEND_DIR = "/app/frontend"

# Cargar plantillas desde /app/frontend
app.jinja_loader = ChoiceLoader([
    FileSystemLoader(FRONTEND_DIR)
])

# Página principal
@app.route("/blockchainweb")
def blockchain_page():
    return render_template("blockchain.html")

# Archivos estáticos (CSS, JS, imágenes)
@app.route("/CriptoBendicion/blockchainweb/<path:filename>")
def blockchain_static(filename):
    return send_from_directory(FRONTEND_DIR, filename)

if __name__ == "__main__":
    print("Explorador Blockchain iniciado en http://0.0.0.0:5005")
    app.run(host="0.0.0.0", port=5005, debug=True)
