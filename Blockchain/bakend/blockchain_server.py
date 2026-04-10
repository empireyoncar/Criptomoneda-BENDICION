import json

from flask import Flask, request, jsonify
from flask_cors import CORS
from blockchain import Blockchain
import sys

# Import signature verification
sys.path.insert(0, "/app/criptografia")
from firma_digital import verificar_firma
from blockchain_crypto import hash_sha256

app = Flask(__name__)
CORS(app)




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
            tx_hash = hash_sha256(json.dumps(tx, sort_keys=True))
            if tx_hash == hash_value:
                return jsonify(tx)
    return jsonify({"error": "Transacción no encontrada"}), 404


# ============================================================
#   BALANCE + SALDO BLOQUEADO + NONCE
# ============================================================
@app.route("/wallet/<address>", methods=["GET"])
def wallet_info(address):
    balance = blockchain.get_balance(address)  # satichis
    locked = blockchain._get_locked_balance(address)  # satichis
    nonce = blockchain.get_nonce(address)
    return jsonify({
        "address": address,
        "balance": balance,  # in satichis
        "locked": locked,    # in satichis
        "nonce": nonce
    })


# ============================================================
#   OBTENER NONCE ACTUAL DE UNA CUENTA
# ============================================================
@app.route("/wallet/<address>/nonce", methods=["GET"])
def get_nonce(address):
    nonce = blockchain.get_nonce(address)
    return jsonify({"address": address, "nonce": nonce})


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
#   TRANSACCIÓN CON NONCE + FIRMA ECDSA VALIDATION
# ============================================================
@app.route("/send_tx", methods=["POST"])
def send_tx():
    data = request.json
    tx = data.get("tx")

    if not tx:
        return jsonify({"error": "Datos incompletos"}), 400

    sender = tx.get("from")
    receiver = tx.get("to")
    amount = tx.get("amount")
    tx_id = tx.get("tx_id")
    metadata = tx.get("metadata")
    nonce = tx.get("nonce")
    public_key = tx.get("public_key")
    signature = tx.get("signature")

    if not sender or not receiver or amount is None:
        return jsonify({"error": "Transacción inválida"}), 400

    # Amount should be in satichis (integers)
    try:
        amount = int(amount)
    except (ValueError, TypeError):
        return jsonify({"error": "Amount must be an integer (satichis)"}), 400

    # SYSTEM transactions don't need signature
    if sender != "SYSTEM":
        # Validate public_key and signature presence
        if not public_key or not signature:
            return jsonify({"error": "TX from user must include public_key and signature"}), 400

        # Verify that address matches public_key
        derived_address = hash_sha256(public_key)
        if derived_address != sender:
            return jsonify({"error": "Public key does not match sender address"}), 403

        # Prepare TX payload for signature verification (without signature field)
        tx_for_verification = {
            "from": sender,
            "to": receiver,
            "amount": amount,
            "nonce": nonce
        }
        if tx_id:
            tx_for_verification["tx_id"] = str(tx_id)
        if metadata is not None:
            tx_for_verification["metadata"] = metadata

        # Verify ECDSA signature
        try:
            if not verificar_firma(tx_for_verification, signature, public_key):
                return jsonify({"error": "Invalid signature"}), 403
        except Exception as e:
            return jsonify({"error": f"Signature verification failed: {str(e)}"}), 403

    ok = blockchain.add_transaction(sender, receiver, amount, tx_id=tx_id, metadata=metadata, nonce=nonce)
    if not ok:
        return jsonify({"error": "Saldo insuficiente o nonce inválido"}), 400

    return jsonify({"message": "Transacción añadida", "tx_id": tx_id})

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
        amount = int(amount)
    except:
        return jsonify({"error": "Cantidad inválida (debe ser entero en satichis)"}), 400

    # Transacción especial del sistema
    ok = blockchain.add_transaction("SYSTEM", address, amount)

    # LOG 4 — Resultado de add_transaction
    print("BLOCKCHAIN add_transaction OK?:", ok)

    if not ok:
        return jsonify({"error": "No se pudo crear la transacción"}), 400

    return jsonify({"message": "Transacción de mint creada correctamente"})

# ============================================================
#   INICIALIZAR SUMINISTRO (10,000 monedas a treasury)
# ============================================================
@app.route("/initialize_supply", methods=["POST"])
def initialize_supply():
    """
    ONE-TIME: Create 10,000 initial BENDICION tokens.
    Stores them in SYSTEM treasury address.
    
    Treasury address: "0x00000000000000000000000000000000TREASURY"
    Amount: 10,000 * 100,000,000 satichis = 1,000,000,000,000
    """
    # Check if already initialized
    treasury_address = "0x00000000000000000000000000000000TREASURY"
    if blockchain.get_balance(treasury_address) > 0:
        return jsonify({"error": "Supply already initialized"}), 400
    
    # Create 10,000 monedas = 1,000,000,000,000 satichis
    total_supply_satichis = 10_000 * 100_000_000
    
    ok = blockchain.add_transaction("SYSTEM", treasury_address, total_supply_satichis)
    
    if not ok:
        return jsonify({"error": "Failed to create initial supply"}), 400
    
    # Auto-commit to seal it
    block = blockchain.commit_pending_transactions()
    
    return jsonify({
        "message": "Initial supply created",
        "treasury_address": treasury_address,
        "total_monedas": 10_000,
        "total_satichis": total_supply_satichis,
        "block_index": block.index if block else None
    })

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

