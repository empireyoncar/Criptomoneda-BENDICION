from flask import Flask, render_template, jsonify, Blueprint
from flask_cors import CORS
from jinja2 import FileSystemLoader, ChoiceLoader

# Importar función del backend de staking
from staking_recompensa import get_total_staked

# ============================================================
# Blueprint API Staking
# ============================================================
staking_api = Blueprint("staking_api", __name__)

@staking_api.route("/Staking/total", methods=["GET"])
def staking_total():
    total = get_total_staked()
    return jsonify({"total_staked": total})


# ============================================================
# Servidor principal
# ============================================================
app = Flask(__name__)
CORS(app)

# Cargar plantillas desde /app/frontend (Docker)
app.jinja_loader = ChoiceLoader([
    FileSystemLoader("/app/frontend")
])

# Registrar Blueprint
app.register_blueprint(staking_api)


# ============================================================
# Rutas HTML
# ============================================================
@app.route("/CriptoBendicion/staking/panelstaking")
def staking_page():
    return render_template("staking.html")

@app.route("/staking/dashboard")
def staking_dashboard_page():
    return render_template("staking_dashboard.html")


# ============================================================
# Servidor
# ============================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5007, debug=True)
