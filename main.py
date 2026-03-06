# main.py
from wallets import Wallet

# Crear una wallet
alice_wallet = Wallet("Alice")
print("Clave privada de Alice:", alice_wallet.get_private_key())

# Generar varias direcciones públicas
addr1 = alice_wallet.generate_public_key()
addr2 = alice_wallet.generate_public_key()
print("Direcciones públicas de Alice:", alice_wallet.get_public_keys())

# Firmar mensaje
message = "Enviar 10 monedas"
signature = alice_wallet.sign_message(message)
print("Firma:", signature)

# Verificar firma
print("Verificación:", alice_wallet.verify_signature(message, signature))
