import os
import requests
from fastapi import APIRouter, Request, Response, status
import logging

from app.services.gemini_service import classify_text_intent, generate_embedding, generate_rag_response, extract_media_content
from app.services.telegram_service import download_telegram_file
from app.db.supabase_client import get_db

router = APIRouter(prefix="/telegram", tags=["Telegram Webhook"])
logger = logging.getLogger("app.webhook")

@router.post("/webhook")
async def telegram_webhook_entry(request: Request):
    """
    Receives incoming messages from Telegram, processes multimodal attachments,
    routes them via AI, and interacts with the Supabase pgvector database.
    """
    try:
        payload = await request.json()
        message_data = payload.get("message", {})
        telegram_id = message_data.get("from", {}).get("id")
        username = message_data.get("from", {}).get("username", "unknown")
        
        # Security drop for empty payloads
        if not telegram_id:
            return Response(status_code=status.HTTP_200_OK)

        print(f"\n--- NEW INCOMING MESSAGE ---")
        
        user_text = message_data.get("text", "")
        caption = message_data.get("caption", "")
        
        file_id = None
        file_ext = ""
        media_type = ""
        
        # 1. Identify Media Attachments
        if "photo" in message_data:
            file_id = message_data["photo"][-1]["file_id"]
            file_ext = "jpg"
            media_type = "image"
        elif "voice" in message_data:
            file_id = message_data["voice"]["file_id"]
            file_ext = "ogg"
            media_type = "audio"
        elif "document" in message_data:
            file_id = message_data["document"]["file_id"]
            file_ext = "pdf"
            media_type = "document"
        elif "video" in message_data:
            file_id = message_data["video"]["file_id"]
            file_ext = "mp4"
            media_type = "video"

        # 2. Extract Media Content via Gemini
        if file_id:
            print(f"📎 {media_type.capitalize()} attachment detected! Downloading...")
            try:
                local_path = download_telegram_file(file_id, file_ext)
                extracted_text = extract_media_content(local_path, media_type, caption)
                print(f"🧠 Extracted Media Content: {extracted_text[:100]}...")
                os.remove(local_path)
                
                # Override the user_text variable so the RAG pipeline processes it normally
                user_text = f"[{media_type.upper()} UPLOAD] Caption: {caption}\nExtracted Content: {extracted_text}"
            except Exception as e:
                print(f"❌ Failed to process media: {e}")
                return Response(status_code=status.HTTP_200_OK)
                
        # 3. Validation
        if not user_text:
            return Response(status_code=status.HTTP_200_OK)

        print(f"User {telegram_id} says: '{user_text[:50]}...'")
        
        # 4. AI Intent Routing
        intent = classify_text_intent(user_text)
        print(f"🧠 AI Decision -> Action: {intent.action} | Sensitive: {intent.is_sensitive}")
        
        db = get_db()
        
        # User Authentication Check
        user_check = db.table("users").select("telegram_id").eq("telegram_id", telegram_id).execute()
        if not user_check.data:
            print(f"👤 New user detected. Creating profile for {telegram_id}...")
            db.table("users").insert({"telegram_id": telegram_id, "username": username}).execute()
        
        # 5. Database Execution Pipeline
        if intent.action == "store_data":
            if intent.is_sensitive:
                print("🔒 Sensitive data detected. Routing to secure vault...")
            else:
                print("💾 Storing standard memory in notes table...")
                note_response = db.table("notes").insert({
                    "telegram_id": telegram_id,
                    "content": user_text,
                    "cleaned_content": intent.summary
                }).execute()
                
                new_note_id = note_response.data[0]['id']
                print(f"✅ Text saved with ID: {new_note_id}")
                
                print("🧮 Generating 768-dimensional vector embedding...")
                vector_array = generate_embedding(user_text)
                
                if vector_array:
                    db.table("note_embeddings").insert({
                        "id": new_note_id,
                        "telegram_id": telegram_id,
                        "embedding": vector_array
                    }).execute()
                    print("✅ Vector successfully indexed in Supabase!")
                    
        elif intent.action == "query_data":
            print("🔍 Query detected. Initiating vector search...")
            query_vector = generate_embedding(user_text)
            
            # Geometric distance search
            rpc_response = db.rpc(
                'match_notes', 
                {
                    'query_embedding': query_vector,
                    'match_threshold': 0.5,
                    'match_count': 3,
                    'p_telegram_id': telegram_id
                }
            ).execute()
            
            retrieved_notes = [match['content'] for match in rpc_response.data]
            print(f"📚 Found {len(retrieved_notes)} relevant memories.")
            
            # RAG Synthesis
            final_answer = generate_rag_response(user_text, retrieved_notes)
            print(f"🤖 AI Answer: {final_answer}")
            
            # Send the AI response back to Telegram
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
            telegram_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            requests.post(telegram_url, json={
                "chat_id": telegram_id,
                "text": final_answer
            })
            print("✅ Reply successfully sent to Telegram!")
            
        return Response(status_code=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"❌ Webhook Error: {str(e)}")
        return Response(status_code=status.HTTP_200_OK)