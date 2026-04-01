FROM python:3.10-slim

# Carpeta de trabajo
WORKDIR /app

# Copiar SOLO el módulo staking
COPY . /app/staking/backend

# Copiar módulos necesarios del proyecto principal
COPY ../../token /app/token
COPY ../../wallet /app/wallet

# Instalar dependencias del módulo staking
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Exponer puerto del servidor de staking
EXPOSE 5006

# Ejecutar el servidor principal de staking
CMD ["python", "/app/staking/backend/staking_server.py"]
