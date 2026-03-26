from flask import Flask, render_template
from flask_cors import CORS
from jinja2 import FileSystemLoader, ChoiceLoader

app = Flask(__name__)
CORS(app)

# ============================================================
# Cargar plantillas desde admin/frontend (para Docker)
# ============================================================
app.jinja_loader = ChoiceLoader([
    FileSystemLoader("/app/admin/frontend")
])

# ============================================================
# Página de Login del Admin
# ============================================================
@app.route("/CriptoBendicion/admin/login")
def admin_login_page():
    return render_template("login.html")

# ============================================================
# Panel Principal del Admin
# ============================================================
@app.route("/CriptoBendicion/admin/")
def admin_dashboard():
    return render_template("admin.html")

# ============================================================
# Página de Mint del Admin
# ============================================================
@app.route("/CriptoBendicion/admin/mint")
def admin_mint_page():
    return render_template("mint.html")

# ============================================================
# Servidor
# ============================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5011, debug=True)
