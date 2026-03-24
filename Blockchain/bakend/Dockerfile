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
# Copiamos TODO el contenido de la carpeta bakend al contenedor
# ============================================================
COPY . /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# ============================================================
# INSTALAR DEPENDENCIAS PYTHON
# Si tienes un requirements.txt, se instala aquí
# Si no lo tienes, instalamos solo lo necesario
# ============================================================

# Si tu blockchain usa otras librerías, agrégalas aquí:
# RUN pip install --no-cache-dir ecdsa
# RUN pip install --no-cache-dir flask-cors

# ============================================================
# PUERTO POR DEFECTO
# El servidor blockchain usa el puerto 5004 o 5005 según el servicio
# ============================================================
EXPOSE 5004
EXPOSE 5005

# ============================================================
# COMANDO POR DEFECTO
# El compose lo sobrescribe con:
#   command: python blockchain_server.py
# o
#   command: python blockchain_webserver.py
# ============================================================
CMD ["python", "blockchain_server.py"]
