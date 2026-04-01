FROM python:3.10-slim

# Carpeta de trabajo
WORKDIR /app

# Copiar todo el proyecto token
COPY . /app/token

# Instalar dependencias
COPY token/backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Exponer puertos
EXPOSE 5008
EXPOSE 5009

# Comando por defecto: iniciar el servidor web DON
# Puedes cambiarlo al backend si quieres
CMD ["python", "/app/token/backend/don_webserver.py"]
