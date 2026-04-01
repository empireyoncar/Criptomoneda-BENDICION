import json
import os

VALUE_FILE = "/app/don_value.json"


def _init_value():
    """Crea el archivo don_value.json si no existe."""
    if not os.path.exists(VALUE_FILE):
        with open(VALUE_FILE, "w") as f:
            json.dump({"don_value": 1.0}, f, indent=4)


def get_don_value() -> float:
    """Obtiene el valor actual de DON en BENDICIÓN."""
    _init_value()
    with open(VALUE_FILE, "r") as f:
        data = json.load(f)
        return float(data.get("don_value", 1.0))


def set_don_value(new_value: float):
    """Actualiza el valor de DON en BENDICIÓN."""
    _init_value()
    with open(VALUE_FILE, "w") as f:
        json.dump({"don_value": float(new_value)}, f, indent=4)
