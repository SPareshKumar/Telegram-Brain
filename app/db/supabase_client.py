import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Extract cloud environment parameters
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("CRITICAL: Missing your SUPABASE_URL or SUPABASE_KEY in the .env configuration file.")

# Initialize the persistent connection client
# Utilizing the service_role secret enables the backend service to bypass frontend RLS policies safely.
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_db() -> Client:
    """Returns the globally configured, singleton Supabase client instance."""
    return supabase