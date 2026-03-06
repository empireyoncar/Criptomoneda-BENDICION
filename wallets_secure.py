# wallets_secure.py
import os
import hashlib
import json
import ecdsa
from cryptography.fernet import Fernet

WALLETS_DIR = "wallets_data"
os.makedirs(WALLETS_DIR, exist_ok=True)

def derive_key(password: str) -> bytes:
    """Deriva una clave de 32 bytes a partir de la contraseña"""
    return hashlib.sha256(password.encode()).digest()

class SecureWallet:
    def __init__(self, name):
        self.name = name
        self.private_key = None
        self.public_keys = []
        self.password = None

    # -------------------------
    # Crear wallet nueva
    # -------------------------
    def create_wallet(self, password: str):
        self.password = password
        self.private_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
        self.save_wallet()
        return self

    # -------------------------
    # Guardar wallet en disco cifrada
    # -------------------------
    def save_wallet(self):
        path = os.path.join(WALLETS_DIR, f"{self.name}.wallet")
        key = derive_key(self.password)
        fernet_key = Fernet(base64.urlsafe_b64encode(key))
        encrypted = fernet_key.encrypt(self.private_key.to_string())
        with open(path, "wb") as f:
            f.write(encrypted)

    # -------------------------
    # Cargar wallet existente
    # -------------------------
    def load_wallet(self, password: str):
        path = os.path.join(WALLETS_DIR, f"{self.name}.wallet")
        if not os.path.exists(path):
            raise FileNotFoundError("Wallet no encontrada")
        with open(path, "rb") as f:
            encrypted = f.read()
        key = derive_key(password)
        fernet_key = Fernet(base64.urlsafe_b64encode(key))
        decrypted = fernet_key.decrypt(encrypted)
        self.private_key = ecdsa.SigningKey.from_string(decrypted, curve=ecdsa.SECP256k1)
        self.password = password
        return self

    # -------------------------
    # Generar dirección pública
    # -------------------------
    def generate_address(self):
        vk = self.private_key.get_verifying_key()
        address = hashlib.sha256(vk.to_string()).hexdigest()
        self.public_keys.append(address)
        return address

    # -------------------------
    # Firmar mensaje/transacción
    # -------------------------
    def sign_message(self, message: str):
        return self.private_key.sign(message.encode()).hex()
