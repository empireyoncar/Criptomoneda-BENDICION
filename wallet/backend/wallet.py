"""Wallet utilities compatible with blockchain and ECDSA signatures."""

import sys
import json
import importlib
from pathlib import Path
from ecdsa import SigningKey, SECP256k1


def _load_hash_sha256():
    """Load hash_sha256 without importing criptografia package __init__."""
    candidate_dirs = [
        Path("/app/criptografia"),
        Path(__file__).resolve().parent / "criptografia",
        Path(__file__).resolve().parents[1] / "criptografia",
    ]

    for crypto_dir in candidate_dirs:
        if not crypto_dir.exists():
            continue
        if str(crypto_dir) not in sys.path:
            sys.path.insert(0, str(crypto_dir))
        try:
            return importlib.import_module("blockchain_crypto").hash_sha256
        except ModuleNotFoundError:
            continue

    raise ModuleNotFoundError("No se pudo cargar blockchain_crypto desde criptografia")


hash_sha256 = _load_hash_sha256()


def generate_wallet():
    """
    Generate wallet with ECDSA keypair.
    
    Returns:
        {
            "private_key_hex": "raw hex string (not PEM)",
            "public_key_hex": "raw hex string (not PEM)",
            "address": "SHA256(public_key_hex)"
        }
    """
    sk = SigningKey.generate(curve=SECP256k1)
    vk = sk.get_verifying_key()

    private_key_hex = sk.to_string().hex()
    public_key_hex = vk.to_string().hex()

    # Address = SHA256 hash of public key
    address = hash_sha256(public_key_hex)

    return {
        "private_key_hex": private_key_hex,
        "public_key_hex": public_key_hex,
        "address": address
    }


def _canonical_json(data: dict) -> bytes:
    """Serialize dict to deterministic JSON for signing."""
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign_transaction(private_key_hex: str, tx_data: dict) -> str:
    """
    Sign transaction with ECDSA private key.
    
    Args:
        private_key_hex: Raw hex string from wallet
        tx_data: Transaction dict (from, to, amount, nonce, etc.)
    
    Returns:
        Signature as hex string
    """
    sk = SigningKey.from_string(bytes.fromhex(private_key_hex), curve=SECP256k1)
    signature = sk.sign(_canonical_json(tx_data))
    return signature.hex()


def build_and_sign_tx(wallet: dict, receiver: str, amount: int, nonce: int, tx_id: str = None, metadata: dict = None) -> dict:
    """
    Build and sign a complete transaction ready for blockchain.
    
    Args:
        wallet: Wallet dict from generate_wallet()
        receiver: Receiving address
        amount: Amount in satichis (integers)
        nonce: Current nonce for sender
        tx_id: Optional transaction ID
        metadata: Optional metadata
    
    Returns:
        Complete transaction dict with signature
    """
    # Build TX payload (without signature yet)
    tx_data = {
        "from": wallet["address"],
        "to": receiver,
        "amount": int(amount),
        "nonce": int(nonce)
    }
    if tx_id:
        tx_data["tx_id"] = str(tx_id)
    if metadata is not None:
        tx_data["metadata"] = metadata

    # Sign it
    signature = sign_transaction(wallet["private_key_hex"], tx_data)

    # Return complete TX with signature and public_key
    return {
        **tx_data,
        "public_key": wallet["public_key_hex"],
        "signature": signature
    }
