# wallet.py
from ecdsa import SigningKey, SECP256k1
from hashlib import sha256
import json


def generate_wallet():
    """
    Genera:
    - clave privada (hex)
    - clave pública (hex)
    - address (hex derivada de la clave pública)
    """
    sk = SigningKey.generate(curve=SECP256k1)
    vk = sk.get_verifying_key()

    private_key = sk.to_string().hex()
    public_key = vk.to_string().hex()

    # Address simple: hash de la clave pública
    address = sha256(bytes.fromhex(public_key)).hexdigest()

    return {
        "private_key": private_key,
        "public_key": public_key,
        "address": address
    }


def sign_transaction(private_key_hex, tx_dict):
    """
    Firma una transacción (dict) con la clave privada.
    Devuelve la firma en hex.
    """
    sk = SigningKey.from_string(bytes.fromhex(private_key_hex), curve=SECP256k1)

    tx_string = json.dumps(tx_dict, sort_keys=True).encode()
    tx_hash = sha256(tx_string).digest()

    signature = sk.sign(tx_hash)
    return signature.hex()
