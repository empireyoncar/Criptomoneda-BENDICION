from flask import Flask, jsonify, request
from flask_cors import CORS
import don  # tu backend del token
from don_history import get_transactions
from don_value import get_don_value, set_don_value

app = Flask(__name__)
CORS(app)


def _json_payload():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def _missing_fields(data, required):
    return [field for field in required if field not in data]

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


@app.route("/don/history", methods=["GET"])
def history():
    limit = request.args.get("limit", type=int)
    user_id = request.args.get("user_id")
    transactions = get_transactions(limit=limit, user_id=user_id)
    return jsonify({"transactions": transactions, "count": len(transactions)})


@app.route("/don/add", methods=["POST"])
def add():
    data = _json_payload()
    missing = _missing_fields(data, ["user_id", "amount"])
    if missing:
        return jsonify({"error": f"Faltan campos: {', '.join(missing)}"}), 400

    tx_id = don.add(data["user_id"], data["amount"], metadata=data.get("metadata"))
    if not tx_id:
        return jsonify({"error": "No se pudo emitir DON. Verifica el monto."}), 400
    return jsonify({"status": "ok", "tx_id": tx_id})


@app.route("/don/transfer", methods=["POST"])
def transfer():
    data = _json_payload()
    missing = _missing_fields(data, ["from_user", "to_user", "amount"])
    if missing:
        return jsonify({"error": f"Faltan campos: {', '.join(missing)}"}), 400

    ok, tx_id = don.transfer(data["from_user"], data["to_user"], data["amount"], metadata=data.get("metadata"))
    if not ok:
        return jsonify({"success": False, "tx_id": None, "error": "Saldo insuficiente o monto inválido"}), 400
    return jsonify({"success": True, "tx_id": tx_id})


@app.route("/don/burn", methods=["POST"])
def burn():
    data = _json_payload()
    missing = _missing_fields(data, ["user_id", "amount"])
    if missing:
        return jsonify({"error": f"Faltan campos: {', '.join(missing)}"}), 400

    ok, tx_id = don.burn(data["user_id"], data["amount"], metadata=data.get("metadata"))
    if not ok:
        return jsonify({"success": False, "tx_id": None, "error": "Saldo insuficiente o monto inválido"}), 400
    return jsonify({"success": True, "tx_id": tx_id})

@app.route("/price", methods=["GET"])
def price():
    return jsonify({"don_value": get_don_value()})

@app.route("/price/update", methods=["POST"])
def update_price():
    data = _json_payload()
    try:
        new_value = float(data.get("don_value", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "Valor inválido"}), 400

    if new_value <= 0:
        return jsonify({"error": "Valor inválido"}), 400

    set_don_value(new_value)
    return jsonify({"status": "ok", "new_value": new_value})

# ============================
#   SERVIDOR
# ============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5008, debug=True)
