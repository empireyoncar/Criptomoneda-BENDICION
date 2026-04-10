FROM python:3.11-slim

WORKDIR /app

# Copiar requirements e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# El código real llega por volumen en docker-compose
CMD ["python", "seguridad/backend/seguridad_server.py"]
