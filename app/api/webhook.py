import os
import requests
from fastapi import APIRouter, Request, Response, status, BackgroundTasks
from app.db.supabase_client import get_db
from app.services.gemini_service import analyze_and_extract, generate_rag_response
from app.services.crypto_service import encrypt_text, decrypt_text
from langfuse.decorators import observe, langfuse_context
from app.services.eval_service import run_rag_evaluation

router = APIRouter()

@router.post("/telegram/webhook")
@observe(name="telegram_interaction")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        # --- 0. EXTRACT DATA & INITIALIZE DB ---
        payload = await request.json()
        
        message = payload.get("message", {})
        telegram_id = message.get("from", {}).get("id")
        user_text = message.get("text", "")
        
        if not telegram_id or not user_text:
            print("⚠️ Webhook received an empty or non-text payload.")
            return Response(status_code=status.HTTP_200_OK)

        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        db = get_db()

        # --- 1. FETCH SHORT-TERM MEMORY (EARLY PULL) ---
        print(f"💬 Fetching chat context for user {telegram_id}...")
        history_res = db.table("chat_history").select("role, content").eq("telegram_id", telegram_id).order("created_at", desc=True).limit(5).execute()
        recent_messages = history_res.data[::-1] 
        chat_context = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in recent_messages])

        # --- 2. INTENT & GRAPH ANALYSIS (WITH QUERY REWRITE) ---
        print(f"📝 Raw User Text: {user_text}")
        ai_response = analyze_and_extract(user_text, chat_context=chat_context)
        
        intent_action = ai_response.get("intent", "query_data")
        is_sensitive = ai_response.get("is_sensitive", False)
        summary = ai_response.get("summary", "New Memory")
        standalone_text = ai_response.get("standalone_query", user_text)
        
        print(f"🎯 Action Decision: {intent_action} | Sensitive: {is_sensitive}")
        print(f"🎯 Standalone Query: {standalone_text}")

        # --- 3. DATABASE EXECUTION PIPELINE ---
        if intent_action == "error":
            print("🛑 System overloaded. Alerting user...")
            requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", json={
                "chat_id": telegram_id,
                "text": "My neural pathways are a bit congested right now (Google API 503). Give me a few seconds and try again!"
            })
            return Response(status_code=status.HTTP_200_OK)
            
        elif intent_action == "store_data":
            if is_sensitive:
                print("🔒 Sensitive data detected. Encrypting and routing to Secure Vault...")
                safe_label = summary
                encrypted_data = encrypt_text(user_text)
                
                db.table("secure_vault").insert({
                    "telegram_id": telegram_id,
                    "secret_type": "document",
                    "encrypted_value": encrypted_data,
                    "associated_label": safe_label
                }).execute()
                
                pointer_text = f"[SECURE_VAULT_REF] {safe_label}"
                db.table("notes").insert({
                    "telegram_id": telegram_id,
                    "content": pointer_text,
                    "cleaned_content": safe_label
                }).execute()
            else:
                print("💾 Storing standard memory in notes table...")
                db.table("notes").insert({
                    "telegram_id": telegram_id,
                    "content": user_text,
                    "cleaned_content": summary
                }).execute()
            
            # Text confirmation back to user
            requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", json={
                "chat_id": telegram_id,
                "text": f"🧠 Memory locked in: \"{summary}\""
            })
            return Response(status_code=status.HTTP_200_OK)
            
        elif intent_action == "query_data":
            print("🔍 Query detected. Initiating HYBRID search...")
            from app.services.gemini_service import client, types # Local import helper for safety
            
            # Use the rewritten text for the embedding match
            # (Assuming you have a function named generate_embedding available)
            # query_vector = generate_embedding(standalone_text)
            
            # Placeholder for your standard match query logic if needed, 
            # for now defaulting to pulling notes directly or via RPC
            rpc_response = db.table("notes").select("content").eq("telegram_id", telegram_id).limit(5).execute()
            
            retrieved_notes = []
            for match in rpc_response.data:
                note_text = match['content']
                if note_text.startswith("[SECURE_VAULT_REF]"):
                    label = note_text.replace("[SECURE_VAULT_REF] ", "")
                    print(f"🔓 Secure pointer found for '{label}'. Decrypting in RAM...")
                    vault_res = db.table("secure_vault").select("encrypted_value").eq("associated_label", label).eq("telegram_id", telegram_id).execute()
                    if vault_res.data:
                        decrypted_text = decrypt_text(vault_res.data[0]['encrypted_value'])
                        retrieved_notes.data.append(f"SECURE DOCUMENT ({label}):\n{decrypted_text}")
                else:
                    retrieved_notes.append(note_text)
            
            # Generate RAG response
            final_answer = generate_rag_response(
                question=standalone_text, 
                context_notes=retrieved_notes, 
                graph_context=[],
                chat_context=chat_context
            )
            
            # Save interaction to history
            db.table("chat_history").insert([
                {"telegram_id": telegram_id, "role": "user", "content": user_text},
                {"telegram_id": telegram_id, "role": "assistant", "content": final_answer}
            ]).execute()

            # --- 6. SEND TO TELEGRAM ---
            requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", json={
                "chat_id": telegram_id,
                "text": final_answer
            })
            
            # --- 7. TRIGGER BACKGROUND EVALUATION ---
            # Capture the master Langfuse Trace ID for this conversation
            trace_id = langfuse_context.get_current_trace_id()
            
            # Convert retrieved notes to a single string for the judge
            context_string = "\n".join(retrieved_notes) if isinstance(retrieved_notes, list) else str(retrieved_notes)
            
            # Hand the heavy lifting off to the background thread
            background_tasks.add_task(run_rag_evaluation, trace_id, standalone_text, context_string, final_answer)
            
            # Instantly tell Telegram we are done so the webhook doesn't hang!
            return Response(status_code=status.HTTP_200_OK)

    except Exception as main_err:
        print(f"❌ Critical Webhook Failure: {str(main_err)}")
        return Response(status_code=status.HTTP_200_OK)