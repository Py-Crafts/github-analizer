import base64
from cryptography.fernet import Fernet
from django.conf import settings
import hashlib


def get_encryption_key():
    """Generate a consistent encryption key from settings"""
    # Use the secret key to generate a consistent Fernet key
    key_material = settings.SECRET_KEY.encode('utf-8')
    # Hash to get consistent 32 bytes
    key_hash = hashlib.sha256(key_material).digest()
    # Encode to base64 for Fernet
    return base64.urlsafe_b64encode(key_hash)


def encrypt_data(data):
    """Encrypt sensitive data"""
    if not data:
        return None
    
    try:
        key = get_encryption_key()
        fernet = Fernet(key)
        encrypted_data = fernet.encrypt(data.encode('utf-8'))
        return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
    except Exception as e:
        raise ValueError(f"Encryption failed: {str(e)}")


def decrypt_data(encrypted_data):
    """Decrypt sensitive data"""
    if not encrypted_data:
        return None
    
    try:
        key = get_encryption_key()
        fernet = Fernet(key)
        # Decode from base64
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
        # Decrypt
        decrypted_data = fernet.decrypt(encrypted_bytes)
        return decrypted_data.decode('utf-8')
    except Exception as e:
        raise ValueError(f"Decryption failed: {str(e)}")


def is_encrypted(data):
    """Check if data appears to be encrypted"""
    if not data:
        return False
    
    try:
        # Try to decode as base64
        base64.urlsafe_b64decode(data.encode('utf-8'))
        return True
    except Exception:
        return False