from fastapi import HTTPException

from app.config.supabase import get_supabase
from app.nlp.ddi_engine import get_ddi_match_alert
from app.nlp.normalizer import normalize_input
from app.nlp.resolver import resolve_entity, resolve_patient_meds_to_salts
from app.controllers.schema import DrugCheckRequest


async def check_drug_safety(req: DrugCheckRequest):
    supabase = get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    patient_res = supabase.table("patients").select(
        "id, name, current_medications, current_conditions"
    ).eq("id", req.patient_id).execute()

    if not patient_res.data or len(patient_res.data) == 0:
        raise HTTPException(status_code=404, detail="Patient not found")


    patient = patient_res.data[0]

    clean_query = normalize_input(req.pharmacist_query)
    resolved_drug = resolve_entity(clean_query)

    if not resolved_drug:
        return {"status": "error", "message": "Could not confidently identify the medicine."}

    target_salt = resolved_drug["generic_salt"]

    alert = {
        "severity_tier": "Green",
        "message": "No known interaction found in database. Verify independently before dispensing.",
        "resolved_data": resolved_drug,
        "suggested_alternative": None,
    }

    # 1. DDI Check (Patient's own meds)
    patient_meds = patient.get("current_medications", []) or []
    patient_salts = resolve_patient_meds_to_salts(patient_meds)

    matched_ddi = get_ddi_match_alert(target_salt, patient_salts)
    if matched_ddi:
        alert["severity_tier"] = matched_ddi["severity_tier"]
        alert["message"] = matched_ddi["message"]
        alert["suggested_alternative"] = matched_ddi["suggested_alternative"]
        return alert

    # 2. Family History Risk Check (Genetic/Shared sensitivity)
    # Fetch relatives
    relations = supabase.table("family_relationships").select("relative_id, relationship_type")\
        .eq("patient_id", req.patient_id).execute().data or []
    
    for rel in relations:
        rel_id = rel["relative_id"]
        rel_type = rel["relationship_type"]
        # Fetch relative's medical profile
        rel_data = supabase.table("patients").select("name, current_conditions, medicines_to_avoid")\
            .eq("id", rel_id).execute().data
        
        if rel_data:
            relative = rel_data[0]
            rel_name = relative["name"]
            rel_meds_avoid = relative.get("medicines_to_avoid", []) or []
            rel_conditions = relative.get("current_conditions", []) or []
            
            # Simple fuzzy match for names/salts in medicines_to_avoid
            for avoid in rel_meds_avoid:
                if target_salt.lower() in avoid.lower() or avoid.lower() in target_salt.lower():
                    return {
                        "severity_tier": "Red",
                        "message": f"CRITICAL: Family risk detected. Relative ({rel_type}) {rel_name} has a recorded sensitivity to {avoid}. Use with extreme caution.",
                        "resolved_data": resolved_drug,
                        "suggested_alternative": "Consult a specialist for genomic-appropriate alternatives."
                    }
            
            # Specific logic for G6PD deficiency -> Aspirin (Common genetic risk)
            if "g6pd" in str(rel_conditions).lower() and "aspirin" in target_salt.lower():
                return {
                    "severity_tier": "Red",
                    "message": f"CRITICAL: Family history of G6PD deficiency ({rel_type}: {rel_name}). Drugs like {target_salt} may trigger hemolytic anemia in genetically predisposed individuals.",
                    "resolved_data": resolved_drug,
                    "suggested_alternative": "Acetaminophen (Paracetamol) is generally safer."
                }

    return alert
