import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Get your token from the .env file
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# IMPORTANT: Paste your exact Ngrok URL here, and make sure it ends with /telegram/webhook
NGROK_URL = "https://YOUR-NGROK-URL-HERE.ngrok-free.app/telegram/webhook"

url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={NGROK_URL}"

print(f"Setting webhook to: {NGROK_URL}")
response = requests.get(url)

print("Telegram API Response:")
print(response.json())