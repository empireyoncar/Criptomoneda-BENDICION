from flask import Flask, send_from_directory, render_template
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "..", "frontend")
STATIC_DIR = os.path.join(TEMPLATES_DIR, "static")

app = Flask(
    __name__,
    template_folder=TEMPLATES_DIR,
    static_folder=STATIC_DIR
)

# ============================================================
# Página principal de Wallet
# ============================================================
@app.route("/wallet")
def wallet_page():
    return render_template("wallet.html")


# ============================================================
# Archivos estáticos (CSS, JS, imágenes)
# ============================================================
@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(STATIC_DIR, filename)


# ============================================================
# Servidor
# ============================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003)
