import os
import requests
from fastapi import APIRouter, Request, Response, status
import logging

from app.services.gemini_service import analyze_and_extract, generate_embedding, generate_rag_response, extract_media_content
from app.services.telegram_service import download_telegram_file
from app.db.supabase_client import get_db
from app.services.graph_service import build_and_traverse_graph
from app.services.crypto_service import encrypt_text, decrypt_text

router = APIRouter(prefix="/telegram", tags=["Telegram Webhook"])
logger = logging.getLogger("app.webhook")

@router.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    # --- 0. EXTRACT DATA & INITIALIZE DB ---
    payload = await request.json()

    # Safely extract message data (adapt this to your exact extraction logic)
    message = payload.get("message", {})
    telegram_id = message.get("from", {}).get("id")
    user_text = message.get("text", "")

    if not telegram_id or not user_text:
        return Response(status_code=status.HTTP_200_OK)

    # 🚨 THE FIX: Initialize the database connection HERE, before anything else!
    db = get_db()

    # --- 1. FETCH SHORT-TERM MEMORY (EARLY PULL) ---
    history_res = db.table("chat_history").select("role, content").eq("telegram_id", telegram_id).order("created_at", desc=True).limit(5).execute()
    recent_messages = history_res.data[::-1]
    chat_context = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in recent_messages])

    # --- 2. INTENT & GRAPH ANALYSIS (WITH QUERY REWRITE) ---
    # ... (the rest of your code continues normally)

    try:
        print(f"\n--- NEW INCOMING MESSAGE ---")
        caption = message.get("caption", "")
        username = message.get("from", {}).get("username", "unknown")
        
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

        # --- 1. FETCH SHORT-TERM MEMORY (EARLY PULL) ---
        history_res = db.table("chat_history").select("role, content").eq("telegram_id", telegram_id).order("created_at", desc=True).limit(5).execute()
        recent_messages = history_res.data[::-1]
        chat_context = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in recent_messages])

        # --- 2. INTENT & GRAPH ANALYSIS (WITH QUERY REWRITE) ---
        print(f"📝 Raw User Text: {user_text}")
        ai_response = analyze_and_extract(user_text, chat_context=chat_context)

        intent_action = ai_response.get("intent", "query_data")
        is_sensitive = ai_response.get("is_sensitive", False)
        summary = ai_response.get("summary", "New Memory")

        # EXTRACT THE REWRITTEN QUERY
        standalone_text = ai_response.get("standalone_query", user_text)
        print(f"🎯 Standalone Query: {standalone_text}")

        print(f"🧠 AI Decision -> Action: {intent_action} | Sensitive: {is_sensitive}")
        
        db = get_db()
        
        # User Authentication Check
        user_check = db.table("users").select("telegram_id").eq("telegram_id", telegram_id).execute()
        if not user_check.data:
            print(f"👤 New user detected. Creating profile for {telegram_id}...")
            db.table("users").insert({"telegram_id": telegram_id, "username": username}).execute()
        
        # 5. Database Execution Pipeline
        if intent_action == "error":
            print("🛑 System overloaded. Alerting user...")
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
            requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", json={
                "chat_id": telegram_id,
                "text": "My neural pathways are a bit congested right now (Google API 503). Give me a few seconds and try again!"
            })
            return Response(status_code=status.HTTP_200_OK)
        elif intent_action == "store_data":
            if is_sensitive:
                print("🔒 Sensitive data detected. Encrypting and routing to Secure Vault...")
                # 1. Generate the Safe Label (We'll use the AI's summary)
                safe_label = summary

                # 2. Encrypt the raw, sensitive text
                encrypted_data = encrypt_text(user_text)

                # 3. Store the ciphertext in the secure_vault table
                db.table("secure_vault").insert({
                    "telegram_id": telegram_id,
                    "secret_type": "document",
                    "encrypted_value": encrypted_data,
                    "associated_label": safe_label
                }).execute()

                # 4. Create a "Pointer Note" for the Vector DB and Graph
                pointer_text = f"[SECURE_VAULT_REF] {safe_label}"
                note_response = db.table("notes").insert({
                    "telegram_id": telegram_id,
                    "content": pointer_text, # The AI will see this pointer later
                    "cleaned_content": safe_label
                }).execute()

                new_note_id = note_response.data[0]['id']

                # 5. Embed the Safe Label (NOT the raw text)
                print("🧮 Generating vector embedding for Safe Label...")
                vector_array = generate_embedding(safe_label)

                # --- GRAPH INGESTION (Now using our consolidated data!) ---
                nodes_data = ai_response.get("nodes", [])
                edges_data = ai_response.get("edges", [])

                if vector_array:
                    db.table("note_embeddings").insert({
                        "id": new_note_id,
                        "telegram_id": telegram_id,
                        "embedding": vector_array
                    }).execute()

                if nodes_data:
                    for node in nodes_data:
                        db.table("nodes").insert({
                            "telegram_id": telegram_id,
                            "note_id": new_note_id,
                            "entity_name": node.get("name", "").lower(),
                            "entity_type": node.get("type", "").lower()
                        }).execute()

                if edges_data:
                    for edge in edges_data:
                        db.table("edges").insert({
                            "telegram_id": telegram_id,
                            "source_entity_name": edge.get("source", "").lower(),
                            "target_entity_name": edge.get("target", "").lower(),
                            "relationship": edge.get("relationship", "").lower()
                        }).execute()

                print(f"✅ Pipeline Complete: Vector + {len(nodes_data)} Nodes + {len(edges_data)} Edges stored.")
            else:
                print("💾 Storing standard memory in notes table...")
                note_response = db.table("notes").insert({
                    "telegram_id": telegram_id,
                    "content": user_text,
                    "cleaned_content": summary
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
                    
                # --- GRAPH INGESTION (Now using our consolidated data!) ---
                nodes_data = ai_response.get("nodes", [])
                edges_data = ai_response.get("edges", [])
                
                if nodes_data:
                    for node in nodes_data:
                        db.table("nodes").insert({
                            "telegram_id": telegram_id,
                            "note_id": new_note_id,
                            "entity_name": node.get("name", "").lower(),
                            "entity_type": node.get("type", "").lower()
                        }).execute()
                
                if edges_data:
                    for edge in edges_data:
                        db.table("edges").insert({
                            "telegram_id": telegram_id,
                            "source_entity_name": edge.get("source", "").lower(),
                            "target_entity_name": edge.get("target", "").lower(),
                            "relationship": edge.get("relationship", "").lower()
                        }).execute()
                        
                print(f"✅ Pipeline Complete: Vector + {len(nodes_data)} Nodes + {len(edges_data)} Edges stored.")
                
        elif intent_action == "query_data":
            print("🔍 Query detected. Initiating HYBRID search...")
            
            # --- 1. VECTOR SEARCH (Semantic) ---
            query_vector = generate_embedding(standalone_text)
            rpc_response = db.rpc(
                'match_notes', 
                {
                    'query_embedding': query_vector,
                    'match_threshold': 0.5,
                    'match_count': 3,
                    'p_telegram_id': telegram_id
                }
            ).execute()
            
            # --- THE DECRYPTION INTERCEPTOR ---
            retrieved_notes = []
            for match in rpc_response.data:
                note_text = match['content']
                if note_text.startswith("[SECURE_VAULT_REF]"):
                    # It's a pointer! Let's fetch and decrypt the real data in memory.
                    label = note_text.replace("[SECURE_VAULT_REF] ", "")
                    print(f"🔓 Secure pointer found for '{label}'. Decrypting in RAM...")
                    
                    vault_res = db.table("secure_vault").select("encrypted_value").eq("associated_label", label).eq("telegram_id", telegram_id).execute()
                    
                    if vault_res.data:
                        decrypted_text = decrypt_text(vault_res.data[0]['encrypted_value'])
                        retrieved_notes.append(f"SECURE DOCUMENT ({label}):\n{decrypted_text}")
                else:
                    # Standard public note
                    retrieved_notes.append(note_text)
            
            print(f"📚 Vector Search: Found {len(retrieved_notes)} relevant memories.")

            # --- 2. GRAPH SEARCH (Relational) ---
            graph_context = build_and_traverse_graph(telegram_id, user_text)
            print(f"🕸️ Graph Search: Found {len(graph_context)} relationship edges.")

            # --- 3. FETCH SHORT-TERM MEMORY ---
            history_res = db.table("chat_history").select("role, content").eq("telegram_id", telegram_id).order("created_at", desc=True).limit(5).execute()
            
            # Reverse the list so it reads chronologically (oldest to newest)
            recent_messages = history_res.data[::-1] 
            chat_context = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in recent_messages])
            
            print("💬 Injected recent conversational memory.")

            # --- 4. RAG SYNTHESIS ---
            # map graph_context to graph_relationships for the new API
            graph_relationships = graph_context
            final_answer = generate_rag_response(
                question=standalone_text, 
                context_notes=retrieved_notes, 
                graph_context=graph_relationships,
                chat_context=chat_context
            )
            
            # --- 5. SAVE NEW INTERACTION TO SHORT-TERM MEMORY ---
            db.table("chat_history").insert([
                {"telegram_id": telegram_id, "role": "user", "content": user_text},
                {"telegram_id": telegram_id, "role": "assistant", "content": final_answer}
            ]).execute()

            # --- 6. SEND TO TELEGRAM ---
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
            requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", json={
                "chat_id": telegram_id,
                "text": final_answer
            })
            return Response(status_code=status.HTTP_200_OK)
            
        return Response(status_code=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"❌ Webhook Error: {str(e)}")
        return Response(status_code=status.HTTP_200_OK)