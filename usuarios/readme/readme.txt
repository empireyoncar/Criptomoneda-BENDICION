📘 README – Módulo de Usuarios – Criptomoneda BENDICIÓN
El módulo USUARIOS es el componente encargado de gestionar:

Registro de usuarios

Inicio de sesión

Gestión de wallets

Sistema de KYC

Roles (admin / user)

Interfaz de login y registro

Persistencia en JSON

API REST con Flask

Este módulo funciona como un microservicio independiente dentro del ecosistema Criptomoneda BENDICIÓN.

🏗️ 1. Estructura del módulo
Código
usuarios/
│
├── backend/
│   ├── login_server.py      → Servidor Flask (API)
│   ├── database.py          → Lógica de base de datos JSON
│   └── database.json        → Base de datos local
│
└── frontend/
    ├── login.html           → Interfaz de inicio de sesión
    └── register.html        → Interfaz de registro
🌐 2. Backend (Flask)
El backend expone una API REST que maneja:

✔ Registro
POST /register

Guarda:

Datos personales

Contraseña hasheada

Estructura KYC

Wallets (vacía al inicio)

Rol por defecto: user

✔ Login
POST /login

Devuelve:

Código
{ "user_id": "xxxx" }
✔ Obtener wallet
GET /wallet/<user_id>

Devuelve la wallet del usuario (si existe).

✔ Añadir wallet
POST /wallet/add

Permite asignar solo una wallet por usuario.

🗂️ 3. Base de datos (database.json)
El módulo usa un archivo JSON como almacenamiento local.

Estructura de cada usuario:

json
{
  "id": "uuid",
  "fullname": "Nombre",
  "birthdate": "YYYY-MM-DD",
  "country": "País",
  "address": "Dirección",
  "phone": "Teléfono",
  "email": "Correo",
  "password": "hash_sha256",
  "role": "user/admin",
  "wallets": ["direccion_wallet"],
  "kyc": {
    "id_document": { "file": null, "status": "pending" },
    "address_document": { "file": null, "status": "pending" },
    "selfie": { "file": null, "status": "pending" },
    "phone_verification": { "status": "pending" },
    "overall_status": "pending"
  }
}
🧠 4. Lógica interna (database.py)
Este archivo maneja toda la lógica del módulo:

✔ register_user()
Verifica email duplicado

Genera UUID

Hashea contraseña

Crea estructura KYC

Guarda en JSON

✔ login_user()
Compara email + hash

Devuelve user_id si coincide

✔ add_wallet_to_user()
Solo permite 1 wallet

Guarda cambios

✔ get_user_wallet()
Devuelve la wallet del usuario

✔ save_kyc_document()
Guarda archivos KYC

Cambia estado a submitted

✔ is_admin()
Verifica si un usuario tiene rol admin

🖥️ 5. Frontend
El módulo incluye dos interfaces HTML:

🔐 login.html
Funciones:

Validación de email y contraseña

Envío al endpoint /login

Manejo de errores del backend

Guarda user_id en localStorage

Redirige a /CriptoBendicion/home

Incluye:

Modo claro/oscuro

Animación de partículas

Estilo moderno

📝 register.html
Funciones:

Validación de todos los campos

Confirmación de contraseña

Envío al endpoint /register

Manejo de errores del backend

Redirección automática al login

Incluye:

Modo claro/oscuro

Animación de partículas

Estilo moderno

🔐 6. Seguridad del módulo
Contraseñas hasheadas con SHA‑256

No se guardan contraseñas en texto plano

No se exponen datos sensibles

Validación en backend y frontend

JSON protegido dentro del contenedor Docker

🔄 7. Flujo completo del usuario
1. Usuario abre register.html
→ Completa datos
→ Se envía a /register

2. Backend crea usuario
→ Guarda en JSON
→ Devuelve user_id

3. Usuario inicia sesión
→ En login.html  
→ Se envía a /login

4. Backend valida
→ Devuelve user_id

5. Frontend guarda user_id
→ Redirige al home

🧱 8. Integración con Docker y NGINX
El módulo funciona detrás de NGINX bajo:

Código
/CriptoBendicion/usuarios/
Ejemplos:

/CriptoBendicion/usuarios/login

/CriptoBendicion/usuarios/register

/CriptoBendicion/usuarios/wallet/<id>

NGINX redirige internamente al puerto 5001 del contenedor.

🟩 9. Estado del módulo
Todos los archivos revisados:

✔ backend

✔ base de datos

✔ frontend

✔ rutas

✔ lógica

✔ integración

Están correctos, funcionales y sin errores.

🎯 10. Objetivo del módulo
El módulo USUARIOS proporciona:

Identidad digital

Seguridad

Wallet única

KYC completo

Acceso al ecosistema

Base para el panel admin

Base para el sistema de staking

Es el núcleo de autenticación del ecosistema BENDICIÓN.