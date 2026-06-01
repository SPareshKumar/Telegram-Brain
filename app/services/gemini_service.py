import os
import json
import time
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the Gemini Client
# Force the client to use the exact key from the .env file
gemini_key = os.getenv("GEMINI_API_KEY")
if not gemini_key:
    raise ValueError("GEMINI_API_KEY is completely missing from the environment variables.")

client = genai.Client(api_key=gemini_key)

# Define the strict JSON structure we want Gemini to return
class IntentResponse(BaseModel):
    action: str = Field(description="Must be strictly 'store_data' or 'query_data'")
    is_sensitive: bool = Field(description="True ONLY if the text contains passwords, pins, API keys, or financial data")
    summary: str = Field(description="A clean, 5-word summary of the payload")

# Define our cascade hierarchy using currently active models
FALLBACK_MODELS = [
    'gemini-3.5-flash',
    'gemini-2.5-flash',
    'gemini-2.5-flash-lite'
]

def analyze_and_extract(text: str, chat_context: str = "") -> dict:
    """
    Consolidates Intent Classification, Graph Extraction, and Contextual Query Rewriting 
    into a single efficient call.
    """
    prompt = f"""
    Analyze the following text and perform THREE tasks:
    1. Contextual Rewrite: If the user text contains pronouns (he, she, it, they, this) referencing the recent conversation, rewrite the text replacing the pronouns with the actual names. If it is already standalone, leave it identical.
    2. Determine if the user is asking a question (query_data) or sharing information to be saved (store_data).
    3. Extract a Knowledge Graph (nodes and edges) from the standalone text.
    
    Return ONLY a valid JSON object matching this exact schema:
    {{
        "standalone_query": "The rewritten, context-aware text",
        "intent": "store_data" or "query_data",
        "is_sensitive": false,
        "summary": "Brief 5-word summary",
        "nodes": [
            {{"name": "Concept 1", "type": "Technology/Person/Team"}}
        ],
        "edges": [
            {{"source": "Concept 1", "target": "Concept 2", "relationship": "plays for / uses / etc"}}
        ]
    }}

    RECENT CONVERSATION (Use for pronoun resolution):
    {chat_context if chat_context else "No recent conversation."}

    TEXT TO ANALYZE:
    {text}
    """

    # Iterate through our models from heaviest to lightest
    for attempt, model_name in enumerate(FALLBACK_MODELS):
        try:
            print(f"🧠 Routing Analysis to {model_name}...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            return json.loads(response.text)
            
        except Exception as e:
            error_msg = str(e)
            print(f"⚠️ {model_name} Failed: {error_msg}")
            if "503" in error_msg or "429" in error_msg:
                if attempt < len(FALLBACK_MODELS) - 1:
                    time.sleep(1)
                    continue 
            break
            
    return {"standalone_query": text, "intent": "error", "is_sensitive": False, "summary": "System Error", "nodes": [], "edges": []}
    

def generate_embedding(text: str) -> list[float]:
    """
    Converts cleartext into a 768-dimensional mathematical vector.
    Uses gemini-embedding-2 with forced output truncation to match our database schema.
    """
    try:
        # Use Google's latest embedding model and explicitly compress to 768 dimensions
        result = client.models.embed_content(
            model='gemini-embedding-2',
            contents=text,
            config=types.EmbedContentConfig(output_dimensionality=768)
        )
        # Extract the raw floating-point array
        return result.embeddings[0].values
        
    except Exception as e:
        print(f"❌ Vector Generation Error: {e}")
        return []
    
def generate_rag_response(question: str, context_notes: list[str], graph_context: list[str], chat_context: str = "") -> str:
    """
    Synthesizes a final answer using semantic vectors, graph relationships, and short-term chat history.
    """
    notes_text = "\n- ".join(context_notes) if context_notes else "No specific notes found."
    graph_text = "\n- ".join(graph_context) if graph_context else "No graph relationships found."
    history_text = chat_context if chat_context else "No recent conversation history."
    system_prompt = f"""
    You are the voice of the user's Digital Second Brain.
    Answer the user's question using the provided context. 
    
    You have three types of memory to pull from:
    
    1. SHORT-TERM CONVERSATION (Recent Chat Context):
    {history_text}
    
    2. RAW MEMORIES (Semantic Search):
    - {notes_text}
    
    3. KNOWLEDGE GRAPH (Relational Connections):
    - {graph_text}
    
    Synthesize this information into a concise, conversational, and direct answer. 
    Use the short-term conversation to understand pronouns or context (e.g., if the user says "how old is he?", figure out who "he" is from the recent chat).
    If the answer isn't in any of the memory banks, say you don't know.
    
    USER QUESTION:
    {question}
    """

    # Iterate through our models
    for attempt, model_name in enumerate(FALLBACK_MODELS):
        try:
            print(f"🗣️ Synthesizing response using {model_name}...")
            response = client.models.generate_content(
                model=model_name,
                contents=system_prompt,
            )
            return response.text
        except Exception as e:
            error_msg = str(e)
            print(f"⚠️ RAG Synthesis {model_name} Failed: {error_msg}")

            if "503" in error_msg or "429" in error_msg:
                if attempt < len(FALLBACK_MODELS) - 1:
                    time.sleep(1)
                    continue
            break

    return "My neural pathways are severely congested right now. Please try asking again in a minute!"
    

def extract_media_content(local_file_path: str, media_type: str, user_caption: str = "") -> str:
    """
    Uploads media to Gemini, extracts the context/text, and returns a comprehensive summary.
    """
    try:
        # 1. Manually map the MIME type to prevent Docker "slim" container errors
        explicit_mime = None
        if local_file_path.endswith('.ogg'):
            explicit_mime = 'audio/ogg'
        elif local_file_path.endswith('.jpg'):
            explicit_mime = 'image/jpeg'
        elif local_file_path.endswith('.mp4'):
            explicit_mime = 'video/mp4'
        elif local_file_path.endswith('.pdf'):
            explicit_mime = 'application/pdf'

        # 2. Upload the file, passing the mime_type via the config object
        print(f"Uploading {media_type} to Gemini (MIME: {explicit_mime})...")
        
        if explicit_mime:
            uploaded_file = client.files.upload(
                file=local_file_path, 
                config=types.UploadFileConfig(mime_type=explicit_mime)
            )
        else:
            uploaded_file = client.files.upload(file=local_file_path)
        
        # 3. Craft a dynamic prompt based on the media type
        prompt = f"Analyze this {media_type}."
        if user_caption:
            prompt += f" The user provided this context: '{user_caption}'."
            
        prompt += """
        Provide a highly detailed, comprehensive text extraction and summary of this file. 
        If it's an image of text or a PDF, transcribe the important parts. 
        If it's audio/video, summarize the transcription and visual events.
        Make it detailed enough that a vector search engine can index it accurately.
        """
        
        # 4. Generate the extraction
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=[uploaded_file, prompt]
        )
        
        # 5. Clean up Google's servers
        client.files.delete(name=uploaded_file.name)
        
        return response.text
        
    except Exception as e:
        print(f"❌ Media Extraction Error: {e}")
        return f"Failed to extract content from the {media_type}."
    

def extract_entities_and_relationships(text: str) -> dict:
    """
    Forces the LLM to extract a Knowledge Graph from the text in strict JSON format.
    """
    prompt = f"""
    Analyze the following text and extract a Knowledge Graph.
    Identify the core entities (nodes) and how they relate to each other (edges).
    
    Return ONLY a valid JSON object matching this exact schema:
    {{
        "nodes": [
            {{"name": "Concept 1", "type": "Technology/Person/Company/etc"}}
        ],
        "edges": [
            {{"source": "Concept 1", "target": "Concept 2", "relationship": "uses / relates to / is required for"}}
        ]
    }}

    TEXT TO ANALYZE:
    {text}
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"❌ Graph Extraction Error: {e}")
        return {"nodes": [], "edges": []}