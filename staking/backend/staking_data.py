import glob
import json
import os

# Ruta base dentro del contenedor Docker
BASE_PATH = "/app/backend"
CHUNK_SIZE = 100
COMPLETED_CHUNK_PATTERN = os.path.join(BASE_PATH, "stakingcompletados_*.json")

FILES = {
    "activos": os.path.join(BASE_PATH, "stakingactivos.json"),
    "completados": os.path.join(BASE_PATH, "stakingcompletados.json"),
    "cancelados": os.path.join(BASE_PATH, "stakingcancelados_history.json")
}


def get_chunk_threshold(path):
    name = os.path.basename(path)
    number = name.split("_")[-1].split(".")[0]
    try:
        return int(number)
    except ValueError:
        return 0


def get_completed_chunk_path():
    chunk_files = glob.glob(COMPLETED_CHUNK_PATTERN)
    if not chunk_files:
        return os.path.join(BASE_PATH, f"stakingcompletados_{CHUNK_SIZE}.json")

    chunk_files.sort(key=get_chunk_threshold)
    latest = chunk_files[-1]
    with open(latest, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = []

    if len(data) < CHUNK_SIZE:
        return latest

    next_threshold = get_chunk_threshold(latest) + CHUNK_SIZE
        return os.path.join(BASE_PATH, f"stakingcompletados_{next_threshold}.json")

def load_json_file(path):
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_json_file(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

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
    return load_json_file(FILES[name])


def save_file(name, data):
    """Guarda un archivo JSON de staking."""
    save_json_file(FILES[name], data)


def append_to_completed_chunk(stake):
    path = get_completed_chunk_path()
    data = load_json_file(path)
    data.append(stake)
    save_json_file(path, data)


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
            append_to_completed_chunk(s)
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
