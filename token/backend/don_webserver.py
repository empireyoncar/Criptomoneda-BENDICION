from flask import Flask, render_template, request, redirect
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
    client_ip = request.remote_addr

    # Solo permitir acceso desde la red interna 192.168.x.x
    if not client_ip.startswith("192.168."):
        return "Acceso permitido solo desde la red interna", 403

    return render_template("admin_don.html")


@app.route("/don/admin/history")
def don_admin_history():
    client_ip = request.remote_addr

    if not client_ip.startswith("192.168."):
        return "Acceso permitido solo desde la red interna", 403

    return render_template("admin_don_history.html")

# ============================================================
# Servidor
# ============================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5009, debug=True)
