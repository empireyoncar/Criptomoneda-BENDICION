FROM python:3.10-slim

WORKDIR /app

# Copiar TODO el backend staking dentro del contenedor
COPY . /app/backend

# Instalar dependencias
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Exponer puertos
EXPOSE 5006
EXPOSE 5007

# Comando por defecto (API + WEB)
CMD ["sh", "-c", "python /app/backend/staking_server.py & python /app/backend/staking_recompensa.py"]
