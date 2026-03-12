📘 README – Criptomoneda BENDICIÓN
Sistema blockchain + wallets reales + KYC + panel admin + Docker

🚀 Descripción del proyecto
Criptomoneda BENDICIÓN es una plataforma blockchain educativa y funcional que integra:

Blockchain propia

Wallets reales generadas en backend (ECDSA SECP256k1)

Transacciones firmadas

Sistema de usuarios (registro/login)

KYC profesional en 4 pasos

Panel administrador completo

Base de datos persistente

Despliegue con Docker

Frontend HTML simple y directo

El objetivo es ofrecer un proyecto realista, didáctico y modular, mostrando cómo funciona una criptomoneda desde cero.

📁 Estructura del proyecto (completa y real)
Código
Criptomoneda-BENDICION/
│
├── __pycache__/
│
├── .github/workflows/
│   └── deploy.yml
│
├── kyc_docs/                     # Archivos KYC persistentes
│
├── templates/                    # Plantillas del panel admin
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
└── wallet_manager.py             # Gestión y almacenamiento de wallets
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
Este proyecto ahora usa wallets reales generadas en backend, igual que Ethereum.

✔ Generación en wallet.py
Usa ECDSA SECP256k1 para generar:

Clave privada real

Clave pública

Dirección (SHA-256 de la clave pública)

✔ Almacenamiento separado
database.json
Guarda solo datos del usuario:

json
"wallets": [
  "direccion_wallet_real"
]
wallets.json
Guarda wallets completas:

json
{
  "wallets": [
    {
      "user_id": "03a4061b-86a3-456b-b7f8-0d20632da61f",
      "private_key": "hex...",
      "public_key": "hex...",
      "address": "hex..."
    }
  ]
}
✔ Gestión en wallet_manager.py
Genera wallet real

La guarda en wallets.json

Inserta la dirección en database.json

Devuelve la wallet al frontend

✔ Frontend actualizado (index.html)
El botón “Crear wallet” ahora:

Verifica si el usuario ya tiene wallet

Llama al backend con POST

Muestra la wallet real

Guarda la clave privada en localStorage

Código final:

js
document.getElementById("btnCreateWallet").onclick = async () => {

    const res = await fetch(`${API}/user_wallet/${userId}`);
    const data = await res.json();

    if (data.wallet) {
        alert("Ya tienes una wallet asociada.");
        return;
    }

    const res2 = await fetch(`${API}/generate_wallet`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId })
    });

    const wallet = await res2.json();

    document.getElementById("address").textContent = wallet.address;
    document.getElementById("publicKey").textContent = wallet.public_key;
    document.getElementById("privateKey").textContent = wallet.private_key;

    localStorage.setItem("private_key", wallet.private_key);
    localStorage.setItem("public_key", wallet.public_key);
    localStorage.setItem("address", wallet.address);

    alert("Wallet creada y guardada correctamente.");
};
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
✔ Servicios:
Servicio	Puerto	Archivo
backend	7777	node.py
admin	8888	admin_server.py
✔ Persistencia:
yaml
volumes:
  - ./database.json:/app/database.json
  - ./kyc_docs:/app/kyc_docs
✔ Comandos:
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
GET	/user_wallet/	Obtener wallet
POST	/generate_wallet	Crear wallet real
GET	/balance/	Ver balance
POST	/send_tx	Enviar transacción
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
Los datos NO se pierden al borrar contenedores porque:

database.json está montado como volumen

wallets.json también puede montarse

kyc_docs/ es persistente

🧩 9. Requisitos
Python 3.10

Docker + Docker Compose

Navegador moderno

🧪 10. Cómo probar
Backend:

Código
http://localhost:7777
Admin:

Código
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