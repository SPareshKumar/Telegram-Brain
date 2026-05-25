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
# It automatically picks up GEMINI_API_KEY from your .env file
client = genai.Client()

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
            model='gemini-1.5-flash',
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