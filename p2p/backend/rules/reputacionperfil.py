from __future__ import annotations

import p2p_repository as repo
from p2p_common import require_non_empty


def get_reputation(user_id: str) -> dict:
    user_id = require_non_empty(user_id, "user_id")
    return repo.get_user_reputation(user_id)


def update_profile(user_id: str, actor_user_id: str, bio: str) -> dict:
    user_id = require_non_empty(user_id, "user_id")
    actor_user_id = require_non_empty(actor_user_id, "actor_user_id")
    if user_id != actor_user_id:
        raise PermissionError("Solo el propietario puede editar su biografia")

    bio = str(bio or "").strip()
    if len(bio) > 300:
        raise ValueError("La biografia no puede superar 300 caracteres")
    return repo.upsert_user_profile(user_id, bio)
