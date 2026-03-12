📘 README – Criptomoneda BENDICIÓN
Sistema blockchain + wallets reales + KYC + panel admin + Docker

🚀 Descripción del proyecto
Criptomoneda BENDICIÓN es una plataforma blockchain educativa y funcional que integra:

Blockchain propia

Wallets reales generadas en backend (ECDSA SECP256k1)

Transacciones firmadas digitalmente

Sistema de usuarios (registro/login)

KYC profesional en 4 pasos

Panel administrador completo

Base de datos persistente

Despliegue con Docker

Frontend HTML simple y directo

El objetivo es ofrecer un proyecto realista, modular y didáctico que muestre cómo funciona una criptomoneda desde cero.

📁 Estructura del proyecto
Código
Criptomoneda-BENDICION/
│
├── kyc_docs/                     # Archivos KYC persistentes
│
├── templates/                    # Panel admin
│   ├── admin.html
│   └── login.html
│
├── admin_kyc.html                # Panel admin KYC
├── admin_server.py               # Servidor admin (Flask)
├── blockchain.py                 # Lógica blockchain
├── database.json                 # Base de datos de usuarios
├── database.py                   # Registro, login, KYC
├── docker-compose.yml            # Orquestación Docker
├── Dockerfile                    # Imagen Docker
│
├── estado_kyc.html               # Estado del KYC
├── index.html                    # Wallet del usuario
├── KYC_aprobado.html             # Pantalla final
├── kyc.html                      # KYC paso a paso
├── KYCtelefono.html              # Verificación telefónica
├── login.html                    # Login
├── node.py                       # Backend principal
├── register.html                 # Registro
│
├── wallet.py                     # Generación y firma de wallets reales
├── wallet_manager.py             # Gestión y almacenamiento de wallets
└── wallets.json                  # Almacenamiento seguro de wallets
🧠 Componentes principales
🔗 1. Blockchain (blockchain.py)
Estructura de bloques

Transacciones

Validación

Commit manual de bloques

Consulta de chain

👤 2. Sistema de usuarios (database.py + node.py)
Registro con SHA256

Login

KYC integrado

Persistencia en JSON

Asociación de wallets reales

🔐 3. Sistema de Wallets Reales (Actualización 2026)
El proyecto usa wallets reales generadas en backend con ECDSA SECP256k1, igual que Ethereum.

✔ Generación (wallet.py)
Produce:

Clave privada real (hex)

Clave pública (hex)

Dirección = SHA-256(public_key)

✔ Almacenamiento separado
database.json  
Guarda solo la dirección:

json
"wallets": [
  "direccion_wallet_real"
]
wallets.json  
Guarda la wallet completa:

json
{
  "wallets": [
    {
      "user_id": "03a4061b...",
      "private_key": "hex...",
      "public_key": "hex...",
      "address": "hex..."
    }
  ]
}
✔ Gestión (wallet_manager.py)
Genera wallet

La guarda en wallets.json

Inserta la dirección en database.json

Devuelve la wallet al frontend

✔ Nueva ruta añadida (2026)
python
@app.route("/wallet_info/<address>", methods=["GET"])
def wallet_info(address):
    with open("wallets.json") as f:
        data = json.load(f)

    for w in data.get("wallets", []):
        if w["address"] == address:
            return jsonify(w)
    return jsonify({"error": "Wallet not found"}), 404
🪪 4. Sistema KYC profesional
Pasos:

Documento de identidad

Comprobante de domicilio

Selfie

Verificación telefónica

Estados:

pending

submitted

approved

rejected

Archivos:

kyc.html

estado_kyc.html

KYC_aprobado.html

admin_kyc.html

kyc_docs/

🛠 5. Panel administrador
Servidor:
admin_server.py (Flask, puerto 8888)

Funciones:

Ver usuarios

Ver transacciones

Ver bloques

Aprobar/rechazar KYC

🐳 6. Docker
Servicios:

Servicio	Puerto	Archivo
backend	7777	node.py
admin	8888	admin_server.py
Persistencia:

yaml
volumes:
  - ./database.json:/app/database.json
  - ./wallets.json:/app/wallets.json
  - ./kyc_docs:/app/kyc_docs
Comandos:

Código
docker compose up -d
docker compose logs -f
docker compose restart
docker compose down
🌐 7. Endpoints principales
Usuario
Método	Endpoint	Descripción
POST	/register	Registrar usuario
POST	/login	Login
GET	/user_wallet/	Obtener wallet asociada
GET	/wallet_info/
Obtener wallet completa
POST	/generate_wallet	Crear wallet real
GET	/balance/
Ver balance
POST	/send_tx	Enviar transacción firmada
POST	/commit	Crear bloque
GET	/chain	Ver blockchain
KYC
Método	Endpoint	Descripción
POST	/upload_kyc_step	Subir documento
POST	/update_kyc_status	Cambiar estado
GET	/get_kyc_status/	Estado completo
POST	/update_phone_verification	Paso 4
Admin
Método	Endpoint	Descripción
GET	/admin/users	Ver usuarios
GET	/admin/transactions	Ver transacciones
GET	/admin/blocks	Ver bloques
POST	/admin/kyc/approve_step	Aprobar paso
🔒 8. Persistencia de datos
Los datos NO se pierden al borrar contenedores:

database.json → volumen

wallets.json → volumen

kyc_docs/ → persistente

🧩 9. Requisitos
Python 3.10

Docker + Docker Compose

Navegador moderno

🧪 10. Cómo probar
Backend:
http://localhost:7777

Admin:
http://localhost:8888

Frontend:
Abrir los archivos HTML directamente.

🧱 11. Próximas mejoras
Minería PoW

JWT

Dashboard admin

API pública

Encriptación avanzada

Modo oscuro completo

🎉 12. Autor
Proyecto desarrollado por Jonatan  
Asistido por Copilot