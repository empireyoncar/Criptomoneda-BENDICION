# Validación de Firmas Digitales en Blockchain

## Resumen
Todas las transacciones de usuarios (no SYSTEM) **deben estar firmadas con ECDSA** para ser aceptadas.

## Flujo Correcto de TX Firmada

### 1. Cliente Genera Wallet
```python
from wallet import generate_wallet

wallet = generate_wallet()
# {
#   "private_key": "hex_string",
#   "public_key": "hex_string", 
#   "address": "sha256_hash_de_public_key"
# }
```

### 2. Cliente Obtiene Nonce
```bash
GET /wallet/{address}/nonce
# Respuesta: {"address": "...", "nonce": 5}
```

### 3. Cliente Construye TX
```python
tx_data = {
    "from": wallet["address"],
    "to": "receiver_address",
    "amount": 1_000_000_000,  # satichis
    "nonce": 5,
    "tx_id": "optional_id",
    "metadata": {"memo": "compra"}
}
```

### 4. Cliente Firma TX
```python
from wallet import sign_transaction

signature = sign_transaction(wallet["private_key"], tx_data)
# signature = "hex_string_muy_largo"
```

### 5. Cliente Envía TX Completa
```bash
POST /send_tx
Content-Type: application/json

{
  "tx": {
    "from": "address_wallet",
    "to": "address_destino",
    "amount": 1_000_000_000,
    "nonce": 5,
    "tx_id": "optional",
    "metadata": {...},
    "public_key": "hex_public_key_usuario",
    "signature": "hex_firma_ecdsa"
  }
}
```

### 6. Blockchain Valida
```
✓ Contiene public_key y signature
✓ SHA256(public_key) == sender
✓ Firma valida para este payload
✓ Nonce es correcto
✓ Balance suficiente
→ TX ACEPTADA
```

---

## Validaciones en Servidor

### Paso 1: Verificar Existencia de Firma
```python
if sender != "SYSTEM":
    if not public_key or not signature:
        return "TX from user must include public_key and signature"
```

### Paso 2: Verificar que Address Corresponde a Public Key
```python
derived_address = SHA256(public_key)
assert derived_address == sender
```

### Paso 3: Verificar Firma ECDSA
```python
tx_for_verification = {
    "from": sender,
    "to": receiver,
    "amount": amount,
    "nonce": nonce,
    # ... otros campos
}
assert verificar_firma(tx_for_verification, signature, public_key)
```

---

## Seguridad

### ❌ Qué NO Protege
- Robo de private_key (es responsabilidad del usuario guardarla)
- Pérdida de private_key (no hay recuperación)
- Servidor hackeado (si no está protegido)

### ✅ Qué SÍ Protege
- **Transacción falsificada**: Alguien no puede inventar una TX sin la private_key
- **Transacción alterada**: Si alguien cambia `amount` o `receiver`, firma falla
- **Suplantación**: Sin la private_key, es imposible firmar como otro usuario
- **Replay**: Nonce + firma única = TX no puede reenviarse

---

## Ejemplo Completo (Python)

```python
import sys
sys.path.insert(0, "/app/wallet")
sys.path.insert(0, "/app/criptografia")

from wallet import generate_wallet, sign_transaction
import requests
import json

# 1. Generar wallet
wallet = generate_wallet()
print(f"Address: {wallet['address']}")

# 2. Obtener nonce
response = requests.get(f"http://blockchain:5004/wallet/{wallet['address']}/nonce")
nonce = response.json()["nonce"]

# 3. Construir TX
tx_data = {
    "from": wallet["address"],
    "to": "receiver_address_aqui",
    "amount": 500_000_000,  # 5 BENDICION
    "nonce": nonce,
    "tx_id": "tx_001"
}

# 4. Firmar TX
signature = sign_transaction(wallet["private_key"], tx_data)

# 5. Enviar TX con firma
tx_complete = {
    **tx_data,
    "public_key": wallet["public_key"],
    "signature": signature
}

response = requests.post(
    "http://blockchain:5004/send_tx",
    json={"tx": tx_complete}
)

print(response.json())
# {"message": "Transacción añadida", "tx_id": "tx_001"}
```

---

## Excepciones: SYSTEM Transactions

Las transacciones del SISTEMA (mint, airdrops, etc.) **NO requieren firma**:

```bash
POST /mint
Content-Type: application/json

{
  "address": "receiving_address",
  "amount": 1_000_000_000
}
```

Estas txs se agregan directamente.

---

## Troubleshooting

### "TX from user must include public_key and signature"
→ Faltan fields en la TX. Verifica que incluyas ambos.

### "Public key does not match sender address"
→ El address no corresponde a la public_key. Asegúrate que `SHA256(public_key) == address`.

### "Invalid signature"
→ La firma no valida. Posibles causas:
- Modificaste la TX después de firmar
- Usaste private_key diferente
- Signature está corrupta

### "Saldo insuficiente o nonce inválido"
→ O no hay saldo, o el nonce es incorrecto. Consulta `/wallet/{address}/nonce`.

