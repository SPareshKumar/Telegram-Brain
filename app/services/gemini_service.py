import os
import json
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from langfuse import observe
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

@observe(name="intent_classification")
def classify_text_intent(user_text: str) -> IntentResponse:
    """
    Analyzes the user's raw text to determine their intent and flags sensitive data.
    The @observe decorator automatically sends trace telemetry to your Langfuse dashboard.
    """
    
    system_prompt = f"""
    You are the classification routing engine for a Digital Second Brain.
    Analyze the user's input.
    - If they are providing information to remember, output 'store_data'.
    - If they are asking a question to retrieve information, output 'query_data'.
    
    User Input: "{user_text}"
    """
    
    try:
        # Call Gemini 1.5 Flash for high-speed routing
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=system_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=IntentResponse,
                temperature=0.1, # Keep temperature low for deterministic routing
            ),
        )
        
        # Parse the JSON string returned by Gemini into our Pydantic model
        result = IntentResponse.model_validate_json(response.text)
        return result
        
    except Exception as e:
        # Fallback safeguard in case of API failure
        print(f"Gemini Routing Error: {e}")
        return IntentResponse(
            action="store_data", 
            is_sensitive=False, 
            summary="Unclassified payload"
        )
    

@observe(name="generate_vector")
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
    
@observe(name="rag_synthesis")
def generate_rag_response(question: str, context_notes: list[str]) -> str:
    """
    Takes the retrieved database notes and synthesizes a natural language answer.
    """
    # Combine the retrieved notes into a single context block
    context_text = "\n- ".join(context_notes)
    
    system_prompt = f"""
    You are the voice of the user's Digital Second Brain.
    Answer the user's question using ONLY the provided context notes.
    If the answer is not contained in the notes, say "I don't have that in my memory."
    Keep your answer concise, conversational, and direct.
    
    CONTEXT NOTES:
    - {context_text}
    
    USER QUESTION:
    {question}
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=system_prompt,
        )
        return response.text
    except Exception as e:
        print(f"❌ RAG Generation Error: {e}")
        return "I'm having trouble thinking right now. Please try again."
    

@observe(name="multimodal_extraction")
def extract_media_content(local_file_path: str, media_type: str, user_caption: str = "") -> str:
    """
    Uploads media to Gemini, extracts the context/text, and returns a comprehensive summary.
    """
    try:
        # 1. Upload the file to Google's temporary generative storage
        print(f"Uploading {media_type} to Gemini...")
        uploaded_file = client.files.upload(file=local_file_path)
        
        # 2. Craft a dynamic prompt based on the media type
        prompt = f"Analyze this {media_type}."
        if user_caption:
            prompt += f" The user provided this context: '{user_caption}'."
            
        prompt += """
        Provide a highly detailed, comprehensive text extraction and summary of this file. 
        If it's an image of text or a PDF, transcribe the important parts. 
        If it's audio/video, summarize the transcription and visual events.
        Make it detailed enough that a vector search engine can index it accurately.
        """
        
        # 3. Generate the extraction using our current 3.5-flash model
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=[uploaded_file, prompt]
        )
        
        # 4. Clean up Google's servers by deleting the file after processing
        client.files.delete(name=uploaded_file.name)
        
        return response.text
        
    except Exception as e:
        print(f"❌ Media Extraction Error: {e}")
        return f"Failed to extract content from the {media_type}."