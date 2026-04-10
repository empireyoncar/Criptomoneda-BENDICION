FROM python:3.10-slim

# Carpeta de trabajo
WORKDIR /app

# Dependencias Python del servicio
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Exponer puertos
EXPOSE 5008
EXPOSE 5009

# Comando por defecto
CMD ["python", "/app/token/don_webserver.py"]
