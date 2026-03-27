# ============================================================
# IMAGEN BASE
# Usamos Python 3.10 slim para un contenedor ligero y estable
# ============================================================
FROM python:3.10-slim

# ============================================================
# CONFIGURACIÓN DEL SISTEMA
# Instalamos dependencias necesarias para Python y librerías
# ============================================================
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# ============================================================
# DIRECTORIO DE TRABAJO
# Todo el backend se ejecutará dentro de /app
# ============================================================
WORKDIR /app

# ============================================================
# COPIAR ARCHIVOS DEL BACKEND
# Copiamos TODO el contenido de la carpeta backend al contenedor
# ============================================================
COPY . /app

# ============================================================
# INSTALAR DEPENDENCIAS PYTHON
# Usamos requirements.txt si existe, si no instalamos manualmente
# ============================================================
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt || \
    pip install --no-cache-dir flask flask-cors requests ecdsa

# ============================================================
# PUERTOS EXPUESTOS
# admin_api usa 5010
# admin_web usa 5011
# ============================================================
EXPOSE 5010
EXPOSE 5011

# ============================================================
# COMANDO POR DEFECTO
# docker-compose lo sobrescribe con:
#   command: python admin_server.py
# o
#   command: python admin_webserver.py
# ============================================================
CMD ["python", "admin_server.py"]
