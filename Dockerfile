FROM python:3.10-slim

# Crear carpeta de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos del proyecto
COPY *.py /app
COPY db /app/db

# Instalar dependencias Python
RUN pip install --no-cache-dir flask flask-cors ecdsa werkzeug

# Crear carpetas necesarias
RUN mkdir -p kyc_docs

# Exponer puertos (node.py = 7777, admin_server.py = 8888)
EXPOSE 7777
EXPOSE 8888

# El comando final se define en docker-compose
CMD ["python", "node.py"]
