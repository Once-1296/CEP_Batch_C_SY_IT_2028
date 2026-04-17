import json
from fastapi import HTTPException
from app.config.supabase import get_supabase
from app.controllers.schema import DrugCheckRequest

# Load Pre-processed Deterministic Maps
# (In production, these would be cached in Redis or loaded on app startup)
def load_json_map(filepath):
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {} # Fallback if not generated yet

BRAND_MAP = load_json_map("data/brand_to_salt.json")
DDI_MAP = load_json_map("data/ddi_map.json")
CLINICAL_MAP = load_json_map("data/clinical_map.json")

async def check_drug_safety(req: DrugCheckRequest):
    supabase = get_supabase()
    if not supabase: raise HTTPException(status_code=500, detail="Supabase not configured")

    # 1. Fetch Patient
    patient_res = supabase.table("patients").select("id, name, abha_id").eq("id", req.patient_id).execute()
    if not patient_res.data: raise HTTPException(status_code=404, detail="Patient not found")
    abha_id = req.abha_id or patient_res.data[0].get("abha_id")

    # 2. Resolve Drug Deterministically (Brand -> Salts)
    query = req.pharmacist_query.lower().strip()
    target_salts = BRAND_MAP.get(query, [query]) # E.g., "augmentin" -> ["amoxycillin", "clavulanic acid"]

    # 3. Fetch ABDM Profile
    abdm_res = supabase.table("abdm_mock_records").select("*").eq("abha_id", abha_id).execute()
    record = abdm_res.data[0] if abdm_res.data else {}
    
    active_meds = [m.get("medication_name", "").lower() for m in record.get("medication_history", []) if m.get("status") in ["active", "current"]]
    conditions = [c.get("condition", "").lower() for c in record.get("pre_existing_conditions", [])]
    allergies = [a.get("allergen", "").lower() for a in record.get("allergies", [])]
    genotypes = record.get("basic_health_details", {}).get("genotype_markers", {})

    highest_risk_score = 0.0
    alerts = []
    severity_tier = "Green"

    # 4. DIRECT ALLERGIES (Score: 0.99)
    for salt in target_salts:
        for allergy in allergies:
            if salt in allergy or allergy in salt:
                return compile_response("Red", 0.99, f"CRITICAL: Patient has explicit allergy to {salt.title()}.", target_salts)

    # 5. DDI (DRUG-DRUG INTERACTIONS) (Score: 0.85)
    for salt in target_salts:
        if salt in DDI_MAP:
            for med in active_meds:
                if med in DDI_MAP[salt]:
                    alerts.append(f"DDI Alert ({salt.title()} + {med.title()}): {DDI_MAP[salt][med]}")
                    highest_risk_score = max(highest_risk_score, 0.85)

    # 6. CLINICAL & GENOMIC CONDITIONS (Score: 0.70 - 0.95)
    for salt in target_salts:
        if salt in CLINICAL_MAP:
            # Check diseases
            for condition in conditions:
                if condition in CLINICAL_MAP[salt]:
                    alerts.append(f"Clinical Risk ({salt.title()} vs {condition.title()}): {CLINICAL_MAP[salt][condition]['warning']}")
                    highest_risk_score = max(highest_risk_score, 0.75)
            
            # Check Genotypes explicitly mapped in CLINICAL_MAP
            for marker, patient_allele in genotypes.items():
                if marker in CLINICAL_MAP[salt] and patient_allele in CLINICAL_MAP[salt][marker]:
                    alerts.append(f"Genomic Alert (Marker {marker} - {patient_allele}): {CLINICAL_MAP[salt][marker][patient_allele]}")
                    highest_risk_score = max(highest_risk_score, 0.95)

    # 7. FAMILY GENOMIC INHERITANCE CHECK
    if highest_risk_score < 0.80:
        relations = supabase.table("family_relationships").select("relative_id, relationship_type").eq("patient_id", req.patient_id).execute().data or []
        for rel in relations:
            rel_patient = supabase.table("patients").select("abha_id, name").eq("id", rel["relative_id"]).execute().data
            if not rel_patient: continue
            
            rel_abdm = supabase.table("abdm_mock_records").select("allergies, basic_health_details").eq("abha_id", rel_patient[0]["abha_id"]).execute().data
            if not rel_abdm: continue
            
            # Check relative's genotypes
            rel_genotypes = rel_abdm[0].get("basic_health_details", {}).get("genotype_markers", {})
            for salt in target_salts:
                if salt in CLINICAL_MAP:
                    for marker, rel_allele in rel_genotypes.items():
                        if marker in CLINICAL_MAP[salt] and rel_allele in CLINICAL_MAP[salt][marker]:
                            alerts.append(f"Family Genomic Risk: Relative ({rel['relationship_type']}) has genetic marker {marker}-{rel_allele} causing adverse reaction to {salt.title()}.")
                            highest_risk_score = max(highest_risk_score, 0.85)
            
            # Check relative's allergies
            rel_allergies = [a.get("allergen", "").lower() for a in rel_abdm[0].get("allergies", [])]
            for salt in target_salts:
                for allergy in rel_allergies:
                     if salt in allergy or allergy in salt:
                        alerts.append(f"Family Allergy Risk: Relative ({rel['relationship_type']}) is allergic to {salt.title()}. Dispense with caution.")
                        highest_risk_score = max(highest_risk_score, 0.60) # Yellow warning

    # Determine Tier
    if highest_risk_score >= 0.80: severity_tier = "Red"
    elif highest_risk_score >= 0.50: severity_tier = "Yellow"

    message = " | ".join(alerts) if alerts else "No adverse drug interactions or genetic conflicts detected based on current evidence."
    return compile_response(severity_tier, highest_risk_score, message, target_salts)

def compile_response(tier, score, message, salts):
    return {
        "severity_tier": tier,
        "risk_probability": score, # Kept for UI backwards compatibility (gauges/charts)
        "message": message,
        "resolved_salts": salts,
        "suggested_alternative": "Consult physician for genomic/interaction-appropriate alternatives." if tier == "Red" else None
    }