from flask import Flask, render_template, jsonify, Blueprint
from flask_cors import CORS
from jinja2 import FileSystemLoader, ChoiceLoader

# Importar función del backend de staking

# ============================================================
# Blueprint API Staking
# ============================================================
staking_api = Blueprint("staking_api", __name__)

# ============================================================
# Servidor principal
# ============================================================
app = Flask(__name__)
CORS(app)

# Cargar plantillas desde /app/frontend (Docker)
app.jinja_loader = ChoiceLoader([
    FileSystemLoader("/app/frontend")
])

# ============================================================
# Rutas HTML
# ============================================================
@app.route("/staking/panelstaking")
def staking_page():
    return render_template("staking.html")

@app.route("/staking/dashboard")
def staking_dashboard_page():
    return render_template("staking_dashboard.html")


@app.route("/staking/stake_activos")
def staking_active_page():
    return render_template("stake_activos.html")


@app.route("/staking/historial")
def staking_history_page():
    return render_template("historial.html")


@app.route("/staking/radar_rapido")
def staking_radar_page():
    return render_template("radar_rapido.html")


@app.route("/staking/calendario_salida")
def staking_calendar_page():
    return render_template("calendario_salida.html")


# ============================================================
# Servidor
# ============================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5007, debug=True)
