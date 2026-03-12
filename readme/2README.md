📄 PROYECTO.md (versión actualizada 2026)
Documentación oficial del proyecto BENDICIÓN

#️⃣ 1. Descripción general del proyecto

BENDICIÓN es una plataforma cripto completa que integra:

🔗 Blockchain propia
Bloques sin minería (PoW pendiente)

Transacciones firmadas con ECDSA

Wallets generadas en el navegador

Validación de firmas en backend

Commit de bloques manual

👤 Sistema de usuarios
Registro nivel 3 (datos personales completos)

Login con SHA256

Asociación automática de wallet

Gestión de sesiones vía localStorage

🪪 Sistema KYC profesional
Subida de documentos por paso

Estados por paso: pending / submitted / approved / rejected

Verificación telefónica vía WhatsApp

Panel admin para aprobar/rechazar cada paso

Página de estado KYC para el usuario

Página final “KYC aprobado”

🛠 Panel administrador
Gestión de usuarios

Gestión de wallets

Gestión de transacciones

Gestión de bloques

Gestión completa de KYC

🗄 Base de datos
JSON persistente

Estructura moderna por usuario

KYC estructurado por pasos

#️⃣ 2. Estructura del proyecto

Código
/bendicion
│
├── node.py               # Backend Flask
├── blockchain.py
├── wallet.py
├── database.py
├── database.json
│
├── kyc_docs/             # Archivos KYC subidos
│
├── index.html            # Wallet del usuario
├── login.html
├── register.html
├── kyc.html              # Verificación KYC por pasos
├── KYCtelefono.html      # Verificación telefónica
├── estado_kyc.html       # Estado del KYC para el usuario
├── KYC_aprobado.html     # Página final de aprobación
│
└── admin_kyc.html        # Panel admin KYC
#️⃣ 3. Backend (node.py)  
El backend está construido con Flask y expone endpoints REST.

✔ Endpoints de usuario
Método	Endpoint	Descripción
POST	/register	Registrar usuario nivel 3
POST	/login	Iniciar sesión
GET	/user_wallet/	Obtener wallet del usuario
POST	/link_wallet	Asociar wallet
GET	/balance/
Ver balance
POST	/send_tx	Enviar transacción firmada
POST	/commit	Crear bloque
GET	/chain	Ver blockchain
✔ Endpoints de KYC (nuevos y actualizados)
Método	Endpoint	Descripción
POST	/upload_kyc_step	Subir documento por paso (id, domicilio, selfie)
POST	/update_kyc_status	Cambiar estado de un paso
GET	/get_kyc_status/	Obtener estado completo del KYC
POST	/update_phone_verification	Marcar paso 4 como enviado
✔ Endpoints de administrador
Método	Endpoint	Descripción
GET	/admin/users	Ver todos los usuarios
GET	/admin/transactions	Ver todas las transacciones
GET	/admin/blocks	Ver todos los bloques
POST	/admin/kyc/approve_step	Aprobar un paso del KYC
#️⃣ 4. Base de datos (database.json)  
Cada usuario tiene esta estructura:

json
{
  "id": "UUID",
  "fullname": "Nombre",
  "birthdate": "YYYY-MM-DD",
  "country": "País",
  "address": "Dirección",
  "phone": "Teléfono",
  "email": "correo",
  "password": "SHA256",
  "role": "user/admin",
  "wallets": ["address"],

  "kyc": {
    "id_document": {
      "file": null,
      "status": "pending"
    },
    "address_document": {
      "file": null,
      "status": "pending"
    },
    "selfie": {
      "file": null,
      "status": "pending"
    },
    "phone_verification": {
      "status": "pending"
    },
    "overall_status": "pending"
  }
}
#️⃣ 5. Lógica de wallets

Las wallets se generan en el navegador con elliptic.js

La dirección es:

Código
address = SHA256(publicKey)
El backend nunca recibe la clave privada

Cada usuario solo puede tener 1 wallet

#️⃣ 6. Lógica de transacciones

Firmadas con ECDSA en el navegador

El backend valida:

Firma

Address

Saldo

Se agregan a pending_transactions

/commit crea un bloque nuevo

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
No hay minería (PoW) aún.

#️⃣ 8. Frontend

✔ register.html
Formulario de registro nivel 3.

✔ login.html
Guarda user_id en localStorage.

✔ index.html
Ver wallet

Crear wallet

Ver balance

Enviar transacciones

Ver transacciones

Ver blockchain

Acceso al KYC

✔ kyc.html (actualizado)
Subida de documentos por paso

Estados reales desde backend

Miniaturas reales

Paso 4 → WhatsApp

Barra de progreso real

✔ KYCtelefono.html
Abre WhatsApp automáticamente

Instrucciones de verificación telefónica

✔ estado_kyc.html
Muestra estados reales del KYC

Miniaturas

Mensaje final según estado

Redirección opcional a KYC_aprobado.html

✔ KYC_aprobado.html
Página final cuando el KYC está aprobado.

✔ admin_kyc.html
Panel profesional para administradores:

Ver usuarios

Ver KYC por usuario

Ver archivos subidos

Aprobar o rechazar pasos

Estado general del KYC

#️⃣ 9. TODO (pendiente)

🔧 Mejoras técnicas
Implementar minería real (PoW)

Recompensas por bloque

Supply total

Quema de tokens

Mempool avanzada

🎨 Mejoras visuales
Dashboard con gráficas (Chart.js)

UI/UX más moderna

🔐 Seguridad
JWT

Sesiones seguras

Encriptar claves privadas

2FA para admin

🌐 API pública
Documentación estilo Swagger

API para desarrolladores externos

#️⃣ 10. Cómo continuar el desarrollo

Cuando quieras seguir, solo dime:

👉 “Aquí está PROYECTO.md, continuemos con X módulo”

Y seguimos exactamente donde lo dejamos.