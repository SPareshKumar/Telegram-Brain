import os
import requests
from fastapi import APIRouter, Request, Response, status, BackgroundTasks
from app.db.supabase_client import get_db
from app.services.gemini_service import analyze_and_extract, generate_rag_response
from app.services.crypto_service import encrypt_text, decrypt_text
from app.services.eval_service import run_rag_evaluation

# 🚨 THE FIX: Import the core client, NOT the decorators
from langfuse import Langfuse 

router = APIRouter()
# Initialize the native client
langfuse_client = Langfuse()

@router.post("/telegram/webhook")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        # --- 0. EXTRACT DATA & INITIALIZE DB ---
        payload = await request.json()
        
        message = payload.get("message", {})
        telegram_id = message.get("from", {}).get("id")
        user_text = message.get("text", "")
        
        if not telegram_id or not user_text:
            return Response(status_code=status.HTTP_200_OK)

        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        db = get_db()

        # 🚀 START MANUAL LANGFUSE TRACE
        trace = langfuse_client.trace(
            name="telegram_interaction",
            user_id=str(telegram_id),
            input={"user_text": user_text}
        )

        # --- 1. FETCH SHORT-TERM MEMORY (EARLY PULL) ---
        history_res = db.table("chat_history").select("role, content").eq("telegram_id", telegram_id).order("created_at", desc=True).limit(5).execute()
        recent_messages = history_res.data[::-1] 
        chat_context = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in recent_messages])

        # --- 2. INTENT & GRAPH ANALYSIS ---
        ai_response = analyze_and_extract(user_text, chat_context=chat_context)
        
        intent_action = ai_response.get("intent", "query_data")
        is_sensitive = ai_response.get("is_sensitive", False)
        summary = ai_response.get("summary", "New Memory")
        standalone_text = ai_response.get("standalone_query", user_text)

        # --- 3. DATABASE EXECUTION PIPELINE ---
        if intent_action == "error":
            requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", json={
                "chat_id": telegram_id,
                "text": "My neural pathways are a bit congested right now (Google API 503). Give me a few seconds and try again!"
            })
            trace.update(output="API 503 Error")
            return Response(status_code=status.HTTP_200_OK)
            
        elif intent_action == "store_data":
            # (Your existing store_data logic here for standard and secure memories...)
            if is_sensitive:
                safe_label = summary
                encrypted_data = encrypt_text(user_text)
                db.table("secure_vault").insert({"telegram_id": telegram_id, "secret_type": "document", "encrypted_value": encrypted_data, "associated_label": safe_label}).execute()
                pointer_text = f"[SECURE_VAULT_REF] {safe_label}"
                db.table("notes").insert({"telegram_id": telegram_id, "content": pointer_text, "cleaned_content": safe_label}).execute()
            else:
                db.table("notes").insert({"telegram_id": telegram_id, "content": user_text, "cleaned_content": summary}).execute()
            
            # Text confirmation back to user
            requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", json={
                "chat_id": telegram_id,
                "text": f"🧠 Memory locked in: \"{summary}\""
            })
            trace.update(output=f"Stored memory: {summary}")
            return Response(status_code=status.HTTP_200_OK)
            
        elif intent_action == "query_data":
            # Retrieve notes
            rpc_response = db.table("notes").select("content").eq("telegram_id", telegram_id).limit(5).execute()
            
            retrieved_notes = []
            for match in rpc_response.data:
                note_text = match['content']
                if note_text.startswith("[SECURE_VAULT_REF]"):
                    label = note_text.replace("[SECURE_VAULT_REF] ", "")
                    vault_res = db.table("secure_vault").select("encrypted_value").eq("associated_label", label).eq("telegram_id", telegram_id).execute()
                    if vault_res.data:
                        decrypted_text = decrypt_text(vault_res.data[0]['encrypted_value'])
                        retrieved_notes.append(f"SECURE DOCUMENT ({label}):\n{decrypted_text}")
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

            # Send answer to Telegram
            requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", json={
                "chat_id": telegram_id,
                "text": final_answer
            })
            
            # 🚀 THE NATIVE TRACE HANDOFF
            trace.update(output=final_answer) # Close the trace loop
            context_string = "\n".join(retrieved_notes)
            
            # Pass the explicit trace.id down to your background judge
            background_tasks.add_task(run_rag_evaluation, trace.id, standalone_text, context_string, final_answer)
            
            return Response(status_code=status.HTTP_200_OK)

    except Exception as main_err:
        print(f"❌ Critical Webhook Failure: {str(main_err)}")
        return Response(status_code=status.HTTP_200_OK)