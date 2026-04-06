from flask import Flask, request, jsonify
from create_staking import crear_staking   # <--- IMPORTAMOS TU FUNCIÓN

app = Flask(__name__)

# ---------------------------------------------------------
#   CREAR STAKING (USADO POR EL FRONTEND)
# ---------------------------------------------------------
@app.post("/Staking/create")
def api_create_staking():
    data = request.json

    required = ["user_id", "wallet", "amount", "days"]
    if not all(k in data for k in required):
        return jsonify({"error": "Faltan parámetros"}), 400

    try:
        result = crear_staking(
            user_id=data["user_id"],
            wallet_address=data["wallet"],
            amount=float(data["amount"]),
            days=int(data["days"])
        )
        return jsonify(result)

    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------
#   INICIAR SERVIDOR
# ---------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5006)
