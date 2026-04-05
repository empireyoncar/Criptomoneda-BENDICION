import json
import os

# Ruta base dentro del contenedor Docker
BASE_PATH = "/app/backend"

FILES = {
    "activos": os.path.join(BASE_PATH, "stakingactivos.json"),
    "completados": os.path.join(BASE_PATH, "stakingcompletados_history.json"),
    "cancelados": os.path.join(BASE_PATH, "stakingcancelados_history.json")
}

# ---------------------------------------------------------
# ASEGURAR QUE LOS ARCHIVOS EXISTEN
# ---------------------------------------------------------
for f in FILES.values():
    if not os.path.exists(f):
        with open(f, "w") as fp:
            json.dump([], fp)


# ---------------------------------------------------------
# FUNCIONES BASE
# ---------------------------------------------------------
def load_file(name):
    """Carga un archivo JSON de staking."""
    with open(FILES[name], "r") as f:
        return json.load(f)


def save_file(name, data):
    """Guarda un archivo JSON de staking."""
    with open(FILES[name], "w") as f:
        json.dump(data, f, indent=4)


# ---------------------------------------------------------
# AGREGAR NUEVO STAKING
# ---------------------------------------------------------
def add_staking(stake):
    activos = load_file("activos")
    activos.append(stake)
    save_file("activos", activos)


# ---------------------------------------------------------
# MOVER A COMPLETADOS
# ---------------------------------------------------------
def move_to_completed(stake_id):
    activos = load_file("activos")
    completados = load_file("completados")

    for s in activos:
        if s["stake_id"] == stake_id:
            activos.remove(s)
            completados.append(s)
            save_file("activos", activos)
            save_file("completados", completados)
            return True

    return False


# ---------------------------------------------------------
# MOVER A CANCELADOS
# ---------------------------------------------------------
def move_to_cancelled(stake_id):
    activos = load_file("activos")
    cancelados = load_file("cancelados")

    for s in activos:
        if s["stake_id"] == stake_id:
            activos.remove(s)
            cancelados.append(s)
            save_file("activos", activos)
            save_file("cancelados", cancelados)
            return True

    return False


# ---------------------------------------------------------
# OBTENER STAKING POR ID
# ---------------------------------------------------------
def get_stake(stake_id):
    activos = load_file("activos")
    for s in activos:
        if s["stake_id"] == stake_id:
            return s
    return None


# ---------------------------------------------------------
# LISTAR TODOS LOS STAKINGS ACTIVOS
# ---------------------------------------------------------
def list_activos():
    return load_file("activos")
