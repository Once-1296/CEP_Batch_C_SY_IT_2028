import os
from dotenv import load_dotenv
import hashlib

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

CORS_ALLOW_ORIGINS = ["*"]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["*"]
CORS_ALLOW_HEADERS = ["*"]

MEDICINES_CSV = "medicines_cleaned.csv"
DRUG_INTERACTIONS_CSV = "drug_interactions_cleaned.csv"
SPACY_MODEL = "en_core_web_sm"

# General Settings stuff 67
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def strip_dosage(salt: str) -> str:
    if not salt:
        return salt
    return salt.split('(')[0].strip()