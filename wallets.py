# wallets.py
import hashlib
import ecdsa  # pip install ecdsa

class Wallet:
    def __init__(self, name, private_key=None):
        """
        name: nombre de la wallet
        private_key: opcional, si quieres cargar una clave privada existente
        """
        self.name = name
        if private_key:
            self.private_key = ecdsa.SigningKey.from_string(bytes.fromhex(private_key), curve=ecdsa.SECP256k1)
        else:
            self.private_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
        self.public_keys = []  # lista de direcciones públicas generadas

    def generate_public_key(self):
        """Genera una nueva dirección pública y la agrega a la wallet"""
        vk = self.private_key.get_verifying_key()
        public_key_bytes = vk.to_string() + len(self.public_keys).to_bytes(1, 'big')  # diferenciación para múltiples direcciones
        address = hashlib.sha256(public_key_bytes).hexdigest()
        self.public_keys.append(address)
        return address

    def get_private_key(self):
        """Devuelve la clave privada en hexadecimal"""
        return self.private_key.to_string().hex()

    def get_public_keys(self):
        """Devuelve todas las direcciones públicas generadas"""
        return self.public_keys

    def sign_message(self, message):
        """Firma un mensaje con la clave privada"""
        return self.private_key.sign(message.encode()).hex()

    def verify_signature(self, message, signature):
        """Verifica una firma dada un mensaje y su firma"""
        vk = self.private_key.get_verifying_key()
        try:
            return vk.verify(bytes.fromhex(signature), message.encode())
        except:
            return False
