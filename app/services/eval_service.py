import json
from langfuse.client import Langfuse
from app.services.gemini_service import client, types 

# In V3, we must explicitly instantiate the core client to push external scores
langfuse_api = Langfuse()

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
        
        # 🚨 THE V3 SCORING FIX 🚨
        if trace_id:
            langfuse_api.score(
                trace_id=trace_id,
                name="Context-Relevance",
                value=float(scores.get("context_relevance", 0)),
                comment=scores.get("reasoning", "")
            )
            langfuse_api.score(
                trace_id=trace_id,
                name="Groundedness",
                value=float(scores.get("groundedness", 0)),
                comment=scores.get("reasoning", "")
            )
            langfuse_api.flush()
            
        print(f"📊 Eval Complete: Relevance [{scores.get('context_relevance')}] | Groundedness [{scores.get('groundedness')}]")
        
    except Exception as e:
        print(f"⚠️ Background evaluation failed: {str(e)}")