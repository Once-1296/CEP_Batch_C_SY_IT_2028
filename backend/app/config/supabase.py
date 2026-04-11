from typing import Optional
from supabase import Client, create_client

from app.config.settings import SUPABASE_KEY, SUPABASE_SERVICE_KEY, SUPABASE_URL


supabase: Optional[Client] = None
supabase_admin: Optional[Client] = None


def initialize_supabase_clients() -> None:
    global supabase, supabase_admin

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("WARNING: SUPABASE_URL or SUPABASE_KEY not set. Supabase features will fail.")
        supabase = None
    else:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("Supabase client initialized successfully (anon key).")

    if SUPABASE_URL and SUPABASE_SERVICE_KEY:
        supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        print("Supabase admin client initialized (service_role key).")
    else:
        supabase_admin = None
        print("WARNING: SUPABASE_SERVICE_KEY not set. Admin write operations will fail.")


def get_supabase() -> Optional[Client]:
    return supabase


def get_supabase_admin() -> Optional[Client]:
    return supabase_admin
