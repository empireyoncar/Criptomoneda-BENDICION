from __future__ import annotations

from typing import Any

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS

import kyc
import os

app = Flask(__name__)
CORS(app)
ALLOWED_ADMIN_IP = os.getenv("KYC_ADMIN_ALLOWED_IP", "192.168.1.178").strip()


def _ok(payload: dict[str, Any], code: int = 200):
    return jsonify(payload), code


def _error(message: str, code: int = 400):
    return jsonify({"success": False, "error": message}), code


def _json_body() -> dict[str, Any]:
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        raise ValueError("Payload JSON invalido")
    return body


def _client_ip() -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return (request.remote_addr or "").strip()


def _require_internal_admin_ip() -> None:
    ip = _client_ip()
    normalized = ip.replace("::ffff:", "")
    if normalized != ALLOWED_ADMIN_IP:
        raise PermissionError("Acceso admin permitido solo desde IP interna autorizada")


@app.get("/health")
def health():
    return _ok({"success": True, "service": "kyc_api", "status": "ok"})


@app.get("/status/<user_id>")
def get_status(user_id: str):
    try:
        status = kyc.get_kyc_status(user_id)
        return _ok({"success": True, "kyc": status})
    except ValueError as exc:
        return _error(str(exc), 404)
    except Exception as exc:
        return _error(f"Error interno: {exc}", 500)


@app.post("/upload")
def upload_step_document():
    try:
        user_id = str(request.form.get("user_id", "")).strip()
        step = str(request.form.get("step", "")).strip()
        file_obj = request.files.get("file")
        if not user_id:
            raise ValueError("user_id es requerido")
        status = kyc.save_kyc_document(user_id=user_id, step=step, file_storage=file_obj)
        return _ok({"success": True, "kyc": status})
    except ValueError as exc:
        return _error(str(exc), 400)
    except Exception as exc:
        return _error(f"Error interno al subir documento: {exc}", 500)


@app.post("/phone/submit")
def submit_phone_step():
    try:
        payload = _json_body()
        user_id = str(payload.get("user_id", "")).strip()
        if not user_id:
            raise ValueError("user_id es requerido")
        status = kyc.submit_phone_verification(user_id)
        return _ok({"success": True, "kyc": status})
    except ValueError as exc:
        return _error(str(exc), 400)
    except Exception as exc:
        return _error(f"Error interno al actualizar telefono: {exc}", 500)


@app.post("/finish")
def finish_kyc():
    try:
        payload = _json_body()
        user_id = str(payload.get("user_id", "")).strip()
        if not user_id:
            raise ValueError("user_id es requerido")
        status = kyc.finish_kyc_submission(user_id)
        return _ok({"success": True, "kyc": status})
    except ValueError as exc:
        return _error(str(exc), 400)
    except Exception as exc:
        return _error(f"Error interno al finalizar KYC: {exc}", 500)


@app.get("/docs/<user_id>/<path:filename>")
def get_doc(user_id: str, filename: str):
    try:
        file_path = kyc.get_document_path(user_id, filename)
        return send_file(file_path)
    except ValueError as exc:
        return _error(str(exc), 404)
    except Exception as exc:
        return _error(f"Error interno al leer documento: {exc}", 500)


@app.get("/admin/requests")
def admin_list_requests():
    try:
        _require_internal_admin_ip()
        rows = kyc.list_kyc_requests()
        return _ok({"success": True, "requests": rows})
    except PermissionError as exc:
        return _error(str(exc), 403)
    except Exception as exc:
        return _error(f"Error interno al listar solicitudes: {exc}", 500)


@app.get("/admin/request/<user_id>")
def admin_get_request(user_id: str):
    try:
        _require_internal_admin_ip()
        detail = kyc.get_user_kyc_detail(user_id)
        return _ok({"success": True, "request": detail})
    except PermissionError as exc:
        return _error(str(exc), 403)
    except ValueError as exc:
        return _error(str(exc), 404)
    except Exception as exc:
        return _error(f"Error interno al leer solicitud: {exc}", 500)


@app.post("/admin/decision")
def admin_decision():
    try:
        _require_internal_admin_ip()
        payload = _json_body()
        user_id = str(payload.get("user_id", "")).strip()
        decision = str(payload.get("decision", "")).strip().lower()
        admin_id = str(payload.get("admin_id", "")).strip()
        reasons_payload = payload.get("reasons", [])

        reasons: list[str]
        if isinstance(reasons_payload, list):
            reasons = [str(x) for x in reasons_payload]
        elif isinstance(reasons_payload, str):
            reasons = [line.strip() for line in reasons_payload.split("\n") if line.strip()]
        else:
            reasons = []

        reviewed = kyc.review_kyc_request(
            user_id=user_id,
            decision=decision,
            reasons=reasons,
            admin_id=admin_id,
        )
        return _ok({"success": True, "kyc": reviewed})
    except PermissionError as exc:
        return _error(str(exc), 403)
    except ValueError as exc:
        return _error(str(exc), 400)
    except Exception as exc:
        return _error(f"Error interno al revisar KYC: {exc}", 500)


if __name__ == "__main__":
    kyc.ensure_storage()
    app.run(host="0.0.0.0", port=5015, debug=True)
