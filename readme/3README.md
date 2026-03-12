📘 README – Criptomoneda BENDICIÓN
Sistema blockchain + wallets + KYC + panel admin + Docker

🚀 Descripción del proyecto
Criptomoneda BENDICIÓN es una plataforma blockchain completa que incluye:

Blockchain propia

Wallets generadas en navegador

Transacciones firmadas con ECDSA

Sistema de usuarios (registro/login)

KYC profesional en 4 pasos

Panel administrador

Base de datos persistente

Despliegue con Docker

Plantillas HTML para panel admin

El proyecto está diseñado para ser simple, educativo y funcional, permitiendo entender cómo funciona una criptomoneda desde cero.

📁 Estructura del proyecto (completa y real)
Código
Criptomoneda-BENDICION/
│
├── __pycache__/                     # Caché de Python
│   ├── blockchain.cpython-314.pyc
│   ├── database.cpython-314.pyc
│   └── node.cpython-314.pyc
│
├── .github/                         # Configuración GitHub Actions
│   └── workflows/
│       └── deploy.yml
│
├── kyc_docs/                        # Archivos KYC subidos (persistentes)
│
├── templates/                       # Plantillas usadas por admin_server.py
│   ├── admin.html
│   └── login.html
│
├── 1 PROYECTO.md                    # Documentación interna
├── 2 PROYECTO.md                    # Documentación interna
│
├── admin_kyc.html                   # Panel admin KYC (frontend)
├── admin_server.py                  # Servidor admin (Flask)
├── blockchain.py                    # Lógica blockchain
├── database.json                    # Base de datos persistente
├── database.py                      # Lógica de usuarios + KYC
├── docker-compose.yml               # Orquestación Docker
├── Dockerfile                       # Imagen Docker
│
├── estado_kyc.html                  # Estado del KYC para el usuario
├── index.html                       # Wallet del usuario
├── KYC_aprobado.html                # Página final de aprobación
├── kyc.html                         # Verificación KYC por pasos
├── KYCtelefono.html                 # Verificación telefónica
├── login.html                       # Login
├── node.py                          # Backend principal (Flask)
├── register.html                    # Registro
└── wallet.py                        # Lógica de wallets
🧠 Componentes principales
🔗 1. Blockchain (blockchain.py)
Estructura de bloques

Transacciones

Validación básica

Commit manual de bloques

👤 2. Sistema de usuarios (database.py + node.py)
Registro nivel 3

Login con SHA256

Asociación de wallet

Persistencia en JSON

🪪 3. Sistema KYC profesional
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

Archivos relacionados:
kyc.html

estado_kyc.html

KYC_aprobado.html

admin_kyc.html

kyc_docs/

🛠 4. Panel administrador
Servidor:
admin_server.py (Flask, puerto 8888)

Plantillas:
templates/admin.html

templates/login.html

Funciones:
Ver usuarios

Ver transacciones

Ver bloques

Aprobar/rechazar KYC

🐳 5. Docker
✔ Dockerfile
Construye una imagen con:

Python 3.10

Flask

Flask-CORS

ECDSA

WerkZeug

✔ docker-compose.yml
Levanta dos servicios:

Servicio	Puerto	Archivo
backend	7777	node.py
admin	8888	admin_server.py
✔ Persistencia garantizada
Los datos NO se pierden al borrar contenedores.

yaml
volumes:
  - ./database.json:/app/database.json
  - ./kyc_docs:/app/kyc_docs
Esto asegura:

La base de datos vive fuera del contenedor

Los documentos KYC viven fuera del contenedor

Puedes borrar contenedores sin perder nada

✔ Levantar servicios
Código
docker compose up -d
✔ Ver logs
Código
docker compose logs -f
✔ Reiniciar
Código
docker compose restart
✔ Detener sin borrar datos
Código
docker compose down
🌐 6. Endpoints principales
Usuario
Método	Endpoint	Descripción
POST	/register	Registrar usuario
POST	/login	Login
GET	/user_wallet/	Obtener wallet
POST	/link_wallet	Asociar wallet
GET	/balance/
Ver balance
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
🔒 7. Persistencia de datos
❗ Importante:
Los datos NO se borran al eliminar contenedores porque:

database.json está montado como volumen local

kyc_docs/ también está montado como volumen local

Solo se perderían si tú los borras manualmente.

🧩 8. Requisitos
Python 3.10

Docker + Docker Compose

Navegador moderno

🧪 9. Cómo probar
Backend:

Código
http://localhost:7777
Admin:

Código
http://localhost:8888
Frontend:
Abrir los archivos HTML directamente o servirlos con un servidor estático.

🧱 10. Próximas mejoras
Minería PoW

JWT

Dashboard admin

API pública

Encriptación avanzada

Modo oscuro completo

🎉 11. Autor
Proyecto desarrollado por Jonatan  
Asistido por Copilot.