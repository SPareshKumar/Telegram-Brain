import json
# 🚨 THE V3 FIX: Use get_client again
from langfuse import get_client
from app.services.gemini_service import client, types 

# Initialize the client
langfuse = get_client()

def run_rag_evaluation(trace_id: str, query: str, context: str, response: str):
    print(f"⚖️ Running background evaluation for trace: {trace_id}")
    
    prompt = f"""
    You are an impartial AI judge evaluating a Retrieval-Augmented Generation (RAG) system.
    Evaluate the following interaction based on two metrics:
    
    1. Context Relevance: Does the retrieved context contain information relevant to the user's query? (Score 0.0 to 1.0)
    2. Groundedness: Is the generated response completely supported by the retrieved context? (Score 0.0 to 1.0)
    
    User Query: {query}
    Retrieved Context: {context}
    Generated Response: {response}
    
    Return ONLY a JSON object matching this schema:
    {{
        "context_relevance": 0.9,
        "groundedness": 1.0,
        "reasoning": "Brief 1-sentence explanation of the scores."
    }}
    """
    
    try:
        eval_response = client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        scores = json.loads(eval_response.text)
        
        # 🚨 THE SMOKING GUN: It is create_score(), not score()! 🚨
        if trace_id:
            langfuse.create_score(
                trace_id=trace_id,
                name="Context-Relevance",
                value=float(scores.get("context_relevance", 0)),
                comment=scores.get("reasoning", "")
            )
            langfuse.create_score(
                trace_id=trace_id,
                name="Groundedness",
                value=float(scores.get("groundedness", 0)),
                comment=scores.get("reasoning", "")
            )
            
            # V3 uses flush() to force the background thread to send the API request immediately
            langfuse.flush()
            
        print(f"📊 Eval Complete: Relevance [{scores.get('context_relevance')}] | Groundedness [{scores.get('groundedness')}]")
        
    except Exception as e:
        print(f"⚠️ Background evaluation failed: {str(e)}")