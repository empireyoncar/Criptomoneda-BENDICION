from flask import Flask, request, jsonify
from flask_cors import CORS
from blockchain import Blockchain
from hashlib import sha256
from ecdsa import VerifyingKey, SECP256k1
import json

app = Flask(__name__)
CORS(app)

# Instancia única de la blockchain
blockchain = Blockchain()


# ============================================================
#   ESTADO DE LA CADENA
# ============================================================
@app.route("/crypto/validate", methods=["GET"])
def validate_chain():
    return jsonify({"valid": blockchain.is_chain_valid()})


# ============================================================
#   VER CADENA COMPLETA
# ============================================================
@app.route("/crypto/chain", methods=["GET"])
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
@app.route("/crypto/pending", methods=["GET"])
def get_pending():
    return jsonify(blockchain.pending_transactions)


# ============================================================
#   BUSCAR BLOQUE POR HASH
# ============================================================
@app.route("/crypto/block/<hash_value>", methods=["GET"])
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
@app.route("/crypto/tx/<hash_value>", methods=["GET"])
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
@app.route("/crypto/wallet/<address>", methods=["GET"])
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
@app.route("/crypto/wallet/<address>/history", methods=["GET"])
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

@app.route("/crypto/send_tx", methods=["POST"])
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
#   CREAR BLOQUE
# ============================================================
@app.route("/crypto/commit", methods=["POST"])
def commit_block():
    block = blockchain.commit_pending_transactions()
    if block is None:
        return jsonify({"error": "No hay transacciones pendientes"}), 400

    return jsonify({
        "message": "Bloque creado",
        "index": block.index
    })


# ============================================================
#   INICIAR SERVIDOR
# ============================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004, debug=True)
