import time

from don_db import ensure_schema, fetch_one, transaction


DON_VALUE_KEY = "don_value"


def _ensure_don_value_row():
    ensure_schema()
    with transaction() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO don_settings (setting_key, setting_value, updated_timestamp)
                VALUES (%s, %s, %s)
                ON CONFLICT (setting_key) DO NOTHING
                """,
                (DON_VALUE_KEY, 1.0, int(time.time())),
            )


def get_don_value() -> float:
    """Obtiene el valor actual de DON en BENDICIÓN."""
    _ensure_don_value_row()
    row = fetch_one(
        "SELECT setting_value FROM don_settings WHERE setting_key = %s LIMIT 1",
        (DON_VALUE_KEY,),
    )
    return float(row["setting_value"]) if row else 1.0


def set_don_value(new_value: float):
    """Actualiza el valor de DON en BENDICIÓN."""
    _ensure_don_value_row()
    with transaction() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE don_settings
                SET setting_value = %s, updated_timestamp = %s
                WHERE setting_key = %s
                """,
                (float(new_value), int(time.time()), DON_VALUE_KEY),
            )
