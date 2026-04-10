# ─────────────────────────────────────────────────────────────────────────────
# Ayush-Guard — FastAPI Backend (main.py)
# Complete rewrite: Supabase auth (admin/pharmacist roles), local CSV-based
# medicine lookup + DDI check, Supabase patient management with consent flow.
# ─────────────────────────────────────────────────────────────────────────────

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
import spacy
from fuzzywuzzy import process, fuzz
import hashlib
import os

# CHANGED: Load .env file so SUPABASE_URL and SUPABASE_KEY are available
from dotenv import load_dotenv
load_dotenv()

# CHANGED: Import Supabase client (replaces sqlite3 entirely)
from supabase import create_client, Client


# ─────────────────────────────────────────────────────────────────────────────
# 1. Initialize FastAPI and CORS
# ─────────────────────────────────────────────────────────────────────────────
app = FastAPI(title="Ayush-Guard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For prototyping only; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────────────────────
# 2. Supabase Client Initialization
# CHANGED: All user/patient data now lives in Supabase instead of SQLite/JSON
# ─────────────────────────────────────────────────────────────────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
# CHANGED: Service role key bypasses RLS — needed for admin write operations
# (INSERT into admins/pharmacists tables, which RLS blocks for the anon key)
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("WARNING: SUPABASE_URL or SUPABASE_KEY not set. Supabase features will fail.")
    supabase: Client = None
else:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("Supabase client initialized successfully (anon key).")

# CHANGED: Admin client with service_role key — used for writes to admins/pharmacists tables
if SUPABASE_URL and SUPABASE_SERVICE_KEY:
    supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    print("Supabase admin client initialized (service_role key).")
else:
    supabase_admin = None
    print("WARNING: SUPABASE_SERVICE_KEY not set. Admin write operations will fail.")


# ─────────────────────────────────────────────────────────────────────────────
# 3. SHA-256 Hashing Utility
# CHANGED: Rewritten cleanly — same logic as before, just no SQLite context
# ─────────────────────────────────────────────────────────────────────────────
def hash_password(password: str) -> str:
    """Hash a password using SHA-256. Used for admin, pharmacist, and patient passwords."""
    return hashlib.sha256(password.encode()).hexdigest()


# ─────────────────────────────────────────────────────────────────────────────
# 4. Load CSVs and Build O(1) Lookup Dictionaries at Startup
# CHANGED: Removed mock_rules.json and mock_patients.json loading entirely
# CHANGED: Build dictionaries from DataFrames instead of O(n) scans per request
# ─────────────────────────────────────────────────────────────────────────────
print("Loading datasets and models...")
try:
    # Load medicines CSV — columns: brand_name, primary_salt
    df_medicines = pd.read_csv("medicines_cleaned.csv")

    # CHANGED: Build O(1) lookup dictionary from CSV — brand_name (lowercased) → primary_salt
    # This replaces all DataFrame scans for salt resolution
    brand_to_salt = dict(zip(
        df_medicines['brand_name'].str.lower(),
        df_medicines['primary_salt']
    ))
    brand_name_list = list(brand_to_salt.keys())
    print(f"Loaded {len(brand_name_list)} brand names from medicines_cleaned.csv")

    # Load drug interactions CSV — columns: drug_a, drug_b, severity, clinical_effect, safer_alternative
    df_interactions = pd.read_csv("drug_interactions_cleaned.csv")

    # CHANGED: Build O(1) DDI lookup dictionaries keyed by drug_a and drug_b (lowercased)
    # Each key maps to a list of interaction rows for that drug
    ddi_by_drug_a = {}
    ddi_by_drug_b = {}
    for _, row in df_interactions.iterrows():
        row_dict = row.to_dict()
        a_key = str(row['drug_a']).lower()
        b_key = str(row['drug_b']).lower()
        ddi_by_drug_a.setdefault(a_key, []).append(row_dict)
        ddi_by_drug_b.setdefault(b_key, []).append(row_dict)
    print(f"Loaded {len(df_interactions)} drug interaction rules from drug_interactions_cleaned.csv")

    # Load spaCy model for input normalization (unchanged)
    nlp = spacy.load("en_core_web_sm")

except Exception as e:
    print(f"Startup Error: {e}. Did you run setup_data.py and download spaCy model?")


# ─────────────────────────────────────────────────────────────────────────────
# 5. Pydantic Models for API Requests
# CHANGED: Replaced single UserAuth with role-specific models + patient models
# ─────────────────────────────────────────────────────────────────────────────

# Auth models
class LoginRequest(BaseModel):
    username: str
    password: str

class AddPharmacistRequest(BaseModel):
    name: str
    username: str
    password: str
    phone: str

class AddAdminRequest(BaseModel):
    name: str
    username: str
    password: str

# Patient models
class CreatePatientRequest(BaseModel):
    name: str
    phone: str
    password: str
    current_medications: List[str] = []
    current_conditions: List[str] = []
    added_by: str  # pharmacist username who added this patient

class UpdatePatientRequest(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    current_medications: Optional[List[str]] = None
    current_conditions: Optional[List[str]] = None

class VerifyPatientRequest(BaseModel):
    patient_id: int
    password: str

# Safety check model (unchanged shape — patient_id is now a Supabase integer ID)
class DrugCheckRequest(BaseModel):
    pharmacist_query: str
    patient_id: str  # kept as str for API compat — will be cast to int internally


# ─────────────────────────────────────────────────────────────────────────────
# 6. Core Logic Functions
# ─────────────────────────────────────────────────────────────────────────────

def normalize_input(query: str) -> str:
    """Uses NLP to strip out forms, dosages, and noise from the input."""
    # UNTOUCHED — kept exactly as-is per spec
    doc = nlp(query.lower())

    # Common pharmacy noise words
    noise_words = {'tab', 'tablet', 'cap', 'capsule', 'syp', 'syrup', 'mg', 'ml', 'drop', 'drops'}

    clean_tokens = []
    for token in doc:
        # Ignore numbers, punctuation, and noise words
        if not token.like_num and not token.is_punct and token.text not in noise_words:
            clean_tokens.append(token.text)

    clean_string = " ".join(clean_tokens)
    # Fallback if the NLP stripped everything
    return clean_string if clean_string else query.split()[0]


def strip_dosage(salt: str) -> str:
    """Strip dosage info from a salt name for clean DDI comparison.
    e.g. 'Atorvastatin (10mg)' → 'Atorvastatin'
         'Amoxycillin  (500mg)' → 'Amoxycillin'
    medicines_cleaned.csv primary_salt includes dosage in parens;
    drug_interactions_cleaned.csv uses bare salt names — this bridges them."""
    if not salt:
        return salt
    # Strip everything from the first '(' onward, then strip whitespace
    return salt.split('(')[0].strip()


def resolve_entity(clean_query: str):
    """Uses FuzzyWuzzy to snap the normalized query to the closest brand_name from CSV.
    CHANGED: Now uses brand_name_list from CSV (lowercased) and brand_to_salt dict for O(1) salt lookup.
    Removed therapeutic_class from return value."""
    if not brand_name_list:
        return None

    # FuzzyWuzzy matches against brand_name_list (from CSV, lowercased)
    best_match, score = process.extractOne(clean_query, brand_name_list)[:2]

    # Same 70 score threshold as before
    if score > 70:
        # CHANGED: O(1) dictionary lookup instead of DataFrame scan or Supabase query
        raw_salt = brand_to_salt.get(best_match)
        # CHANGED: Strip dosage so DDI dict keys match — 'Atorvastatin (10mg)' → 'Atorvastatin'
        primary_salt = strip_dosage(raw_salt) if raw_salt else raw_salt

        return {
            "brand_matched": best_match,
            "generic_salt": primary_salt,      # dosage-stripped for clean DDI comparison
            "match_score": score
        }
    return None


def resolve_patient_meds_to_salts(medications: list) -> list:
    """For each medication in the patient's list, resolve to generic salt using the
    exact same pipeline as resolve_entity() for consistency.
    CHANGED: ADDENDUM 4 - Consistent preprocessing pipeline."""
    resolved_salts = []
    for med_name in medications:
        # Step 1: normalize_input
        clean_query = normalize_input(med_name)
        
        # Step 2 & 3: FuzzyWuzzy match > 70 and O(1) lookup in brand_to_salt
        resolved_drug = resolve_entity(clean_query)
        
        if resolved_drug and resolved_drug["generic_salt"]:
            resolved_salts.append(resolved_drug["generic_salt"])
        else:
            # Step 4: Fall back to original name if score < 70
            # Also apply strip_dosage to fallback to ensure consistent DDI matching
            resolved_salts.append(strip_dosage(med_name))
            
    return resolved_salts


# ─────────────────────────────────────────────────────────────────────────────
# 7. Auth Endpoints
# CHANGED: Replaced SQLite-based /api/signup and /api/login with Supabase-based
#          role auth. Signup removed entirely — only admin can add users.
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/login")
async def login(req: LoginRequest):
    """CHANGED: Login checks admins table first, then pharmacists table in Supabase.
    Returns role alongside token so frontend can route accordingly.
    No self-signup — removed entirely."""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    hashed = hash_password(req.password)

    # Check admins table first
    admin_res = supabase.table("admins").select("id, name, username, password").eq("username", req.username).execute()
    if admin_res.data and len(admin_res.data) > 0:
        admin = admin_res.data[0]
        if admin["password"] == hashed:
            return {
                "status": "success",
                "token": f"fake-jwt-{req.username}",
                "role": "admin",
                "name": admin["name"]
            }

    # Check pharmacists table second
    pharm_res = supabase.table("pharmacists").select("id, name, username, password").eq("username", req.username).execute()
    if pharm_res.data and len(pharm_res.data) > 0:
        pharmacist = pharm_res.data[0]
        if pharmacist["password"] == hashed:
            return {
                "status": "success",
                "token": f"fake-jwt-{req.username}",
                "role": "pharmacist",
                "name": pharmacist["name"]
            }

    # Not found in either table
    raise HTTPException(status_code=401, detail="Invalid username or password")


@app.post("/api/admin/add-pharmacist")
async def add_pharmacist(req: AddPharmacistRequest):
    """CHANGED: Admin-only endpoint to create a new pharmacist account.
    Inserts into Supabase pharmacists table with SHA-256 hashed password.
    Uses supabase_admin (service_role key) to bypass RLS which blocks INSERT for anon key."""
    if not supabase_admin:
        raise HTTPException(status_code=500, detail="Supabase service key not configured — cannot write to pharmacists table")

    # Check if username already exists (anon key can SELECT)
    existing = supabase.table("pharmacists").select("id").eq("username", req.username).execute()
    if existing.data and len(existing.data) > 0:
        raise HTTPException(status_code=400, detail="Username already taken")

    # CHANGED: Use supabase_admin (service_role) to bypass RLS for INSERT
    insert_data = {
        "name": req.name,
        "username": req.username,
        "password": hash_password(req.password),
        "phone": req.phone,
    }
    result = supabase_admin.table("pharmacists").insert(insert_data).execute()

    return {"status": "success", "message": f"Pharmacist '{req.name}' added successfully"}


@app.post("/api/admin/add-admin")
async def add_admin(req: AddAdminRequest):
    """CHANGED: Endpoint to create a new admin account.
    Inserts into Supabase admins table with SHA-256 hashed password.
    Uses supabase_admin (service_role key) to bypass RLS which blocks INSERT for anon key."""
    if not supabase_admin:
        raise HTTPException(status_code=500, detail="Supabase service key not configured — cannot write to admins table")

    # Check if username already exists (anon key can SELECT)
    existing = supabase.table("admins").select("id").eq("username", req.username).execute()
    if existing.data and len(existing.data) > 0:
        raise HTTPException(status_code=400, detail="Username already taken")

    # CHANGED: Use supabase_admin (service_role) to bypass RLS for INSERT
    insert_data = {
        "name": req.name,
        "username": req.username,
        "password": hash_password(req.password),
    }
    result = supabase_admin.table("admins").insert(insert_data).execute()

    return {"status": "success", "message": f"Admin '{req.name}' added successfully"}


# ─────────────────────────────────────────────────────────────────────────────
# 8. Patient CRUD Endpoints
# CHANGED: Patients come from Supabase instead of mock_patients.json
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/patients")
async def list_patients():
    """CHANGED: Fetch all patients from Supabase patients table.
    Returns id, name, phone, current_medications, current_conditions, added_by.
    current_medications and current_conditions are PostgreSQL TEXT[] — they come
    back as Python lists from the Supabase client automatically."""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    result = supabase.table("patients").select(
        "id, name, phone, current_medications, current_conditions, added_by"
    ).execute()

    return {"patients": result.data or []}


@app.post("/api/patients")
async def create_patient(req: CreatePatientRequest):
    """CHANGED: Create a new patient in Supabase.
    current_medications and current_conditions are sent as JSON arrays from frontend —
    Supabase Python client handles TEXT[] serialization automatically when given a Python list."""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    insert_data = {
        "name": req.name,
        "phone": req.phone,
        "password": hash_password(req.password),
        "current_medications": req.current_medications,   # Python list → PostgreSQL TEXT[]
        "current_conditions": req.current_conditions,      # Python list → PostgreSQL TEXT[]
        "added_by": req.added_by,
    }
    result = supabase.table("patients").insert(insert_data).execute()

    if result.data and len(result.data) > 0:
        return {"status": "success", "patient": result.data[0]}
    raise HTTPException(status_code=500, detail="Failed to create patient")


@app.put("/api/patients/{patient_id}")
async def update_patient(patient_id: int, req: UpdatePatientRequest):
    """CHANGED: Update a patient record in Supabase by id.
    Only updates fields that are provided (non-None)."""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    update_data = {}
    if req.name is not None:
        update_data["name"] = req.name
    if req.phone is not None:
        update_data["phone"] = req.phone
    if req.current_medications is not None:
        update_data["current_medications"] = req.current_medications  # list → TEXT[]
    if req.current_conditions is not None:
        update_data["current_conditions"] = req.current_conditions    # list → TEXT[]

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = supabase.table("patients").update(update_data).eq("id", patient_id).execute()

    if result.data and len(result.data) > 0:
        return {"status": "success", "patient": result.data[0]}
    raise HTTPException(status_code=404, detail="Patient not found")


@app.post("/api/patients/verify")
async def verify_patient(req: VerifyPatientRequest):
    """CHANGED: Consent verification — patient enters their password at the counter
    before their record is unlocked. Compares SHA-256 hashes."""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    result = supabase.table("patients").select("id, password").eq("id", req.patient_id).execute()

    if not result.data or len(result.data) == 0:
        raise HTTPException(status_code=404, detail="Patient not found")

    stored_hash = result.data[0]["password"]
    input_hash = hash_password(req.password)

    return {"verified": stored_hash == input_hash}


# ─────────────────────────────────────────────────────────────────────────────
# 9. The Safety Endpoint
# CHANGED: Patient now fetched from Supabase instead of mock_patients.json
# CHANGED: Drug-condition check (Step C.1) removed entirely per Addendum 3
# CHANGED: DDI check uses O(1) dictionary lookup instead of Supabase queries
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/check-drug")
async def check_drug_safety(req: DrugCheckRequest):
    """Safety check endpoint. Resolves medicine via FuzzyWuzzy against CSV,
    then checks DDI against drug_interactions_cleaned.csv lookup dicts."""

    # Step A: Validate Patient — CHANGED: fetch from Supabase instead of mock_patients.json
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    try:
        patient_id_int = int(req.patient_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid patient ID format")

    patient_res = supabase.table("patients").select(
        "id, name, current_medications, current_conditions"
    ).eq("id", patient_id_int).execute()

    if not patient_res.data or len(patient_res.data) == 0:
        raise HTTPException(status_code=404, detail="Patient not found")

    patient = patient_res.data[0]

    # Step B: Normalize & Resolve Input (unchanged logic)
    clean_query = normalize_input(req.pharmacist_query)
    resolved_drug = resolve_entity(clean_query)

    if not resolved_drug:
        return {"status": "error", "message": "Could not confidently identify the medicine."}

    target_salt = resolved_drug["generic_salt"]

    # CHANGED: ADDENDUM 6 - Default honest message
    alert = {
        "severity_tier": "Green",          # Default to safe
        "message": "No known interaction found in database. Verify independently before dispensing.",
        "resolved_data": resolved_drug,
        "suggested_alternative": None
    }

    # CHANGED: DDI check using Fuzzy matching against keys (ADDENDUM 5)
    if target_salt:
        target_salt_lower = target_salt.lower()

        # Resolve patient's current_medications to dosage-stripped generic salts
        patient_meds = patient.get("current_medications", []) or []
        patient_salts = resolve_patient_meds_to_salts(patient_meds)

        matched_rows = []
        
        # Fuzzy match target_salt against DDI keys (threshold 85)
        all_ddi_keys_a = list(ddi_by_drug_a.keys())
        all_ddi_keys_b = list(ddi_by_drug_b.keys())
        
        matches_a = [match for match, score in process.extract(target_salt_lower, all_ddi_keys_a, limit=None) if score >= 85]
        matches_b = [match for match, score in process.extract(target_salt_lower, all_ddi_keys_b, limit=None) if score >= 85]
        
        for k in matches_a:
            matched_rows.extend(ddi_by_drug_a.get(k, []))
        for k in matches_b:
            matched_rows.extend(ddi_by_drug_b.get(k, []))

        for row in matched_rows:
            # Determine the interacting drug (the OTHER one in the pair)
            drug_a = str(row.get("drug_a", ""))
            drug_b = str(row.get("drug_b", ""))
            
            # Since we fuzzy matched, we find which one is the target
            score_a = fuzz.ratio(drug_a.lower(), target_salt_lower)
            score_b = fuzz.ratio(drug_b.lower(), target_salt_lower)
            
            if score_a >= score_b: # drug_a was the matched target
                interacting_salt = drug_b
            else:
                interacting_salt = drug_a
                
            interacting_salt = strip_dosage(interacting_salt)

            # CHANGED: Salt-to-salt fuzzy comparison against patient's resolved medications
            for pat_salt in patient_salts:
                # Fuzzy match between interacting_salt from rules and patient's salt
                score_pat = fuzz.ratio(interacting_salt.lower(), pat_salt.lower())
                if score_pat >= 85:
                    # CHANGED: Map CSV severity (Major/Moderate/Minor) to frontend format (Red/Yellow/Green)
                    csv_severity = row.get("severity", "Moderate")
                    severity_map = {"Major": "Red", "Moderate": "Yellow", "Minor": "Green"}
                    alert["severity_tier"] = severity_map.get(csv_severity, csv_severity)
                    alert["message"] = row.get("clinical_effect", "Drug interaction detected.")
                    alert["suggested_alternative"] = row.get("safer_alternative")
                    return alert  # Return on first DDI match

    return alert


# ─────────────────────────────────────────────────────────────────────────────
# Run with: uvicorn main:app --reload
# Make sure to source .env first: source .env && uvicorn main:app --reload
# ─────────────────────────────────────────────────────────────────────────────