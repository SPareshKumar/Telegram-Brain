import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Retrieve the encryption key from the environment
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

if not ENCRYPTION_KEY:
    raise ValueError("ENCRYPTION_KEY is missing from the .env file. Please generate one.")

# Initialize the cipher suite
cipher_suite = Fernet(ENCRYPTION_KEY.encode())

def encrypt_data(text: str) -> str:
    """Encrypts plain text into an AES-256 cipher string."""
    if not text:
        return ""
    return cipher_suite.encrypt(text.encode()).decode()

def decrypt_data(cipher_text: str) -> str:
    """Decrypts a cipher string back to plain text."""
    if not cipher_text:
        return ""
    return cipher_suite.decrypt(cipher_text.encode()).decode()