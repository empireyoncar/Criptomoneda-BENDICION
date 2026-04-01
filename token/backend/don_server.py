from flask import Flask, jsonify, request
from flask_cors import CORS
import don  # tu backend del token
from don_value import get_don_value, set_don_value

app = Flask(__name__)
CORS(app)

# ============================
#   ENDPOINTS TOKEN DON
# ============================

@app.route("/don/balance/<user_id>", methods=["GET"])
def balance(user_id):
    return jsonify({
        "user_id": user_id,
        "balance": don.get_balance(user_id)
    })


@app.route("/don/total_supply", methods=["GET"])
def total_supply():
    return jsonify({
        "total_supply": don.get_total_supply()
    })


@app.route("/don/add", methods=["POST"])
def add():
    data = request.json
    don.add(data["user_id"], data["amount"])
    return jsonify({"status": "ok"})


@app.route("/don/subtract", methods=["POST"])
def subtract():
    data = request.json
    ok = don.subtract(data["user_id"], data["amount"])
    return jsonify({"success": ok})


@app.route("/don/transfer", methods=["POST"])
def transfer():
    data = request.json
    ok = don.transfer(data["from_user"], data["to_user"], data["amount"])
    return jsonify({"success": ok})


@app.route("/don/burn", methods=["POST"])
def burn():
    data = request.json
    ok = don.burn(data["user_id"], data["amount"])
    return jsonify({"success": ok})

@app.route("/price", methods=["GET"])
def price():
    return jsonify({"don_value": get_don_value()})

@app.route("/price/update", methods=["POST"])
def update_price():
    data = request.json
    new_value = float(data.get("don_value", 0))

    if new_value <= 0:
        return jsonify({"error": "Valor inválido"}), 400

    set_don_value(new_value)
    return jsonify({"status": "ok", "new_value": new_value})

# ============================
#   SERVIDOR
# ============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5008, debug=True)
