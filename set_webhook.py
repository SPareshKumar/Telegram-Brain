import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Your new permanent production cloud URL!
WEBHOOK_URL = "https://mindmap-ai-5ip8.onrender.com/telegram/webhook"

url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}"

print(f"Setting webhook to: {WEBHOOK_URL}")
response = requests.get(url)

print("Telegram API Response:")
print(response.json())