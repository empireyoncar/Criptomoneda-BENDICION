# Imagen base con Python 3.11
FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Copiar todos los archivos del proyecto al contenedor
COPY . /app

# Instalar dependencias necesarias
RUN pip install --no-cache-dir flask flask-cors ecdsa rsa

# Exponer el puerto que usará Flask
EXPOSE 7777

# Comando para iniciar el nodo
CMD ["python", "global_node.py"]
