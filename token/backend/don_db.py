import os
import time
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor


DB_HOST = os.getenv("DON_DB_HOST", "don_db")
DB_PORT = int(os.getenv("DON_DB_PORT", "5548"))
DB_NAME = os.getenv("DON_DB_NAME", "don_db")
DB_USER = os.getenv("DON_DB_USER", "don_user")
DB_PASSWORD = os.getenv("DON_DB_PASSWORD", "don_password")
SCHEMA_PATH = os.getenv("DON_DB_SCHEMA_PATH", "/app/don_schema.sql")


@contextmanager
def get_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def transaction():
    with get_connection() as conn:
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise


def ensure_schema(retries=20, delay_seconds=2):
    last_error = None
    for _ in range(retries):
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
                        cur.execute(f.read())
                conn.commit()
            return
        except Exception as exc:
            last_error = exc
            time.sleep(delay_seconds)

    raise RuntimeError(f"No se pudo inicializar esquema DON: {last_error}")


def fetch_one(query, params=None):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params or ())
            row = cur.fetchone()
            return dict(row) if row else None


def fetch_all(query, params=None):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params or ())
            rows = cur.fetchall()
            return [dict(row) for row in rows]
