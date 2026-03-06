# global_node.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from blockchain import Blockchain
import threading
from hashlib import sha256
from ecdsa import VerifyingKey, SECP256k1, BadSignatureError
import binascii

# Inicializar nodo
blockchain = Blockchain(mining=False)

# Crear app Flask y habilitar CORS
app = Flask(__name__)
CORS(app)  # Permite solicitudes desde cualquier origen

# -----------------------------
# Estado del nodo
# -----------------------------
@app.route("/status", methods=["GET"])
def status():
    data = {
        "blocks": len(blockchain.chain),
        "last_block_hash": blockchain.get_last_block().hash,
        "wallets": {w: blockchain.get_balance(w) for w in blockchain.wallets},
        "pending_transactions": blockchain.pending_transactions
    }
    return jsonify(data)

# -----------------------------
# Registrar usuario / wallet
# -----------------------------
@app.route("/register", methods=["POST"])
def register_user():
    data = request.json
    username = data.get("username")
    email = data.get("email")
    address = data.get("address")
    if not username or not email or not address:
        return jsonify({"error": "Faltan datos"}), 400
    if address in blockchain.wallets:
        return jsonify({"error": "Wallet ya registrada"}), 400
    blockchain.create_wallet(address)
    return jsonify({"message": f"Wallet registrada: {address}"}), 201

# -----------------------------
# Enviar transacción firmada
# -----------------------------
@app.route("/send_tx", methods=["POST"])
def send_transaction():
    data = request.json
    tx = data.get("tx")
    signature = data.get("signature")
    
    if not tx or not signature:
        return jsonify({"error": "Faltan datos"}), 400
    
    sender = tx.get("from")
    receiver = tx.get("to")
    amount = tx.get("amount")
    
    if not sender or not receiver or amount is None:
        return jsonify({"error": "Datos incompletos en la transacción"}), 400

    # Verificar firma usando clave pública del sender
    try:
        vk = VerifyingKey.from_string(binascii.unhexlify(sender[2:]), curve=SECP256k1)
        tx_hash = sha256(str(tx).encode()).digest()
        vk.verify(binascii.unhexlify(signature['signature']), tx_hash)
    except (BadSignatureError, ValueError, TypeError):
        return jsonify({"error": "Firma inválida"}), 400
    
    success = blockchain.add_transaction(sender, receiver, float(amount))
    if success:
        return jsonify({"message": f"Transacción agregada: {sender} -> {receiver} : {amount}"}), 201
    else:
        return jsonify({"error": "Transacción fallida"}), 400

# -----------------------------
# Consultar saldo
# -----------------------------
@app.route("/balance/<address>", methods=["GET"])
def balance(address):
    bal = blockchain.get_balance(address)
    return jsonify({"address": address, "balance": bal})

# -----------------------------
# Minar bloque
# -----------------------------
@app.route("/mine", methods=["POST"])
def mine():
    blockchain.mine_block()
    return jsonify({"message": "Bloque minado", "last_block_hash": blockchain.get_last_block().hash})

# -----------------------------
# Mostrar blockchain completa
# -----------------------------
@app.route("/chain", methods=["GET"])
def full_chain():
    chain_data = []
    for block in blockchain.chain:
        chain_data.append({
            "index": block.index,
            "timestamp": block.timestamp,
            "transactions": block.transactions,
            "previous_hash": block.previous_hash,
            "hash": block.hash,
            "nonce": block.nonce
        })
    return jsonify({"length": len(chain_data), "chain": chain_data})

# -----------------------------
# Ejecutar nodo en hilo separado
# -----------------------------
def run_flask():
    app.run(host="0.0.0.0", port=7777, debug=False)

if __name__ == "__main__":
    print("Iniciando nodo global BENDICION...")
    print("Blockchain cargada:", len(blockchain.chain), "bloques")
    threading.Thread(target=run_flask).start()
