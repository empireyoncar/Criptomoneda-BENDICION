# Imagen base de Python
FROM python:3.10-slim

# Crear carpeta de trabajo
WORKDIR /app

RUN pip install --no-cache-dir Flask==2.3.2 ecdsa==0.18.0 flask_cors requests psycopg2-binary==2.9.10

# Exponer el puerto del backend
EXPOSE 5002

# Comando por defecto (lo sobrescribe docker-compose)
CMD ["python", "wallet_server.py"]
