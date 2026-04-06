from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import spacy
from fuzzywuzzy import process
import json
import re
# Add these to your existing imports
import sqlite3
import hashlib



# 1. Initialize FastAPI and CORS (crucial for React frontend)
app = FastAPI(title="Ayush-Guard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For prototyping only; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --- ADD THIS AFTER YOUR CORS SETUP ---
# 1. Initialize Auth Database
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

class UserAuth(BaseModel):
    username: str
    password: str
# 2. Load Data and Models
print("Loading datasets and models...")
try:
    df_medicines = pd.read_csv("medicines_cleaned.csv")
    with open("mock_rules.json", "r") as f:
        mock_rules = json.load(f)
    with open("mock_patients.json", "r") as f:
        mock_patients = json.load(f)
    
    # Load basic spacy model (make sure you ran: python -m spacy download en_core_web_sm)
    nlp = spacy.load("en_core_web_sm")
except Exception as e:
    print(f"Startup Error: {e}. Did you run setup_data.py?")

# 3. Pydantic Models for API Requests/Responses
class DrugCheckRequest(BaseModel):
    pharmacist_query: str
    patient_id: str

# 4. Core Logic Functions
def normalize_input(query: str) -> str:
    """Uses NLP to strip out forms, dosages, and noise from the input."""
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

def resolve_entity(clean_query: str):
    """Uses FuzzyWuzzy to snap the normalized query to the closest database match."""
    # Extract the best match from the 'name' column
    best_match, score, index = process.extractOne(clean_query, df_medicines['name'])
    
    # If the score is decent, fetch the generic salt and class
    if score > 70:
        row = df_medicines.iloc[index]
        return {
            "brand_matched": best_match,
            "generic_salt": row['generic_salt'],
            "therapeutic_class": row['therapeutic_class'],
            "match_score": score
        }
    return None

# 5. The Safety Endpoint
@app.post("/api/check-drug")
async def check_drug_safety(req: DrugCheckRequest):
    # Step A: Validate Patient
    patient = mock_patients.get(req.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient ABHA ID not found")
    # print(patient)
    # Step B: Normalize & Resolve Input
    clean_query = normalize_input(req.pharmacist_query)
    resolved_drug = resolve_entity(clean_query)
    # print(clean_query)
    if not resolved_drug:
        return {"status": "error", "message": "Could not confidently identify the medicine."}

    target_salt = resolved_drug["generic_salt"]
    # print(target_salt)
    # Step C: The Safety Engine (Cross-referencing rules)
    alert = {
        "severity_tier": "Green", # Default to safe
        "message": "Safe to dispense.",
        "resolved_data": resolved_drug,
        "suggested_alternative": None
    }

    # 1. Check Condition Interactions
    for rule in mock_rules["drug_condition_interactions"]:
        if target_salt in rule["salt"] and rule["condition"] in patient["active_conditions"]:
            alert["severity_tier"] = rule["severity"]
            alert["message"] = rule["alert_message"]
            
            # Find an alternative from the same therapeutic class
            alt_df = df_medicines[(df_medicines['therapeutic_class'] == rule["suggested_alternative_class"]) & 
                                  (~df_medicines['generic_salt'].str.contains(target_salt, na=False))]
            if not alt_df.empty:
                alert["suggested_alternative"] = alt_df.iloc[0]['name']
            return alert # Break early on a condition conflict

    # 2. Check Drug-Drug Interactions
    for rule in mock_rules["drug_drug_interactions"]:
        if target_salt in [rule["salt_a"], rule["salt_b"]]:
            interacting_salt = rule["salt_b"] if target_salt == rule["salt_a"] else rule["salt_a"]
            # Check if patient is taking the interacting salt
            # (In a real app, you'd map patient meds to salts first. For prototype, we check direct names)
            for current_med in patient["current_medications"]:
                if interacting_salt.lower() in current_med.lower():
                    alert["severity_tier"] = rule["severity"]
                    alert["message"] = rule["alert_message"]
                    return alert

    return alert

# Run this file with: uvicorn main:app --reload


@app.post("/api/signup")
async def signup(user: UserAuth):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                       (user.username, hash_password(user.password)))
        conn.commit()
        return {"status": "success", "message": "Pharmacist registered successfully"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists")
    finally:
        conn.close()

@app.post("/api/login")
async def login(user: UserAuth):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username = ?", (user.username,))
    row = cursor.fetchone()
    conn.close()
    
    if row and row[0] == hash_password(user.password):
        # In a real app, return a JWT token here. For prototype, a success flag is fine.
        return {"status": "success", "token": f"fake-jwt-token-for-{user.username}"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

# --- YOUR EXISTING /api/check-drug ENDPOINT GOES HERE ---