from cryptography.fernet import Fernet
from api.config import settings
import base64
import hashlib


def get_encryption_key() -> bytes:
    """
    Derive encryption key from SECRET_KEY
    Fernet requires 32 url-safe base64-encoded bytes
    """
    # Use SECRET_KEY from config and derive a proper Fernet key
    key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return base64.urlsafe_b64encode(key)


def encrypt_token(token: str) -> str:
    """
    Encrypt token using AES-256 (via Fernet)
    
    Args:
        token: Plain text token to encrypt
        
    Returns:
        Encrypted token as base64 string
    """
    f = Fernet(get_encryption_key())
    encrypted = f.encrypt(token.encode())
    return encrypted.decode()


def decrypt_token(encrypted_token: str) -> str:
    """
    Decrypt token using AES-256 (via Fernet)
    
    Args:
        encrypted_token: Encrypted token string
        
    Returns:
        Decrypted plain text token
        
    Raises:
        ValueError: If decryption fails (invalid key or corrupted data)
    """
    try:
        f = Fernet(get_encryption_key())
        decrypted = f.decrypt(encrypted_token.encode())
        return decrypted.decode()
    except Exception as e:
        raise ValueError(f"Failed to decrypt token: {str(e)}")
