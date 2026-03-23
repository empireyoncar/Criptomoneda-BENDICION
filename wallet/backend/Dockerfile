# Imagen base de Python
FROM python:3.10-slim

# Crear carpeta de trabajo
WORKDIR /app

# Copiar requirements si algún día los usas
# (si no tienes requirements.txt, no pasa nada)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt || true

# Copiar todos los archivos del backend
COPY . /app

# Exponer el puerto del backend
EXPOSE 5002

# Comando por defecto (lo sobrescribe docker-compose)
CMD ["python", "wallet_server.py"]
