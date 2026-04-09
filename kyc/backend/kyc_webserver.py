"""Web server for KYC frontend pages."""

from flask import Flask, render_template
from flask_cors import CORS
from jinja2 import ChoiceLoader, FileSystemLoader

app = Flask(__name__)
CORS(app)

app.jinja_loader = ChoiceLoader([
    FileSystemLoader("/app/kyc/fronttend"),
])

@app.route("/kyc")
@app.route("/kyc/")
def kyc_home():
    return render_template("kyc.html")


@app.route("/kyc/estado")
def kyc_estado():
    return render_template("estado_kyc.html")


@app.route("/kyc/aprobado")
def kyc_aprobado():
    return render_template("KYC_aprobado.html")


@app.route("/kyc/rechazado")
@app.route("/kyc/rechzado")
def kyc_rechazado():
    return render_template("kyc_rechzado.html")


@app.route("/kyc/telefono")
def kyc_telefono():
    return render_template("KYCtelefono.html")


@app.route("/kyc/admin")
def admin_kyc_page():
    return render_template("admin_kyc.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5016, debug=True)
