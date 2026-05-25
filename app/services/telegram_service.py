import os
import requests
import tempfile
from fastapi import HTTPException

# Get the token securely
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def download_telegram_file(file_id: str, file_extension: str) -> str:
    """
    Given a Telegram file_id, gets the file path and downloads it 
    to a temporary securely isolated file on the server.
    Returns the local path to the downloaded file.
    """
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN is missing.")

    # 1. Ask Telegram for the file's download path
    get_file_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={file_id}"
    response = requests.get(get_file_url).json()
    
    if not response.get("ok"):
        raise HTTPException(status_code=400, detail="Failed to get file path from Telegram")
        
    file_path = response["result"]["file_path"]
    
    # 2. Download the actual binary file data
    download_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
    file_data = requests.get(download_url)
    
    # 3. Save it to a temporary file in our Docker container
    # We use NamedTemporaryFile so it gets a unique name, preventing collisions if 2 users upload at once
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}")
    with open(temp_file.name, 'wb') as f:
        f.write(file_data.content)
        
    return temp_file.name