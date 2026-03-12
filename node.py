from flask import Flask, request, jsonify
from flask_cors import CORS
from blockchain import Blockchain
from ecdsa import VerifyingKey, SECP256k1
from hashlib import sha256
import json
import os
from werkzeug.utils import secure_filename
from wallet_manager import create_wallet_for_user

from database import (
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
@app.route("/register", methods=["POST"])
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
@app.route("/login", methods=["POST"])
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
@app.route("/user_wallet/<user_id>", methods=["GET"])
def user_wallet(user_id):
    wallet = get_user_wallet(user_id)
    return jsonify({"wallet": wallet})

# ============================================================
#   OBTENER INFORMACIÓN COMPLETA DE UNA WALLET
# ============================================================
@app.route("/wallet_info/<address>", methods=["GET"])
def wallet_info(address):
    try:
        # Cargar wallets.json
        with open("wallets.json", "r") as f:
            data = json.load(f)

        wallets = data.get("wallets", [])

        # Buscar la wallet por address
        for w in wallets:
            if w.get("address") == address:
                return jsonify(w), 200

        # Si no se encuentra
        return jsonify({"error": "Wallet not found"}), 404

    except Exception as e:
        return jsonify({"error": "Server error", "details": str(e)}), 500


# ============================================================
#   ASOCIAR WALLET
# ============================================================
@app.route("/link_wallet", methods=["POST"])
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
@app.route("/generate_wallet", methods=["POST"])
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
@app.route("/user_transactions/<address>", methods=["GET"])
def user_transactions(address):
    txs = []
    for block in blockchain.chain:
        for tx in block.transactions:
            if tx["from"] == address or tx["to"] == address:
                txs.append(tx)
    return jsonify({"transactions": txs})


# ============================================================
#   NUEVO: SUBIR DOCUMENTO KYC POR PASO
# ============================================================
@app.route("/upload_kyc_step", methods=["POST"])
def upload_kyc_step():
    user_id = request.form.get("user_id")
    step = request.form.get("step")  # id_document / address_document / selfie
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
#   NUEVO: ACTUALIZAR ESTADO DE UN PASO KYC
# ============================================================
@app.route("/update_kyc_status", methods=["POST"])
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
#   NUEVO: OBTENER ESTADO KYC COMPLETO
# ============================================================
@app.route("/get_kyc_status/<user_id>", methods=["GET"])
def get_kyc_status(user_id):
    db = load_db()
    for u in db["users"]:
        if u["id"] == user_id:
            return jsonify(u["kyc"])
    return jsonify({"error": "Usuario no encontrado"}), 404


# ============================================================
#   NUEVO: ADMIN APRUEBA UN PASO KYC
# ============================================================
@app.route("/admin/kyc/approve_step", methods=["POST"])
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

            # Si todos los pasos están aprobados → overall_status = approved
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
@app.route("/balance/<address>", methods=["GET"])
def balance(address):
    return jsonify({"address": address, "balance": blockchain.get_balance(address)})


# ============================================================
#   TRANSACCIÓN FIRMADA
# ============================================================
@app.route("/send_tx", methods=["POST"])
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
@app.route("/commit", methods=["POST"])
def commit():
    block = blockchain.commit_pending_transactions()
    if block is None:
        return jsonify({"error": "No hay transacciones"}), 400
    return jsonify({"message": "Bloque creado", "index": block.index})


# ============================================================
#   VER BLOCKCHAIN
# ============================================================
@app.route("/chain", methods=["GET"])
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
@app.route("/admin/users", methods=["GET"])
@require_admin
def admin_users():
    db = load_db()
    return jsonify(db["users"])


@app.route("/admin/transactions", methods=["GET"])
@require_admin
def admin_transactions():
    txs = []
    for block in blockchain.chain:
        for tx in block.transactions:
            txs.append(tx)
    return jsonify(txs)


@app.route("/admin/blocks", methods=["GET"])
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
#   INICIAR SERVIDOR
# ============================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7777, debug=True)
