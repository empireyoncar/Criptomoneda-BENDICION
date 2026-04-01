from flask import Flask, render_template
from flask_cors import CORS
from jinja2 import FileSystemLoader, ChoiceLoader

app = Flask(__name__)
CORS(app)

# ============================================================
# Cargar plantillas desde token/frontend
# ============================================================
app.jinja_loader = ChoiceLoader([
    FileSystemLoader("/app/token/frontend")
])

# ============================================================
# 1. Dashboard DON
# ============================================================
@app.route("/don/dashboard")
def don_dashboard():
    return render_template("dashboard_don.html")

# ============================================================
# 2. Panel del Usuario DON
# ============================================================
@app.route("/don/panel")
def don_panel():
    return render_template("panel_don.html")

@app.route("/don/admin")
def don_admin():
    user_id = request.cookies.get("user_id")

    # Si no hay login → fuera
    if not user_id:
        return redirect("/CriptoBendicion/login")

    # Solo el admin REAL puede entrar
    if user_id != "001":
        return "Acceso denegado", 403

    return render_template("admin_don.html")


# ============================================================
# Servidor
# ============================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5009, debug=True)
