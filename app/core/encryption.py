import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Retrieve the master encryption key from the environment
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

if not ENCRYPTION_KEY:
    raise ValueError("CRITICAL: ENCRYPTION_KEY is missing from your .env file. Please generate one.")

# Initialize the Fernet symmetric cipher suite
cipher_suite = Fernet(ENCRYPTION_KEY.encode())

def encrypt_data(text: str) -> str:
    """Encrypts cleartext into a secure AES-256 ciphertext string."""
    if not text:
        return ""
    return cipher_suite.encrypt(text.encode()).decode()

def decrypt_data(cipher_text: str) -> str:
    """Decrypts AES-256 ciphertext blocks back into readable plain text."""
    if not cipher_text:
        return ""
    return cipher_suite.decrypt(cipher_text.encode()).decode()