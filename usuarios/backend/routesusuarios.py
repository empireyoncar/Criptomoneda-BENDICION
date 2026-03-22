from flask import Blueprint, render_template

usuarios_bp = Blueprint("usuarios", __name__, template_folder="../frontend")

@usuarios_bp.route("/login")
def login_page():
    return render_template("login.html")

@usuarios_bp.route("/register")
def register_page():
    return render_template("register.html")
