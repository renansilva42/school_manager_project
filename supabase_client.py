# supabase_client.py
from supabase import create_client
import os
from dotenv import load_dotenv

def get_supabase_client():
    load_dotenv()
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env file")
        
    return create_client(
        supabase_url,
        supabase_key
    )