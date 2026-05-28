import os
from cryptography.fernet import Fernet

# Pull your existing key from the environment
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

# Initialize the cipher suite (AES-256)
cipher_suite = Fernet(ENCRYPTION_KEY.encode()) if ENCRYPTION_KEY else None

def encrypt_text(text: str) -> str:
    """Encrypts plaintext into a secure ciphertext string."""
    if not cipher_suite:
        raise ValueError("Critical Security Error: ENCRYPTION_KEY is missing.")
    # Encrypt the binary encoding of the string and decode the result for database storage
    return cipher_suite.encrypt(text.encode()).decode()

def decrypt_text(encrypted_text: str) -> str:
    """Decrypts ciphertext back into readable plaintext."""
    if not cipher_suite:
        raise ValueError("Critical Security Error: ENCRYPTION_KEY is missing.")
    return cipher_suite.decrypt(encrypted_text.encode()).decode()