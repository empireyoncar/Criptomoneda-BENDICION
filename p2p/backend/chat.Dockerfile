FROM python:3.10-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    flask \
    flask-cors \
    flask-sock \
    psycopg2-binary \
    PyJWT \
    requests

EXPOSE 5014
