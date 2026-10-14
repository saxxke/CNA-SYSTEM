"""
security.py
===========
Cryptographic password hashing and verification utilities.
Uses standard PBKDF2-HMAC-SHA256 with cryptographically secure random salts.

Rules:
- NEVER store plaintext passwords.
- Salt is unique per hashed password.
- Constant-time comparison (hmac.compare_digest) to prevent timing side-channel attacks.
"""

import hashlib
import hmac
import secrets
from typing import Tuple


DEFAULT_ITERATIONS = 100_000
HASH_PREFIX = "pbkdf2_sha256"


def hash_password(password: str, iterations: int = DEFAULT_ITERATIONS) -> str:
    """
    Hashes a plaintext password using PBKDF2-HMAC-SHA256 with a unique random salt.

    Returns string in format:
        pbkdf2_sha256$<iterations>$<salt_hex>$<derived_key_hex>
    """
    if not isinstance(password, str) or not password:
        raise ValueError("Password must be a non-empty string.")
    
    # 16 bytes (32 hex characters) cryptographically secure salt
    salt = secrets.token_hex(16)
    salt_bytes = salt.encode("utf-8")
    password_bytes = password.encode("utf-8")
    
    dk = hashlib.pbkdf2_hmac(
        hash_name="sha256",
        password=password_bytes,
        salt=salt_bytes,
        iterations=iterations
    )
    derived_hex = dk.hex()
    return f"{HASH_PREFIX}${iterations}${salt}${derived_hex}"


def parse_hash_string(password_hash: str) -> Tuple[str, int, str, str]:
    """
    Parses a formatted password hash string into its components:
    (prefix, iterations, salt, derived_hex)
    """
    if not isinstance(password_hash, str):
        raise ValueError("Password hash must be a string.")
    
    parts = password_hash.split("$")
    if len(parts) != 4:
        raise ValueError("Invalid password hash format. Expected 4 sections separated by '$'.")
    
    prefix, iterations_str, salt, derived_hex = parts
    if prefix != HASH_PREFIX:
        raise ValueError(f"Unsupported hash algorithm '{prefix}'. Expected '{HASH_PREFIX}'.")
    
    try:
        iterations = int(iterations_str)
        if iterations <= 0:
            raise ValueError()
    except ValueError:
        raise ValueError("Invalid iteration count in password hash.")
    
    return prefix, iterations, salt, derived_hex


def verify_password(plain_password: str, password_hash: str) -> bool:
    """
    Verifies a plaintext password against a stored PBKDF2 hash.
    Uses constant-time comparison to protect against timing attacks.

    Returns True if valid, False otherwise.
    """
    if not isinstance(plain_password, str) or not plain_password:
        return False
    if not isinstance(password_hash, str) or not password_hash:
        return False
    
    try:
        _, iterations, salt, expected_derived_hex = parse_hash_string(password_hash)
    except Exception:
        return False
    
    candidate_dk = hashlib.pbkdf2_hmac(
        hash_name="sha256",
        password=plain_password.encode("utf-8"),
        salt=salt.encode("utf-8"),
        iterations=iterations
    )
    candidate_hex = candidate_dk.hex()
    
    # Constant-time comparison
    return hmac.compare_digest(candidate_hex, expected_derived_hex)
