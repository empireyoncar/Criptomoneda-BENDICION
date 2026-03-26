# ============================================================
#   REGISTRO NIVEL 3
# ============================================================
@app.route("/crypto/register", methods=["POST"])
def register():
    data = request.json

    fullname = data.get("fullname")
    birthdate = data.get("birthdate")
    country = data.get("country")
    address = data.get("address")
    phone = data.get("phone")
    email = data.get("email")
    password = data.get("password")

    if not fullname or not birthdate or not country or not address or not email or not password:
        return jsonify({"error": "Faltan datos obligatorios"}), 400

    user_id = register_user(fullname, birthdate, country, address, phone, email, password)

    if not user_id:
        return jsonify({"error": "El email ya está registrado"}), 400

    return jsonify({"message": "Usuario registrado correctamente", "user_id": user_id})


# ============================================================
#   SUBIR DOCUMENTO KYC
# ============================================================
@app.route("/crypto/upload_kyc_step", methods=["POST"])
def upload_kyc_step():
    user_id = request.form.get("user_id")
    step = request.form.get("step")
    file = request.files.get("file")

    if step not in ["id_document", "address_document", "selfie"]:
        return jsonify({"error": "Paso KYC inválido"}), 400

    if not file:
        return jsonify({"error": "Archivo no recibido"}), 400

    filename = secure_filename(file.filename)
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(path)

    db = load_db()
    for u in db["users"]:
        if u["id"] == user_id:
            u["kyc"][step]["file"] = filename
            u["kyc"][step]["status"] = "submitted"
            save_db(db)
            return jsonify({"message": "Archivo subido", "step": step})

    return jsonify({"error": "Usuario no encontrado"}), 404


# ============================================================
#   ACTUALIZAR ESTADO KYC
# ============================================================
@app.route("/crypto/update_kyc_status", methods=["POST"])
def update_kyc_status():
    data = request.json
    user_id = data.get("user_id")
    step = data.get("step")
    status = data.get("status")

    if step not in ["id_document", "address_document", "selfie", "phone_verification"]:
        return jsonify({"error": "Paso inválido"}), 400

    db = load_db()
    for u in db["users"]:
        if u["id"] == user_id:
            u["kyc"][step]["status"] = status
            save_db(db)
            return jsonify({"message": "Estado actualizado"})

    return jsonify({"error": "Usuario no encontrado"}), 404


# ============================================================
#   OBTENER ESTADO KYC
# ============================================================
@app.route("/crypto/get_kyc_status/<user_id>", methods=["GET"])
def get_kyc_status(user_id):
    db = load_db()
    for u in db["users"]:
        if u["id"] == user_id:
            return jsonify(u["kyc"])
    return jsonify({"error": "Usuario no encontrado"}), 404

# ============================================================
#   ACTUALIZAR ESTADO KYC
# ============================================================
@app.route("/crypto/update_kyc_status", methods=["POST"])
def update_kyc_status():
    data = request.json
    user_id = data.get("user_id")
    step = data.get("step")
    status = data.get("status")

    if step not in ["id_document", "address_document", "selfie", "phone_verification"]:
        return jsonify({"error": "Paso inválido"}), 400

    db = load_db()
    for u in db["users"]:
        if u["id"] == user_id:
            u["kyc"][step]["status"] = status
            save_db(db)
            return jsonify({"message": "Estado actualizado"})

    return jsonify({"error": "Usuario no encontrado"}), 404

# ============================================================
#   OBTENER ESTADO KYC
# ============================================================
@app.route("/crypto/get_kyc_status/<user_id>", methods=["GET"])
def get_kyc_status(user_id):
    db = load_db()
    for u in db["users"]:
        if u["id"] == user_id:
            return jsonify(u["kyc"])
    return jsonify({"error": "Usuario no encontrado"}), 404

# ============================================================
#   ADMIN APRUEBA KYC
# ============================================================
@app.route("/crypto/admin/kyc/approve_step", methods=["POST"])
@require_admin
def admin_approve_step():
    data = request.json
    user_id = data.get("user_id")
    step = data.get("step")

    if step not in ["id_document", "address_document", "selfie", "phone_verification"]:
        return jsonify({"error": "Paso inválido"}), 400

    db = load_db()
    for u in db["users"]:
        if u["id"] == user_id:
            u["kyc"][step]["status"] = "approved"

            steps = u["kyc"]
            if all(
                steps[s]["status"] == "approved"
                for s in ["id_document", "address_document", "selfie"]
            ) and steps["phone_verification"]["status"] == "approved":
                u["kyc"]["overall_status"] = "approved"

            save_db(db)
            return jsonify({"message": "Paso aprobado"})

    return jsonify({"error": "Usuario no encontrado"}), 404

# ============================================================
#   KYC
# ============================================================

# --- Obtener documentos KYC
@app.route("/admin/kyc/docs/<user_id>", methods=["GET"])
@require_admin
def admin_kyc_docs(user_id):
    db = load_db()
    for u in db["users"]:
        if str(u["id"]) == str(user_id):
            return jsonify(u.get("kyc", {}))
    return jsonify({"error": "Usuario no encontrado"}), 404


# --- Aprobar KYC
@app.route("/admin/kyc/approve", methods=["POST"])
@require_admin
def admin_approve_kyc():
    data = request.json
    user_id = data.get("user_id")

    db = load_db()
    for u in db["users"]:
        if u["id"] == user_id:
            u["kyc"]["status"] = "approved"
            save_db(db)
            return jsonify({"message": "KYC aprobado"})

    return jsonify({"error": "Usuario no encontrado"}), 404


# --- Rechazar KYC
@app.route("/admin/kyc/reject", methods=["POST"])
@require_admin
def admin_reject_kyc():
    data = request.json
    user_id = data.get("user_id")

    db = load_db()
    for u in db["users"]:
        if u["id"] == user_id:
            u["kyc"]["status"] = "rejected"
            save_db(db)
            return jsonify({"message": "KYC rechazado"})

    return jsonify({"error": "Usuario no encontrado"}), 404


# ============================================================
#   INICIAR SERVIDOR
# ============================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5008, debug=True)
