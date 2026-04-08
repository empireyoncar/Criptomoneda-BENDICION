"""Unified cryptography API for the Criptomoneda-BENDICION project."""

from .auditoria import (
    detectar_anomalias,
    obtener_audit_log,
    registrar_cambio,
    registrar_evento,
    registrar_login,
)
from .contrasenas import (
    generar_password_temporal,
    hashear_bcrypt,
    validar_fortaleza,
    verificar_bcrypt,
)
from .encriptacion import (
    derivar_clave,
    desencriptar_aes,
    encriptar_aes,
    generar_clave_maestra,
)
from .firma_digital import (
    firmar_bloque,
    firmar_transaccion,
    generar_nonce,
    verificar_firma,
    verificar_nonce,
)
from .hashing import generate_salt, hash_sha256, hash_sha512, verify_hash
from .tokens import generar_jwt, renovar_jwt, revocar_jwt, verificar_jwt
from .validacion import (
    detectar_fraude,
    validar_cantidad,
    validar_email,
    validar_transaccion,
    validar_usuario,
)

__all__ = [
    "detectar_anomalias",
    "obtener_audit_log",
    "registrar_cambio",
    "registrar_evento",
    "registrar_login",
    "generar_password_temporal",
    "hashear_bcrypt",
    "validar_fortaleza",
    "verificar_bcrypt",
    "derivar_clave",
    "desencriptar_aes",
    "encriptar_aes",
    "generar_clave_maestra",
    "firmar_bloque",
    "firmar_transaccion",
    "generar_nonce",
    "verificar_firma",
    "verificar_nonce",
    "generate_salt",
    "hash_sha256",
    "hash_sha512",
    "verify_hash",
    "generar_jwt",
    "renovar_jwt",
    "revocar_jwt",
    "verificar_jwt",
    "detectar_fraude",
    "validar_cantidad",
    "validar_email",
    "validar_transaccion",
    "validar_usuario",
]
