import time
from p2p import (
    get_offers, add_offer, update_offer, delete_offer,
    get_pending, add_pending, delete_pending,
    add_history
)

# -------------------------
# VALIDACIÓN DE OFERTAS
# -------------------------
def validate_offer(offer):
    required = ["usuario", "tipo", "cantidad", "precio", "min", "max", "pagos", "fiat"]
    for r in required:
        if r not in offer:
            return False, f"Falta el campo: {r}"

    if offer["min"] > offer["max"]:
        return False, "El límite mínimo no puede ser mayor que el máximo."

    return True, "OK"

# -------------------------
# CREAR OFERTA
# -------------------------
def create_offer(offer):
    ok, msg = validate_offer(offer)
    if not ok:
        return False, msg

    offer["estado"] = "activa"
    add_offer(offer)
    return True, "Oferta creada"

# -------------------------
# INICIAR OPERACIÓN
# -------------------------
def start_operation(oferta_id, comprador, cantidad):
    offers = get_offers()
    oferta = next((o for o in offers if o["id"] == oferta_id), None)

    if not oferta:
        return False, "Oferta no encontrada"

    if oferta["estado"] != "activa":
        return False, "La oferta no está disponible"

    if cantidad > oferta["cantidad"]:
        return False, "Cantidad no disponible"

    # Crear operación pendiente
    op = {
        "id": int(time.time() * 1000),
        "oferta_id": oferta_id,
        "comprador": comprador,
        "vendedor": oferta["usuario"],
        "cantidad": cantidad,
        "estado": "pendiente",
        "timestamp": int(time.time())
    }

    add_pending(op)

    # Bloquear oferta
    oferta["estado"] = "bloqueada"
    update_offer(oferta_id, oferta)

    return True, op

# -------------------------
# FINALIZAR OPERACIÓN
# -------------------------
def finish_operation(op_id, completada=True):
    pending = get_pending()
    op = next((o for o in pending if o["id"] == op_id), None)

    if not op:
        return False, "Operación no encontrada"

    oferta_id = op["oferta_id"]

    # Recuperar oferta
    offers = get_offers()
    oferta = next((o for o in offers if o["id"] == oferta_id), None)

    if not oferta:
        return False, "Oferta no encontrada"

    if completada:
        # Registrar en historial
        op["estado"] = "completada"
        op["timestamp_fin"] = int(time.time())
        add_history(op)

        # Actualizar oferta
        oferta["cantidad"] -= op["cantidad"]

        if oferta["cantidad"] <= 0:
            delete_offer(oferta_id)
        else:
            oferta["estado"] = "activa"
            update_offer(oferta_id, oferta)

    else:
        # Cancelada → restaurar oferta
        oferta["estado"] = "activa"
        update_offer(oferta_id, oferta)

    # Eliminar de pendientes
    delete_pending(op_id)

    return True, "Operación finalizada"
