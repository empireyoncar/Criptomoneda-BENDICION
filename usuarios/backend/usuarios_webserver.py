from flask import Flask, abort, render_template, send_file, send_from_directory
from flask_cors import CORS
from jinja2 import FileSystemLoader, ChoiceLoader

app = Flask(__name__)
CORS(app)

VENDOR_FILES = {"elliptic.min.js", "crypto-js.min.js"}


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

# Cargar plantillas desde usuarios/frontend
app.jinja_loader = ChoiceLoader([
    FileSystemLoader("/app/frontend")
])

@app.route("/home")
def home_page():
    return render_template("home.html")

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/register")
def register_page():
    return render_template("register.html")


@app.route("/verificacion")
def verification_2fa_page():
    return render_template("verificacion.html")

@app.route("/ssh")
def ssh_page():
    return render_template("ssh.html")

@app.route("/seguridad/guard.js")
@app.route("/CriptoBendicion/seguridad/guard.js")
def usuarios_security_guard_js():
    return send_file("/app/seguridad/frontend/guard.js", mimetype="application/javascript")


@app.route("/seguridad/vendor/<path:filename>")
@app.route("/CriptoBendicion/seguridad/vendor/<path:filename>")
def usuarios_security_vendor_js(filename):
    if filename not in VENDOR_FILES:
        abort(404)
    return send_from_directory("/app/seguridad/frontend/vendor", filename, mimetype="application/javascript")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
