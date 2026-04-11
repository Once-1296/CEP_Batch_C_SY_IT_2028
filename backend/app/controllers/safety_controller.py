from fastapi import HTTPException

from app.config.supabase import get_supabase
from app.nlp.ddi_engine import get_ddi_match_alert
from app.nlp.normalizer import normalize_input
from app.nlp.resolver import resolve_entity, resolve_patient_meds_to_salts
from app.schemas.safety import DrugCheckRequest


async def check_drug_safety(req: DrugCheckRequest):
    supabase = get_supabase()
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

    patient_meds = patient.get("current_medications", []) or []
    patient_salts = resolve_patient_meds_to_salts(patient_meds)

    matched = get_ddi_match_alert(target_salt, patient_salts)
    if matched:
        alert["severity_tier"] = matched["severity_tier"]
        alert["message"] = matched["message"]
        alert["suggested_alternative"] = matched["suggested_alternative"]
        return alert

    return alert
