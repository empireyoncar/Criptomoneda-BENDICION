from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psycopg2
from psycopg2.extras import Json, RealDictCursor
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

KYC_STEPS = ("id_document", "address_document", "selfie", "phone_verification")
UPLOAD_STEPS = ("id_document", "address_document", "selfie")
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}


def _utc_now_iso() -> str:
	return datetime.now(timezone.utc).isoformat()


def _default_kyc_state() -> dict[str, Any]:
	return {
		"id_document": {"file": None, "status": "pending"},
		"address_document": {"file": None, "status": "pending"},
		"selfie": {"file": None, "status": "pending"},
		"phone_verification": {"status": "pending"},
		"overall_status": "pending",
		"submitted_at": None,
		"reviewed_at": None,
		"rejection_reasons": [],
	}


def _resolve_default_docs_root() -> Path:
	# Keep KYC docs inside KYC backend folder as requested.
	return Path(__file__).resolve().parent / "kyc_docs"


DOCS_ROOT = Path(os.getenv("KYC_DOCS_ROOT", str(_resolve_default_docs_root())))


def _users_db_env(name: str, default: str) -> str:
	return os.getenv(name, default)


def _users_connection():
	return psycopg2.connect(
		host=_users_db_env("USERS_DB_HOST", "localhost"),
		port=int(_users_db_env("USERS_DB_PORT", "5546")),
		dbname=_users_db_env("USERS_DB_NAME", "users_db"),
		user=_users_db_env("USERS_DB_USER", "users_user"),
		password=_users_db_env("USERS_DB_PASSWORD", "users_password"),
		cursor_factory=RealDictCursor,
	)


def _row_to_user(row: dict[str, Any]) -> dict[str, Any]:
	return {
		"id": str(row.get("id", "")),
		"fullname": str(row.get("fullname", "")).strip(),
		"birthdate": row.get("birthdate"),
		"country": str(row.get("country", "")).strip(),
		"address": row.get("address"),
		"phone": row.get("phone"),
		"email": str(row.get("email", "")).strip(),
		"password": row.get("password", ""),
		"role": row.get("role", "user"),
		"wallets": list(row.get("wallets") or []),
		"kyc": row.get("kyc") if isinstance(row.get("kyc"), dict) else _default_kyc_state(),
	}


def ensure_storage() -> None:
	DOCS_ROOT.mkdir(parents=True, exist_ok=True)


def load_db() -> dict[str, Any]:
	with _users_connection() as conn:
		with conn.cursor() as cur:
			cur.execute(
				"""
				SELECT id, fullname, birthdate, country, address, phone,
					   email, password, role, wallets, kyc
				FROM users
				ORDER BY created_at ASC, id ASC
				"""
			)
			return {"users": [_row_to_user(dict(row)) for row in cur.fetchall()]}


def save_db(data: dict[str, Any]) -> None:
	users = data.get("users", []) if isinstance(data, dict) else []
	ids = [str(user.get("id", "")) for user in users if user.get("id")]

	with _users_connection() as conn:
		with conn.cursor() as cur:
			if ids:
				cur.execute("DELETE FROM users WHERE NOT (id = ANY(%s))", (ids,))
			else:
				cur.execute("DELETE FROM users")

			for user in users:
				normalized = _row_to_user(user)
				cur.execute(
					"""
					INSERT INTO users (
						id, fullname, birthdate, country, address, phone,
						email, password, role, wallets, kyc
					)
					VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
					ON CONFLICT (id)
					DO UPDATE SET
						fullname = EXCLUDED.fullname,
						birthdate = EXCLUDED.birthdate,
						country = EXCLUDED.country,
						address = EXCLUDED.address,
						phone = EXCLUDED.phone,
						email = EXCLUDED.email,
						password = EXCLUDED.password,
						role = EXCLUDED.role,
						wallets = EXCLUDED.wallets,
						kyc = EXCLUDED.kyc
					""",
					(
						normalized["id"],
						normalized["fullname"],
						normalized["birthdate"],
						normalized["country"],
						normalized["address"],
						normalized["phone"],
						normalized["email"],
						normalized["password"],
						normalized["role"],
						Json(normalized["wallets"]),
						Json(normalized["kyc"]),
					),
				)
		conn.commit()


def _ensure_user_kyc(user: dict[str, Any]) -> dict[str, Any]:
	current = user.get("kyc")
	if not isinstance(current, dict):
		user["kyc"] = _default_kyc_state()
		return user["kyc"]

	defaults = _default_kyc_state()
	for key, value in defaults.items():
		if key not in current:
			current[key] = value

	for step in ("id_document", "address_document", "selfie"):
		if not isinstance(current.get(step), dict):
			current[step] = {"file": None, "status": "pending"}
		current[step].setdefault("file", None)
		current[step].setdefault("status", "pending")

	if not isinstance(current.get("phone_verification"), dict):
		current["phone_verification"] = {"status": "pending"}
	current["phone_verification"].setdefault("status", "pending")

	if not isinstance(current.get("rejection_reasons"), list):
		current["rejection_reasons"] = []

	return current


def _get_user(data: dict[str, Any], user_id: str) -> dict[str, Any] | None:
	user_id = str(user_id)
	for user in data["users"]:
		if str(user.get("id")) == user_id:
			return user
	return None


def _sanitize_filename(original_name: str) -> str:
	name = secure_filename(original_name or "")
	if not name:
		raise ValueError("Nombre de archivo invalido")
	ext = Path(name).suffix.lower()
	if ext not in ALLOWED_EXTENSIONS:
		raise ValueError("Formato no permitido. Usa JPG, PNG o PDF")
	stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
	return f"{stamp}_{name}"


def save_kyc_document(user_id: str, step: str, file_storage: FileStorage) -> dict[str, Any]:
	if step not in UPLOAD_STEPS:
		raise ValueError("Paso KYC invalido")
	if file_storage is None:
		raise ValueError("Archivo no recibido")

	data = load_db()
	user = _get_user(data, user_id)
	if not user:
		raise ValueError("Usuario no encontrado")

	ensure_storage()
	kyc = _ensure_user_kyc(user)

	filename = _sanitize_filename(file_storage.filename or "")
	user_dir = DOCS_ROOT / str(user_id)
	user_dir.mkdir(parents=True, exist_ok=True)

	file_path = user_dir / filename
	file_storage.save(str(file_path))

	kyc[step]["file"] = filename
	kyc[step]["status"] = "submitted"
	kyc["overall_status"] = "pending"
	kyc["reviewed_at"] = None
	kyc["rejection_reasons"] = []

	save_db(data)
	return get_kyc_status(user_id)


def submit_phone_verification(user_id: str) -> dict[str, Any]:
	data = load_db()
	user = _get_user(data, user_id)
	if not user:
		raise ValueError("Usuario no encontrado")

	kyc = _ensure_user_kyc(user)
	kyc["phone_verification"]["status"] = "submitted"
	kyc["overall_status"] = "pending"
	kyc["reviewed_at"] = None
	save_db(data)
	return get_kyc_status(user_id)


def finish_kyc_submission(user_id: str) -> dict[str, Any]:
	data = load_db()
	user = _get_user(data, user_id)
	if not user:
		raise ValueError("Usuario no encontrado")

	kyc = _ensure_user_kyc(user)
	missing_steps = []
	for step in UPLOAD_STEPS:
		if not kyc[step].get("file"):
			missing_steps.append(step)
	if kyc["phone_verification"].get("status") == "pending":
		missing_steps.append("phone_verification")

	if missing_steps:
		raise ValueError(f"Faltan pasos por completar: {', '.join(missing_steps)}")

	for step in KYC_STEPS:
		if step == "phone_verification":
			if kyc[step]["status"] == "pending":
				kyc[step]["status"] = "submitted"
		else:
			if kyc[step]["status"] == "pending":
				kyc[step]["status"] = "submitted"

	kyc["overall_status"] = "in_review"
	kyc["submitted_at"] = _utc_now_iso()
	kyc["reviewed_at"] = None
	kyc["rejection_reasons"] = []

	save_db(data)
	return get_kyc_status(user_id)


def _calculate_progress(kyc: dict[str, Any]) -> int:
	overall = kyc.get("overall_status", "pending")
	if overall in {"approved", "rejected"}:
		return 100
	if overall == "in_review":
		return 80

	score = 0
	for step in UPLOAD_STEPS:
		status = str(kyc.get(step, {}).get("status", "pending"))
		if status in {"submitted", "approved", "rejected"}:
			score += 1
	phone_status = str(kyc.get("phone_verification", {}).get("status", "pending"))
	if phone_status in {"submitted", "approved", "rejected"}:
		score += 1
	return int((score / 4) * 60)


def get_kyc_status(user_id: str) -> dict[str, Any]:
	data = load_db()
	user = _get_user(data, user_id)
	if not user:
		raise ValueError("Usuario no encontrado")

	kyc = _ensure_user_kyc(user)
	result = {
		"user_id": str(user_id),
		"id_document": dict(kyc["id_document"]),
		"address_document": dict(kyc["address_document"]),
		"selfie": dict(kyc["selfie"]),
		"phone_verification": dict(kyc["phone_verification"]),
		"overall_status": kyc.get("overall_status", "pending"),
		"submitted_at": kyc.get("submitted_at"),
		"reviewed_at": kyc.get("reviewed_at"),
		"rejection_reasons": list(kyc.get("rejection_reasons", [])),
	}
	result["progress"] = _calculate_progress(result)
	result["decision_ready"] = result["overall_status"] in {"approved", "rejected"}
	return result


def list_kyc_requests() -> list[dict[str, Any]]:
	data = load_db()
	rows: list[dict[str, Any]] = []
	for user in data["users"]:
		kyc = _ensure_user_kyc(user)
		rows.append(
			{
				"id": str(user.get("id", "")),
				"fullname": str(user.get("fullname", "")).strip(),
				"email": str(user.get("email", "")).strip(),
				"country": str(user.get("country", "")).strip(),
				"overall_status": str(kyc.get("overall_status", "pending")),
				"submitted_at": kyc.get("submitted_at"),
			}
		)
	rows.sort(key=lambda x: (x["overall_status"] == "pending", x["submitted_at"] or ""), reverse=True)
	return rows


def get_user_kyc_detail(user_id: str) -> dict[str, Any]:
	data = load_db()
	user = _get_user(data, user_id)
	if not user:
		raise ValueError("Usuario no encontrado")

	status = get_kyc_status(user_id)
	status["fullname"] = str(user.get("fullname", "")).strip()
	status["email"] = str(user.get("email", "")).strip()
	status["country"] = str(user.get("country", "")).strip()
	return status


def review_kyc_request(user_id: str, decision: str, reasons: list[str] | None = None, admin_id: str | None = None) -> dict[str, Any]:
	decision = str(decision or "").strip().lower()
	if decision not in {"approved", "rejected"}:
		raise ValueError("decision debe ser approved o rejected")

	data = load_db()
	user = _get_user(data, user_id)
	if not user:
		raise ValueError("Usuario no encontrado")

	kyc = _ensure_user_kyc(user)
	cleaned_reasons = []
	for item in reasons or []:
		txt = str(item).strip()
		if txt:
			cleaned_reasons.append(txt)

	if decision == "rejected" and not cleaned_reasons:
		raise ValueError("Debes indicar al menos un motivo de rechazo")

	kyc["overall_status"] = decision
	kyc["reviewed_at"] = _utc_now_iso()
	kyc["rejection_reasons"] = cleaned_reasons if decision == "rejected" else []
	kyc["reviewed_by"] = str(admin_id or "")

	for step in KYC_STEPS:
		if step == "phone_verification":
			kyc[step]["status"] = "approved" if decision == "approved" else "rejected"
		else:
			if not kyc[step].get("file"):
				continue
			kyc[step]["status"] = "approved" if decision == "approved" else "rejected"

	save_db(data)
	return get_kyc_status(user_id)


def get_document_path(user_id: str, filename: str) -> Path:
	safe_name = secure_filename(filename or "")
	if not safe_name:
		raise ValueError("Archivo invalido")
	file_path = DOCS_ROOT / str(user_id) / safe_name
	if not file_path.exists() or not file_path.is_file():
		raise ValueError("Archivo no encontrado")
	return file_path
