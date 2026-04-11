from flask import Flask, render_template, request, session, redirect, jsonify
from flask_cors import CORS
from jinja2 import FileSystemLoader, ChoiceLoader
from functools import wraps
import requests

# Importar funciones reales del backend
from admin_manager import login_user, is_admin

app = Flask(__name__)
app.secret_key = "clave-super-secreta-123"
CORS(app)


@app.after_request
def set_security_headers(response):
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' data: https:; "
        "connect-src 'self' https: http: ws: wss:; "
        "object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# URL del blockchain API
BC_API = "http://blockchain_api:5004"

# ============================================================
#   PROTECCIÓN DE RUTAS
# ============================================================
def require_admin(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user_id = session.get("user_id")
        if not is_admin(user_id):
            return redirect("/CriptoBendicion/admin/login")
        return func(*args, **kwargs)
    return wrapper

# ============================================================
#   LOGIN
# ============================================================
@app.route("/CriptoBendicion/admin/login")
def login_page():
    return render_template("login.html")


@app.route("/CriptoBendicion/admin_login", methods=["POST"])
def admin_login():
    try:
        if request.is_json:
            data = request.get_json() or {}
            email = data.get("email")
            password = data.get("password")
        else:
            email = request.form.get("email")
            password = request.form.get("password")

        user_id = login_user(email, password)
    except Exception as exc:
        if request.is_json:
            return jsonify({"error": f"Error interno de autenticacion: {exc}"}), 500
        return "Error interno de autenticacion", 500

    if not user_id:
        if request.is_json:
            return jsonify({"error": "Credenciales incorrectas"}), 401
        return "Credenciales incorrectas"

    if not is_admin(user_id):
        if request.is_json:
            return jsonify({"error": "No eres administrador"}), 403
        return "No eres administrador"

    session["user_id"] = user_id

    if request.is_json:
        return jsonify({
            "status": "ok",
            "user_id": user_id,
            "redirect": "/CriptoBendicion/admin/"
        })

    return redirect("/CriptoBendicion/admin/")


@app.route("/CriptoBendicion/admin/logout")
def logout():
    session.clear()
    return redirect("/CriptoBendicion/admin/login")

# ============================================================
#   PANEL ADMIN
# ============================================================
@app.route("/CriptoBendicion/admin/")
@require_admin
def admin_dashboard():
    return render_template("admin.html")


@app.route("/CriptoBendicion/admin/mint")
@require_admin
def admin_mint_page():
    return render_template("mint.html")


@app.route("/CriptoBendicion/admin/password")
@require_admin
def admin_password_page():
    return render_template("password.html")


@app.route("/CriptoBendicion/admin/info")
@require_admin
def admin_info_page():
    return render_template("info.html")


@app.route("/CriptoBendicion/admin/secure")
@require_admin
def admin_secure_page():
    return render_template("secure.html")


# ============================================================
#   CARGA DE PLANTILLAS (Docker)
# ============================================================
app.jinja_loader = ChoiceLoader([
    FileSystemLoader("/app/frontend")
])

# ============================================================
#   RUTA RAÍZ
# ============================================================
@app.route("/")
def root_redirect():
    return redirect("/CriptoBendicion/admin/login")

# ============================================================
#   INICIAR SERVIDOR
# ============================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5011, debug=True)
