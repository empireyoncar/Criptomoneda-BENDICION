👉 “Aquí está PROYECTO.md, seguimos desde aquí.”

Y yo continuaré exactamente donde lo dejamos.

📄 PROYECTO.md
Documentación oficial del proyecto BENDICIÓN

#️⃣ 1. Descripción general del proyecto
BENDICIÓN es una plataforma cripto completa que incluye:

Blockchain propia

Wallets generadas en el navegador

Firma ECDSA

Transacciones firmadas

Bloques sin minería (por ahora)

Sistema de usuarios (registro/login)

Asociación usuario–wallet

KYC con subida de documentos

Panel de administrador

Gestión de usuarios, transacciones, bloques y KYC

El proyecto está dividido en:

Backend (Python + Flask)

Frontend (HTML + JS)

Base de datos (JSON)

#️⃣ 2. Estructura del proyecto
Código
/bendicion
│
├── node.py
├── blockchain.py
├── wallet.py
├── database.py
├── database.json
├── kyc_docs/        # documentos subidos
│
├── index.html       # wallet del usuario
├── login.html
├── register.html
└── admin.html       # panel administrador
#️⃣ 3. Backend (node.py)
✔ Endpoints de usuario
Método	Endpoint	Descripción
POST	/register	Registrar usuario
POST	/login	Iniciar sesión
GET	/user_wallet/	Obtener wallet del usuario
POST	/link_wallet	Asociar wallet al usuario
GET	/balance/
Ver balance
POST	/send_tx	Enviar transacción firmada
POST	/commit	Crear bloque
GET	/chain	Ver blockchain
✔ Endpoints de administrador
Método	Endpoint	Descripción
GET	/CriptoBendicion/admin_api/users	Ver todos los usuarios
GET	/admin/transactions	Ver todas las transacciones
GET	/admin/transactions/
Filtrar transacciones por address
GET	/admin/blocks	Ver todos los bloques
GET	/admin/stats	Estadísticas del sistema
GET	/admin/kyc/docs/	Ver documentos KYC
POST	/admin/kyc/approve	Aprobar KYC
POST	/admin/kyc/reject	Rechazar KYC
✔ Endpoints de KYC
Método	Endpoint	Descripción
POST	/upload_kyc	Subir documento KYC
#️⃣ 4. Base de datos (database.json)
Cada usuario tiene esta estructura:

json
{
  "id": "UUID",
  "email": "correo",
  "password": "SHA256",
  "role": "user/admin",
  "wallets": ["address"],
  "kyc": {
    "status": "pending/approved/rejected",
    "documents": ["archivo1.png", "archivo2.pdf"]
  }
}
#️⃣ 5. Lógica de wallets
Las wallets se generan en el navegador usando elliptic.js

La dirección es:
address = SHA256(publicKey)

El servidor solo registra la address, nunca la clave privada

Cada usuario solo puede tener 1 wallet

#️⃣ 6. Lógica de transacciones
Las transacciones se firman con ECDSA en el navegador

El backend verifica:

Que la address coincide con la clave pública

Que la firma es válida

Que el usuario tiene saldo

Las transacciones se guardan en pending_transactions

Al hacer /commit, se crea un bloque nuevo

#️⃣ 7. Lógica de bloques
Cada bloque contiene:

json
{
  "index": 1,
  "timestamp": 123456789,
  "transactions": [...],
  "previous_hash": "...",
  "hash": "..."
}
No hay minería aún (PoW), pero se puede agregar.

#️⃣ 8. Frontend
✔ register.html
Formulario de registro

Envía email + password

Redirige a login

✔ login.html
Formulario de login

Guarda user_id en localStorage

Redirige a index.html

✔ index.html (wallet del usuario)
Cargar wallet del usuario

Crear wallet (solo si no tiene)

Ver balance

Enviar transacciones firmadas

Ver transacciones del usuario

Subir documentos KYC

Crear bloques

Ver blockchain

✔ admin.html (panel administrador)
Incluye:

Gestión de usuarios
Ver todos los usuarios

Ver wallets

Ver claves públicas/privadas (si se guardan)

Ver estado KYC

Gestión de transacciones
Ver todas las transacciones

Filtrar por address

Gestión de bloques
Ver blockchain completa

Gestión de KYC
Ver documentos

Aprobar

Rechazar

Estadísticas del sistema
Número de usuarios

Número de wallets

Número de bloques

Supply total

Transacciones pendientes

Último bloque

#️⃣ 9. TODO (pendiente)
🔧 Mejoras técnicas
Implementar minería real (PoW)

Añadir recompensas por bloque

Añadir supply total y emisión controlada

Añadir quema de tokens

Añadir mempool avanzada

🎨 Mejoras visuales
Crear dashboard con gráficas (Chart.js)

Mejorar UI/UX

Añadir modo oscuro

🔐 Seguridad
Tokens JWT

Sesiones seguras

Encriptar claves privadas en localStorage

2FA para admin

🌐 API pública
Documentación estilo Swagger

API para desarrolladores externos

#️⃣ 10. Cómo continuar el desarrollo
Cuando quieras seguir, solo dime:

👉 “Aquí está PROYECTO.md, continuemos con X módulo”

Y yo retomaré exactamente donde lo dejamos.