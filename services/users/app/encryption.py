"""
PII data encryption utilities for the Users service
"""

import os
import base64
from cryptography.fernet import Fernet
from typing import Optional


# Encryption key for PII data - in production, store securely
ENCRYPTION_KEY = os.environ.get("PII_ENCRYPTION_KEY", "fernet-key-for-development-only-32chars")

def generate_key() -> str:
    """Generate a new Fernet key."""
    return Fernet.generate_key().decode()


def get_fernet_instance() -> Fernet:
    """Get Fernet instance with the encryption key."""
    # If key is provided as base64, use it directly
    # Otherwise, derive a key from the string (for development)
    try:
        key = base64.urlsafe_b64encode(ENCRYPTION_KEY.ljust(32, '0')[:32].encode())
        return Fernet(key)
    except Exception:
        # Fallback to a generated key for development
        key = Fernet.generate_key()
        return Fernet(key)


def encrypt_pii(data: str) -> str:
    """Encrypt PII data."""
    if not data:
        return data
    
    fernet = get_fernet_instance()
    encrypted_data = fernet.encrypt(data.encode())
    return encrypted_data.decode()


def decrypt_pii(encrypted_data: str) -> str:
    """Decrypt PII data."""
    if not encrypted_data:
        return encrypted_data
    
    try:
        fernet = get_fernet_instance()
        decrypted_data = fernet.decrypt(encrypted_data.encode())
        return decrypted_data.decode()
    except Exception:
        # If decryption fails, return the original data (for backwards compatibility)
        return encrypted_data


def encrypt_user_pii(user_data: dict) -> dict:
    """Encrypt PII fields in user data."""
    encrypted_data = user_data.copy()
    
    # Encrypt PII fields
    pii_fields = ['email', 'first_name', 'last_name', 'phone_number']
    for field in pii_fields:
        if field in encrypted_data and encrypted_data[field]:
            encrypted_data[field] = encrypt_pii(encrypted_data[field])
    
    return encrypted_data


def decrypt_user_pii(user_data: dict) -> dict:
    """Decrypt PII fields in user data."""
    decrypted_data = user_data.copy()
    
    # Decrypt PII fields
    pii_fields = ['email', 'first_name', 'last_name', 'phone_number']
    for field in pii_fields:
        if field in decrypted_data and decrypted_data[field]:
            decrypted_data[field] = decrypt_pii(decrypted_data[field])
    
    return decrypted_data 