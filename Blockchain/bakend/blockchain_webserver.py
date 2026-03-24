from flask import Flask, send_from_directory
from flask_cors import CORS
import os

app = Flask(__name__, static_folder="web")
CORS(app)

# ============================================================
#   SERVIR LA PÁGINA PRINCIPAL DEL EXPLORADOR
# ============================================================
@app.route("/")
def index():
    return send_from_directory("web", "blockchain.html")


# ============================================================
#   SERVIR ARCHIVOS ESTÁTICOS (CSS, JS, IMÁGENES)
# ============================================================
@app.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory("web", filename)


# ============================================================
#   INICIAR SERVIDOR WEB
# ============================================================
if __name__ == "__main__":
    print("Servidor web del explorador blockchain iniciado en http://0.0.0.0:8080")
    app.run(host="0.0.0.0", port=5005, debug=True)
