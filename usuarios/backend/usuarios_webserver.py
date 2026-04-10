from flask import Flask, render_template, send_file
from flask_cors import CORS
from jinja2 import FileSystemLoader, ChoiceLoader

app = Flask(__name__)
CORS(app)

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

@app.route("/seguridad/guard.js")
@app.route("/CriptoBendicion/seguridad/guard.js")
def usuarios_security_guard_js():
    return send_file("/app/seguridad/frontend/guard.js", mimetype="application/javascript")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
