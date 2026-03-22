from flask import Flask, render_template
from flask_cors import CORS
from jinja2 import FileSystemLoader, ChoiceLoader

app = Flask(__name__)
CORS(app)

# Cargar plantillas desde usuarios/frontend
app.jinja_loader = ChoiceLoader([
    FileSystemLoader("/app/frontend")
])

@app.route("/")
def home_page():
    return render_template("home.html")

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/register")
def register_page():
    return render_template("register.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
