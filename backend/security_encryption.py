import base64
from cryptography.fernet import Fernet
from config import ENCRYPTION_KEY

_fernet_instance = None

def get_fernet() -> Fernet:
    global _fernet_instance
    if _fernet_instance is None:
        key_bytes = ENCRYPTION_KEY.encode("utf-8")
        _fernet_instance = Fernet(key_bytes)
    return _fernet_instance

def encrypt_token(token: str) -> str:
    """
    Encrypts a sensitive API token or secret before database storage.
    Returns URL-safe base64-encoded ciphertext string.
    """
    if not token:
        return ""
    fernet = get_fernet()
    encrypted_bytes = fernet.encrypt(token.encode("utf-8"))
    return encrypted_bytes.decode("utf-8")

def decrypt_token(encrypted_token: str) -> str:
    """
    Decrypts an encrypted token retrieved from the database.
    Returns the original plaintext string.
    """
    if not encrypted_token:
        return ""
    fernet = get_fernet()
    decrypted_bytes = fernet.decrypt(encrypted_token.encode("utf-8"))
    return decrypted_bytes.decode("utf-8")
