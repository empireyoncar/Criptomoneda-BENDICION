FROM python:3.10-slim

WORKDIR /app

# Dependencias Python del servicio
RUN pip install --no-cache-dir flask flask-cors requests

# Exponer puertos
EXPOSE 5006
EXPOSE 5007

# Comando por defecto (API + WEB)
CMD ["sh", "-c", "python /app/backend/staking_server.py & python /app/backend/staking_recompensa.py"]
