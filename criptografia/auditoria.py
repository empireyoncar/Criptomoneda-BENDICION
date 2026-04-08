"""Security audit logging and anomaly detection for platform operations."""

from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime, timezone
from typing import Any

_AUDIT_LOG_FILE = os.getenv(
    "CRIPTO_AUDIT_LOG_PATH",
    os.path.join(os.path.dirname(__file__), "audit.log"),
)
_audit_lock = threading.Lock()


def _utc_now() -> str:
    """Return ISO timestamp in UTC for consistent distributed logging."""
    return datetime.now(timezone.utc).isoformat()


def _write_event(event: dict[str, Any]) -> None:
    """Persist event atomically as JSON line to avoid partial writes."""
    os.makedirs(os.path.dirname(_AUDIT_LOG_FILE), exist_ok=True)

    with _audit_lock:
        with open(_AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=True) + "\n")


def registrar_evento(tipo: str, user_id: str, detalles: dict[str, Any], ip: str) -> None:
    """Register a generic audit event with context metadata."""
    if not isinstance(tipo, str) or not tipo.strip():
        raise ValueError("tipo must be a non-empty string")
    if not isinstance(user_id, str) or not user_id.strip():
        raise ValueError("user_id must be a non-empty string")
    if not isinstance(detalles, dict):
        raise ValueError("detalles must be a dictionary")
    if not isinstance(ip, str) or not ip.strip():
        raise ValueError("ip must be a non-empty string")

    event = {
        "timestamp": _utc_now(),
        "tipo": tipo,
        "user_id": user_id,
        "detalles": detalles,
        "ip": ip,
    }

    try:
        _write_event(event)
    except OSError as exc:  # pragma: no cover
        raise RuntimeError("No se pudo registrar evento de auditoria") from exc


def registrar_login(user_id: str, ip: str, resultado: bool) -> None:
    """Register login outcome for authentication monitoring."""
    registrar_evento(
        tipo="login",
        user_id=user_id,
        detalles={"resultado": bool(resultado)},
        ip=ip,
    )


def registrar_cambio(operacion: str, admin_id: str, detalles: dict[str, Any]) -> None:
    """Register administrative configuration or balance changes."""
    if not isinstance(operacion, str) or not operacion.strip():
        raise ValueError("operacion must be a non-empty string")

    payload = dict(detalles)
    payload["operacion"] = operacion
    registrar_evento(tipo="cambio_admin", user_id=admin_id, detalles=payload, ip="internal")


def obtener_audit_log(user_id: str) -> list[dict[str, Any]]:
    """Return audit entries for a given user ordered by file append order."""
    if not isinstance(user_id, str) or not user_id.strip():
        raise ValueError("user_id must be a non-empty string")

    if not os.path.exists(_AUDIT_LOG_FILE):
        return []

    records: list[dict[str, Any]] = []
    with _audit_lock:
        with open(_AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if item.get("user_id") == user_id:
                    records.append(item)

    return records


def detectar_anomalias(user_id: str) -> list[dict[str, Any]]:
    """Detect anomalous security patterns from a user's audit trail."""
    logs = obtener_audit_log(user_id)
    anomalies: list[dict[str, Any]] = []

    if not logs:
        return anomalies

    now = time.time()

    # Failed login burst in the last 15 minutes.
    failed_logins = 0
    for event in logs:
        if event.get("tipo") != "login":
            continue
        if event.get("detalles", {}).get("resultado") is True:
            continue

        ts = event.get("timestamp", "")
        try:
            event_time = datetime.fromisoformat(ts).timestamp()
        except ValueError:
            continue
        if now - event_time <= 900:
            failed_logins += 1

    if failed_logins >= 5:
        anomalies.append(
            {
                "tipo": "failed_login_burst",
                "detalle": f"{failed_logins} intentos fallidos en 15 minutos",
            }
        )

    # Excessive admin changes in the last 10 minutes.
    admin_changes = 0
    for event in logs:
        if event.get("tipo") != "cambio_admin":
            continue
        ts = event.get("timestamp", "")
        try:
            event_time = datetime.fromisoformat(ts).timestamp()
        except ValueError:
            continue
        if now - event_time <= 600:
            admin_changes += 1

    if admin_changes >= 20:
        anomalies.append(
            {
                "tipo": "exceso_cambios_admin",
                "detalle": f"{admin_changes} cambios administrativos en 10 minutos",
            }
        )

    return anomalies
