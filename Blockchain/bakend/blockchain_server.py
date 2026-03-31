from flask import Flask, request, jsonify
from flask_cors import CORS
from blockchain import Blockchain
from hashlib import sha256
from ecdsa import VerifyingKey, SECP256k1
import json

app = Flask(__name__)
CORS(app)

# Permitir hosts internos de Docker
app.config["ALLOWED_HOSTS"] = ["*", "blockchain_api", "blockchain_api:5004", "localhost", "127.0.0.1"]

# Instancia única de la blockchain
blockchain = Blockchain()


# ============================================================
#   ESTADO DE LA CADENA
# ============================================================
@app.route("/validate", methods=["GET"])
def validate_chain():
    return jsonify({"valid": blockchain.is_chain_valid()})


# ============================================================
#   VER CADENA COMPLETA
# ============================================================
@app.route("/chain", methods=["GET"])
def get_chain():
    return jsonify([
        {
            "index": b.index,
            "timestamp": b.timestamp,
            "transactions": b.transactions,
            "previous_hash": b.previous_hash,
            "hash": b.hash
        }
        for b in blockchain.chain
    ])


# ============================================================
#   TRANSACCIONES PENDIENTES
# ============================================================
@app.route("/pending", methods=["GET"])
def get_pending():
    return jsonify(blockchain.pending_transactions)


# ============================================================
#   BUSCAR BLOQUE POR HASH
# ============================================================
@app.route("/block/<hash_value>", methods=["GET"])
def get_block(hash_value):
    for b in blockchain.chain:
        if b.hash == hash_value:
            return jsonify({
                "index": b.index,
                "timestamp": b.timestamp,
                "transactions": b.transactions,
                "previous_hash": b.previous_hash,
                "hash": b.hash
            })
    return jsonify({"error": "Bloque no encontrado"}), 404


# ============================================================
#   BUSCAR TRANSACCIÓN POR HASH
# ============================================================
@app.route("/tx/<hash_value>", methods=["GET"])
def get_tx(hash_value):
    for b in blockchain.chain:
        for tx in b.transactions:
            tx_hash = sha256(json.dumps(tx, sort_keys=True).encode()).hexdigest()
            if tx_hash == hash_value:
                return jsonify(tx)
    return jsonify({"error": "Transacción no encontrada"}), 404


# ============================================================
#   BALANCE + SALDO BLOQUEADO
# ============================================================
@app.route("/wallet/<address>", methods=["GET"])
def wallet_info(address):
    balance = blockchain.get_balance(address)
    locked = blockchain._get_locked_balance(address)
    return jsonify({
        "address": address,
        "balance": balance,
        "locked": locked
    })


# ============================================================
#   HISTORIAL DE WALLET
# ============================================================
@app.route("/wallet/<address>/history", methods=["GET"])
def wallet_history(address):
    history = []
    for b in blockchain.chain:
        for tx in b.transactions:
            if tx["from"] == address or tx["to"] == address:
                history.append(tx)
    return jsonify(history)


# ============================================================
#   TRANSACCIÓN FIRMADA (SEGURA)
# ============================================================
@app.route("/send_tx", methods=["POST"])
def send_tx():
    data = request.json
    tx = data.get("tx")
    public_key_hex = data.get("public_key")
    signature_hex = data.get("signature")

    if not tx or not public_key_hex or not signature_hex:
        return jsonify({"error": "Datos incompletos"}), 400

    sender = tx.get("from")
    receiver = tx.get("to")
    amount = tx.get("amount")

    if not sender or not receiver or amount is None:
        return jsonify({"error": "Transacción inválida"}), 400

    recalculated_address = sha256(bytes.fromhex(public_key_hex)).hexdigest()
    if recalculated_address != sender:
        return jsonify({"error": "Address no coincide con la clave pública"}), 400

    try:
        vk = VerifyingKey.from_string(bytes.fromhex(public_key_hex), curve=SECP256k1)
        tx_hash = sha256(json.dumps(tx, sort_keys=True).encode()).digest()
        vk.verify(bytes.fromhex(signature_hex), tx_hash)
    except:
        return jsonify({"error": "Firma inválida"}), 400

    ok = blockchain.add_transaction(sender, receiver, amount)
    if not ok:
        return jsonify({"error": "Saldo insuficiente"}), 400

    return jsonify({"message": "Transacción añadida"})

# ============================================================
#   MINT (CREAR MONEDAS) 
# ============================================================
@app.route("/mint", methods=["POST"])
def mint():
    # LOG 1 — Ver datos crudos que llegan desde admin
    print("BLOCKCHAIN RAW BODY:", request.data)

    # LOG 2 — Ver JSON interpretado por Flask
    print("BLOCKCHAIN JSON PARSED:", request.json)

    data = request.json
    if not data:
        return jsonify({"error": "JSON inválido o vacío"}), 400

    address = data.get("address")
    amount = data.get("amount")

    # LOG 3 — Ver parámetros individuales
    print("BLOCKCHAIN PARAMS:", {"address": address, "amount": amount})

    if not address or amount is None:
        return jsonify({"error": "Faltan parámetros"}), 400

    try:
        amount = float(amount)
    except:
        return jsonify({"error": "Cantidad inválida"}), 400

    # Transacción especial del sistema
    ok = blockchain.add_transaction("SYSTEM", address, amount)

    # LOG 4 — Resultado de add_transaction
    print("BLOCKCHAIN add_transaction OK?:", ok)

    if not ok:
        return jsonify({"error": "No se pudo crear la transacción"}), 400

    return jsonify({"message": "Transacción de mint creada correctamente"})


# ============================================================
#   CREAR BLOQUE
# ============================================================
@app.route("/commit", methods=["POST"])
def commit_block():
    # LOG 5 — Ver estado antes del commit
    print("BLOCKCHAIN COMMIT — pending:", blockchain.pending_transactions)

    block = blockchain.commit_pending_transactions()

    # LOG 6 — Resultado del commit
    print("BLOCKCHAIN COMMIT RESULT:", block)

    if block is None:
        return jsonify({"error": "No hay transacciones pendientes"}), 400

    return jsonify({
        "message": "Bloque creado",
        "index": block.index
    })

@app.get("/stats")
def get_stats():
    confirmed = 0
    for block in blockchain.chain:
        confirmed += len(block.transactions)

    pending = len(blockchain.pending_transactions)
    blocks = len(blockchain.chain)
    wallets = len(blockchain.wallets)

    return jsonify({
        "confirmed_transactions": confirmed,
        "pending_transactions": pending,
        "total_transactions": confirmed + pending,
        "blocks": blocks,
        "wallets": wallets
    })

# ============================================================
#   INICIAR SERVIDOR
# ============================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004, debug=False, use_reloader=False)

