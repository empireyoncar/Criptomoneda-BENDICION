"""Cryptographic utilities for blockchain (SHA256 + ECDSA)."""

from hashlib import sha256
import json


def hash_sha256(data: str) -> str:
    """Hash data with SHA256 and return hex digest."""
    if not isinstance(data, str):
        raise ValueError("data must be a string")
    return sha256(data.encode("utf-8")).hexdigest()


def canonical_json(data: dict) -> str:
    """
    Serialize dict to deterministic JSON for hashing.
    Used for transactions, blocks, and signatures.
    """
    if not isinstance(data, dict):
        raise ValueError("data must be a dictionary")
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def hash_transaccion(tx_dict: dict) -> str:
    """
    Hash a transaction for integrity checks.
    Input: transaction dict without 'signature' field
    Output: SHA256 hex digest
    """
    if not isinstance(tx_dict, dict):
        raise ValueError("tx_dict must be a dictionary")
    tx_json = canonical_json(tx_dict)
    return hash_sha256(tx_json)


def hash_bloque(block_dict: dict) -> str:
    """
    Hash a block for chain validation.
    Input: block dict (index, timestamp, transactions, previous_hash)
    Output: SHA256 hex digest
    """
    if not isinstance(block_dict, dict):
        raise ValueError("block_dict must be a dictionary")
    
    # Only hash specific fields, not the hash itself
    block_content = {
        "index": block_dict.get("index"),
        "timestamp": block_dict.get("timestamp"),
        "transactions": block_dict.get("transactions", []),
        "previous_hash": block_dict.get("previous_hash")
    }
    block_json = canonical_json(block_content)
    return hash_sha256(block_json)
