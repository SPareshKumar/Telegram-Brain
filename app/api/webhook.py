from fastapi import APIRouter, Request, Response, status
import logging
import os
import requests
from app.services.gemini_service import classify_text_intent, generate_embedding, generate_rag_response
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
                else:
                    print("💾 Storing standard memory in notes table...")
                    
                    # 1. Insert the text note and capture the generated UUID
                    note_response = db.table("notes").insert({
                        "telegram_id": telegram_id,
                        "content": user_text,
                        "cleaned_content": intent.summary
                    }).execute()
                    
                    # Extract the ID of the newly created note
                    new_note_id = note_response.data[0]['id']
                    print(f"✅ Text saved with ID: {new_note_id}")
                    
                    # 2. Generate the mathematical vector
                    print("🧮 Generating 768-dimensional vector embedding...")
                    vector_array = generate_embedding(user_text)
                    
                    # 3. Store the vector in pgvector
                    if vector_array:
                        db.table("note_embeddings").insert({
                            "id": new_note_id,
                            "telegram_id": telegram_id,
                            "embedding": vector_array
                        }).execute()
                        print("✅ Vector successfully indexed in Supabase!")
                    
            elif intent.action == "query_data":
                print("🔍 Query detected. Initiating vector search...")
                
                # 1. Embed the user's question
                query_vector = generate_embedding(user_text)
                
                # 2. Search Supabase using our new SQL RPC function
                rpc_response = db.rpc(
                    'match_notes', 
                    {
                        'query_embedding': query_vector,
                        'match_threshold': 0.5, # Only return somewhat relevant matches
                        'match_count': 3,       # Top 3 results
                        'p_telegram_id': telegram_id
                    }
                ).execute()
                
                # 3. Extract the text content from the database results
                retrieved_notes = [match['content'] for match in rpc_response.data]
                print(f"📚 Found {len(retrieved_notes)} relevant memories.")
                
                # 4. Generate the AI response
                final_answer = generate_rag_response(user_text, retrieved_notes)
                print(f"🤖 AI Answer: {final_answer}")
                
                # 5. Send the message back to the user via Telegram
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