import os
import requests
from fastapi import APIRouter, Request, Response, status, BackgroundTasks
from app.db.supabase_client import get_db
from app.services.gemini_service import analyze_and_extract, generate_rag_response, generate_embedding
from app.services.crypto_service import encrypt_text, decrypt_text
from app.services.eval_service import run_rag_evaluation
from langfuse import get_client

router = APIRouter()
langfuse = get_client()

@router.post("/telegram/webhook")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        payload = await request.json()
        message = payload.get("message", {})
        telegram_id = message.get("from", {}).get("id")
        user_text = message.get("text", "")
        
        if not telegram_id or not user_text:
            return Response(status_code=status.HTTP_200_OK)

        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        db = get_db()

        with langfuse.start_as_current_observation(as_type="span", name="telegram_interaction", input={"user_text": user_text}) as current_op:
            trace_id = langfuse.get_current_trace_id()

            history_res = db.table("chat_history").select("role, content").eq("telegram_id", telegram_id).order("created_at", desc=True).limit(5).execute()
            recent_messages = history_res.data[::-1] 
            chat_context = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in recent_messages])

            ai_response = analyze_and_extract(user_text, chat_context=chat_context)
            
            intent_action = ai_response.get("intent", "query_data")
            is_sensitive = ai_response.get("is_sensitive", False)
            summary = ai_response.get("summary", "New Memory")
            standalone_text = ai_response.get("standalone_query", user_text)

            if intent_action == "error":
                requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", json={"chat_id": telegram_id, "text": "API Congested."})
                current_op.update(output="API 503 Error")
                return Response(status_code=status.HTTP_200_OK)
                
            elif intent_action == "store_data":
                if is_sensitive:
                    safe_label = summary
                    encrypted_data = encrypt_text(user_text)
                    db.table("secure_vault").insert({"telegram_id": telegram_id, "secret_type": "document", "encrypted_value": encrypted_data, "associated_label": safe_label}).execute()
                    pointer_text = f"[SECURE_VAULT_REF] {safe_label}"
                    db.table("notes").insert({"telegram_id": telegram_id, "content": pointer_text, "cleaned_content": safe_label}).execute()
                else:
                    db.table("notes").insert({"telegram_id": telegram_id, "content": user_text, "cleaned_content": summary}).execute()
                
                requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", json={"chat_id": telegram_id, "text": f"🧠 Memory locked in: \"{summary}\""})
                current_op.update(output=f"Stored memory: {summary}")
                return Response(status_code=status.HTTP_200_OK)
                
            elif intent_action == "query_data":
                # 🚨 THE FIX: RESTORING THE HYBRID VECTOR SEARCH 🚨
                query_vector = generate_embedding(standalone_text) 
                # Defensive formatting: stringify the list to match Postgres's expected vector literal format '[...]'
                query_vector_str = str(query_vector)
                
                rpc_response = db.rpc(
                    'match_notes', 
                    {
                        'query_embedding': query_vector_str,
                        'match_threshold': 0.2,
                        'match_count': 5,
                        'p_telegram_id': telegram_id
                    }
                ).execute()
                
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
                
                final_answer = generate_rag_response(
                    question=standalone_text, 
                    context_notes=retrieved_notes, 
                    graph_context=[],
                    chat_context=chat_context
                )
                
                db.table("chat_history").insert([
                    {"telegram_id": telegram_id, "role": "user", "content": user_text},
                    {"telegram_id": telegram_id, "role": "assistant", "content": final_answer}
                ]).execute()

                requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", json={"chat_id": telegram_id, "text": final_answer})
                
                current_op.update(output=final_answer) 
                context_string = "\n".join(retrieved_notes)
                
                background_tasks.add_task(run_rag_evaluation, trace_id, standalone_text, context_string, final_answer)
                return Response(status_code=status.HTTP_200_OK)

    except Exception as main_err:
        print(f"❌ Critical Webhook Failure: {str(main_err)}")
        return Response(status_code=status.HTTP_200_OK)