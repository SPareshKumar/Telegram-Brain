from fastapi import APIRouter, Request, Response, status
import logging
from app.services.gemini_service import classify_text_intent

router = APIRouter(prefix="/telegram", tags=["Telegram Webhook"])
logger = logging.getLogger("app.webhook")

@router.post("/webhook")
async def telegram_webhook_entry(request: Request):
    """
    Receives incoming messages from Telegram and routes them via AI.
    """
    try:
        payload = await request.json()
        
        # Safely extract the text message from the Telegram JSON payload
        # Telegram JSON structure: payload['message']['text']
        message_data = payload.get("message", {})
        user_text = message_data.get("text", "")
        telegram_id = message_data.get("from", {}).get("id")
        
        if user_text and telegram_id:
            logger.info(f"Processing message from {telegram_id}...")
            
            # Send the text to Gemini for classification
            intent = classify_text_intent(user_text)
            
            logger.info(f"AI Decision -> Action: {intent.action} | Sensitive: {intent.is_sensitive}")
            
            # TODO: Next step is executing the Database Insertion based on this decision!
            
        return Response(status_code=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Webhook processing failed: {str(e)}")
        return Response(status_code=status.HTTP_200_OK)