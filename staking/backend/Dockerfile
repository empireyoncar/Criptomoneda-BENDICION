FROM python:3.10-slim

# -----------------------------
#   WORKDIR
# -----------------------------
WORKDIR /app

# -----------------------------
#   DEPENDENCIAS
# -----------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# -----------------------------
#   COPIAR TODO EL MÓDULO
# -----------------------------
COPY backend /app/backend
COPY frontend /app/frontend

# Crear carpeta DB
RUN mkdir -p /app/db

# -----------------------------
#   EXPONER PUERTOS
# -----------------------------
EXPOSE 5006
EXPOSE 5007

# -----------------------------
#   ENTRYPOINT: API + WEB
# -----------------------------
CMD ["sh", "-c", "python backend/staking_server.py & python backend/staking_webserver.py"]
