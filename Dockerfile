FROM python:3.10-slim

# Carpeta de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar SOLO el backend del servicio correspondiente
COPY . /app

# Instalar dependencias Python necesarias
RUN pip install --no-cache-dir flask flask-cors ecdsa werkzeug

# Crear carpetas necesarias
RUN mkdir -p /app/db
RUN mkdir -p /app/kyc_docs

# El CMD final lo define docker-compose
