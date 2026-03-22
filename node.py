from flask import Flask, request, jsonify
from flask_cors import CORS
from blockchain import Blockchain
from ecdsa import VerifyingKey, SECP256k1
from hashlib import sha256
import json
import os
from werkzeug.utils import secure_filename
from wallet_manager import create_wallet_for_user

from usuarios.backend.database import (
    register_user, login_user, add_wallet_to_user,
    get_user_wallet, load_db, save_db
)

app = Flask(__name__)
CORS(app)

blockchain = Blockchain()

UPLOAD_FOLDER = "kyc_docs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ============================================================
#   SISTEMA DE ROLES: ADMIN
# ============================================================

def is_admin(user_id):
    db = load_db()
    for u in db["users"]:
        if u["id"] == user_id and u["role"] == "admin":
            return True
    return False


def require_admin(func):
    def wrapper(*args, **kwargs):
        user_id = request.args.get("user_id")
        if not user_id or not is_admin(user_id):
            return jsonify({"error": "No autorizado"}), 403
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper


# ============================================================
#   REGISTRO NIVEL 3
# ============================================================
@app.route("/crypto/register", methods=["POST"])
def register():
    data = request.json

    fullname = data.get("fullname")
    birthdate = data.get("birthdate")
    country = data.get("country")
    address = data.get("address")
    phone = data.get("phone")
    email = data.get("email")
    password = data.get("password")

    if not fullname or not birthdate or not country or not address or not email or not password:
        return jsonify({"error": "Faltan datos obligatorios"}), 400

    user_id = register_user(fullname, birthdate, country, address, phone, email, password)

    if not user_id:
        return jsonify({"error": "El email ya está registrado"}), 400

    return jsonify({"message": "Usuario registrado correctamente", "user_id": user_id})


# ============================================================
#   LOGIN
# ============================================================
@app.route("/crypto/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    user_id = login_user(email, password)
    if user_id is None:
        return jsonify({"error": "Credenciales incorrectas"}), 401

    return jsonify({"message": "Login correcto", "user_id": user_id})


# ============================================================
#   WALLET DEL USUARIO
# ============================================================
@app.route("/crypto/user_wallet/<user_id>", methods=["GET"])
def user_wallet(user_id):
    wallet = get_user_wallet(user_id)
    return jsonify({"wallet": wallet})


# ============================================================
#   OBTENER INFORMACIÓN COMPLETA DE UNA WALLET
# ============================================================
@app.route("/crypto/wallet_info/<address>", methods=["GET"])
def wallet_info(address):
    try:
        with open("db/wallets.json", "r") as f:
            data = json.load(f)

        wallets = data.get("wallets", [])

        for w in wallets:
            if w.get("address") == address:
                return jsonify(w), 200

        return jsonify({"error": "Wallet not found"}), 404

    except Exception as e:
        return jsonify({"error": "Server error", "details": str(e)}), 500


# ============================================================
#   ASOCIAR WALLET
# ============================================================
@app.route("/crypto/link_wallet", methods=["POST"])
def link_wallet():
    data = request.json
    user_id = data.get("user_id")
    address = data.get("address")

    ok = add_wallet_to_user(user_id, address)
    if not ok:
        return jsonify({"error": "El usuario ya tiene una wallet"}), 400

    return jsonify({"message": "Wallet asociada"})


# ============================================================
#   REGISTRAR WALLET EN BLOCKCHAIN
# ============================================================
@app.route("/crypto/generate_wallet", methods=["POST"])
def generate_wallet_route():
    data = request.json
    user_id = data.get("user_id")

    wallet = create_wallet_for_user(user_id)

    return jsonify({
        "message": "Wallet creada",
        "address": wallet["address"],
        "public_key": wallet["public_key"],
        "private_key": wallet["private_key"]
    })


# ============================================================
#   TRANSACCIONES DEL USUARIO
# ============================================================
@app.route("/crypto/user_transactions/<address>", methods=["GET"])
def user_transactions(address):
    txs = []
    for block in blockchain.chain:
        for tx in block.transactions:
            if tx["from"] == address or tx["to"] == address:
                txs.append(tx)
    return jsonify({"transactions": txs})


# ============================================================
#   SUBIR DOCUMENTO KYC
# ============================================================
@app.route("/crypto/upload_kyc_step", methods=["POST"])
def upload_kyc_step():
    user_id = request.form.get("user_id")
    step = request.form.get("step")
    file = request.files.get("file")

    if step not in ["id_document", "address_document", "selfie"]:
        return jsonify({"error": "Paso KYC inválido"}), 400

    if not file:
        return jsonify({"error": "Archivo no recibido"}), 400

    filename = secure_filename(file.filename)
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(path)

    db = load_db()
    for u in db["users"]:
        if u["id"] == user_id:
            u["kyc"][step]["file"] = filename
            u["kyc"][step]["status"] = "submitted"
            save_db(db)
            return jsonify({"message": "Archivo subido", "step": step})

    return jsonify({"error": "Usuario no encontrado"}), 404


# ============================================================
#   ACTUALIZAR ESTADO KYC
# ============================================================
@app.route("/crypto/update_kyc_status", methods=["POST"])
def update_kyc_status():
    data = request.json
    user_id = data.get("user_id")
    step = data.get("step")
    status = data.get("status")

    if step not in ["id_document", "address_document", "selfie", "phone_verification"]:
        return jsonify({"error": "Paso inválido"}), 400

    db = load_db()
    for u in db["users"]:
        if u["id"] == user_id:
            u["kyc"][step]["status"] = status
            save_db(db)
            return jsonify({"message": "Estado actualizado"})

    return jsonify({"error": "Usuario no encontrado"}), 404


# ============================================================
#   OBTENER ESTADO KYC
# ============================================================
@app.route("/crypto/get_kyc_status/<user_id>", methods=["GET"])
def get_kyc_status(user_id):
    db = load_db()
    for u in db["users"]:
        if u["id"] == user_id:
            return jsonify(u["kyc"])
    return jsonify({"error": "Usuario no encontrado"}), 404


# ============================================================
#   ADMIN APRUEBA KYC
# ============================================================
@app.route("/crypto/admin/kyc/approve_step", methods=["POST"])
@require_admin
def admin_approve_step():
    data = request.json
    user_id = data.get("user_id")
    step = data.get("step")

    if step not in ["id_document", "address_document", "selfie", "phone_verification"]:
        return jsonify({"error": "Paso inválido"}), 400

    db = load_db()
    for u in db["users"]:
        if u["id"] == user_id:
            u["kyc"][step]["status"] = "approved"

            steps = u["kyc"]
            if all(
                steps[s]["status"] == "approved"
                for s in ["id_document", "address_document", "selfie"]
            ) and steps["phone_verification"]["status"] == "approved":
                u["kyc"]["overall_status"] = "approved"

            save_db(db)
            return jsonify({"message": "Paso aprobado"})

    return jsonify({"error": "Usuario no encontrado"}), 404


# ============================================================
#   BALANCE
# ============================================================
@app.route("/crypto/balance/<address>", methods=["GET"])
def balance(address):
    return jsonify({"address": address, "balance": blockchain.get_balance(address)})


# ============================================================
#   TRANSACCIÓN FIRMADA
# ============================================================
@app.route("/crypto/send_tx", methods=["POST"])
def send_tx():
    data = request.json
    tx = data.get("tx")
    public_key_hex = data.get("public_key")
    signature_hex = data.get("signature")

    sender = tx["from"]
    receiver = tx["to"]
    amount = tx["amount"]

    recalculated_address = sha256(bytes.fromhex(public_key_hex)).hexdigest()
    if recalculated_address != sender:
        return jsonify({"error": "Address no coincide"}), 400

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
def commit():
    block = blockchain.commit_pending_transactions()
    if block is None:
        return jsonify({"error": "No hay transacciones"}), 400
    return jsonify({"message": "Bloque creado", "index": block.index})


# ============================================================
#   VER BLOCKCHAIN
# ============================================================
@app.route("/crypto/chain", methods=["GET"])
def chain():
    return jsonify([{
        "index": b.index,
        "timestamp": b.timestamp,
        "transactions": b.transactions,
        "previous_hash": b.previous_hash,
        "hash": b.hash
    } for b in blockchain.chain])


# ============================================================
#   PANEL ADMIN
# ============================================================
@app.route("/crypto/admin/users", methods=["GET"])
@require_admin
def admin_users():
    db = load_db()
    return jsonify(db["users"])


@app.route("/crypto/admin/transactions", methods=["GET"])
@require_admin
def admin_transactions():
    txs = []
    for block in blockchain.chain:
        for tx in block.transactions:
            txs.append(tx)
    return jsonify(txs)


@app.route("/crypto/admin/blocks", methods=["GET"])
@require_admin
def admin_blocks():
    return jsonify([{
        "index": b.index,
        "timestamp": b.timestamp,
        "transactions": b.transactions,
        "previous_hash": b.previous_hash,
        "hash": b.hash
    } for b in blockchain.chain])

# ============================================================
#   ADMIN: CREAR CRIPTOMONEDAS (MINT)
# ============================================================
@app.route("/crypto/admin/mint", methods=["POST"])
@require_admin
def admin_mint():
    address = request.args.get("address")
    amount = request.args.get("amount")

    if not address or not amount:
        return jsonify({"error": "Faltan datos"}), 400

    try:
        amount = float(amount)
        if amount <= 0:
            return jsonify({"error": "La cantidad debe ser mayor a 0"}), 400
    except:
        return jsonify({"error": "Cantidad inválida"}), 400

    ok = blockchain.add_transaction("SYSTEM", address, amount)
    if not ok:
        return jsonify({"error": "No se pudo crear la transacción"}), 400

    return jsonify({
        "message": "Monedas creadas correctamente",
        "address": address,
        "amount": amount
    })

# ============================================================
#   INICIAR SERVIDOR
# ============================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7777, debug=True)
