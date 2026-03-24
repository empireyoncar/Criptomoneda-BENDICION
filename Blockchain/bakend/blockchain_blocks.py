# blockchain_blocks.py
import os
import json
import shutil


BLOCKS_PER_FILE = 1000
MAIN_FILE = "blockchain.json"
ARCHIVE_DIR = "archive"


def ensure_directories():
    """Crea la carpeta archive si no existe."""
    if not os.path.exists(ARCHIVE_DIR):
        os.makedirs(ARCHIVE_DIR)


def load_state():
    """
    Carga blockchain.json si existe.
    Devuelve:
    - chain_data (lista de bloques)
    - pending_transactions
    - wallets
    - locked_balances
    """
    if not os.path.exists(MAIN_FILE):
        return [], [], {}, {}

    with open(MAIN_FILE, "r") as f:
        data = json.load(f)

    return (
        data.get("chain", []),
        data.get("pending_transactions", []),
        data.get("wallets", {}),
        data.get("locked_balances", {})
    )


def save_state(chain, pending_transactions, wallets, locked_balances):
    """
    Guarda el estado actual en blockchain.json.
    """
    data = {
        "chain": chain,
        "pending_transactions": pending_transactions,
        "wallets": wallets,
        "locked_balances": locked_balances
    }

    with open(MAIN_FILE, "w") as f:
        json.dump(data, f, indent=4)


def rotate_if_needed(chain, pending_transactions, wallets, locked_balances):
    """
    Si la cadena tiene 1000 bloques, rota el archivo:
    - Mueve blockchain.json a archive/blockchain_1_1000.json
    - Crea un nuevo blockchain.json con:
        * El último bloque (para continuidad)
        * Wallets
        * Locked balances
        * Pendientes vacías
    """
    if len(chain) < BLOCKS_PER_FILE:
        return  # No rotar todavía

    ensure_directories()

    # Determinar número de archivo
    first_index = chain[0]["index"]
    last_index = chain[-1]["index"]

    archive_name = f"blockchain_{first_index}_{last_index}.json"
    archive_path = os.path.join(ARCHIVE_DIR, archive_name)

    # Mover archivo actual al archivo de archivo
    shutil.move(MAIN_FILE, archive_path)

    # Crear nuevo archivo con el último bloque
    new_chain = [chain[-1]]  # Mantener continuidad

    save_state(
        new_chain,
        [],  # Pendientes vacías
        wallets,
        locked_balances
    )
