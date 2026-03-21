from flask import Flask, request, jsonify
from staking_manager import stake_tokens

app = Flask(__name__)

@app.post("/stake")
def api_stake():
    data = request.json

    user_id = data.get("user_id")
    amount = data.get("amount")
    days = data.get("days")

    if not user_id or not amount or not days:
        return jsonify({"error": "Faltan parámetros"}), 400

    result = stake_tokens(user_id, amount, days)

    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6666)
