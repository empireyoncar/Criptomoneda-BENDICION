FROM python:3.10-slim

# Carpeta de trabajo
WORKDIR /app

# Dependencias Python del servicio
RUN pip install --no-cache-dir Flask flask-cors jinja2 waitress

# Exponer puertos
EXPOSE 5008
EXPOSE 5009

# Comando por defecto
CMD ["python", "/app/token/don_webserver.py"]
