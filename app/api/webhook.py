from fastapi import APIRouter, Request, Response, status
import logging
from app.services.gemini_service import classify_text_intent
from app.db.supabase_client import get_db

router = APIRouter(prefix="/telegram", tags=["Telegram Webhook"])
logger = logging.getLogger("app.webhook")

@router.post("/webhook")
async def telegram_webhook_entry(request: Request):
    """
    Receives incoming messages from Telegram, routes them via AI, 
    and interacts with the Supabase database.
    """
    try:
        payload = await request.json()
        
        # Extract metadata
        message_data = payload.get("message", {})
        user_text = message_data.get("text", "")
        telegram_id = message_data.get("from", {}).get("id")
        username = message_data.get("from", {}).get("username", "unknown")
        
        if user_text and telegram_id:
            print(f"\n--- NEW MESSAGE ---")
            print(f"User {telegram_id} says: '{user_text}'")
            
            # 1. AI Intent Classification
            intent = classify_text_intent(user_text)
            print(f"🧠 AI Decision -> Action: {intent.action} | Sensitive: {intent.is_sensitive}")
            
            # 2. Database Execution
            db = get_db()
            
            # Check if user exists, if not, insert them
            user_check = db.table("users").select("telegram_id").eq("telegram_id", telegram_id).execute()
            if not user_check.data:
                print(f"👤 New user detected. Creating profile for {telegram_id}...")
                db.table("users").insert({"telegram_id": telegram_id, "username": username}).execute()
            
            # Execute the AI's routed action
            if intent.action == "store_data":
                if intent.is_sensitive:
                    print("🔒 Sensitive data detected. Routing to secure vault... (To Be Implemented)")
                    # We will add the encryption logic here next!
                else:
                    print("💾 Storing standard memory in notes table...")
                    db.table("notes").insert({
                        "telegram_id": telegram_id,
                        "content": user_text,
                        "cleaned_content": intent.summary
                    }).execute()
                    print("✅ Memory successfully saved to Supabase!")
                    
            elif intent.action == "query_data":
                print("🔍 Query detected. Initiating vector search... (To Be Implemented)")
                
        return Response(status_code=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"❌ Webhook Error: {str(e)}")
        return Response(status_code=status.HTTP_200_OK)