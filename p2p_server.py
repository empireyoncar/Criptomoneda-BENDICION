from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)

DATA_FILE = "db/p2p_data.json"

# Cargar ofertas desde archivo
def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)

# Guardar ofertas en archivo
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

@app.get("/ofertas")
def get_ofertas():
    return jsonify(load_data())

@app.post("/ofertas")
def add_oferta():
    data = load_data()
    nueva = request.json
    data.append(nueva)
    save_data(data)
    return jsonify({"status": "ok", "message": "Oferta guardada"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9999)
