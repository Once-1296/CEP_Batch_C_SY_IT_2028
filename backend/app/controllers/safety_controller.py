from fastapi import HTTPException

from app.config.supabase import get_supabase
from app.nlp.normalizer import normalize_input
from app.nlp.resolver import resolve_entity
from app.nlp.cdss import predict_risk
from app.controllers.schema import DrugCheckRequest


async def check_drug_safety(req: DrugCheckRequest):
    supabase = get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    # 1. Validate patient exists
    patient_res = supabase.table("patients").select(
        "id, name, abha_id"
    ).eq("id", req.patient_id).execute()

    if not patient_res.data or len(patient_res.data) == 0:
        raise HTTPException(status_code=404, detail="Patient not found")

    patient = patient_res.data[0]
    abha_id = req.abha_id or patient.get("abha_id")

    # 2. NLP: normalize + resolve to generic salt
    clean_query = normalize_input(req.pharmacist_query)
    resolved_drug = resolve_entity(clean_query)

    if not resolved_drug:
        return {"status": "error", "message": "Could not confidently identify the medicine."}

    target_salt = resolved_drug["generic_salt"]

    # 3. Fetch patient medical data from abdm_mock_records
    abdm_res = supabase.table("abdm_mock_records").select(
        "medication_history, pre_existing_conditions, allergies"
    ).eq("abha_id", abha_id).execute()

    active_items = []

    if abdm_res.data and len(abdm_res.data) > 0:
        record = abdm_res.data[0]

        # Extract active medications
        meds = record.get("medication_history", []) or []
        for m in meds:
            if isinstance(m, dict):
                status = (m.get("status", "") or "").lower()
                time_period = (m.get("time_period", "") or "").lower()
                if status in ["active", "current"] or time_period in ["active", "current"]:
                    med_name = m.get("medication_name", "")
                    if med_name:
                        active_items.append(med_name)
            elif isinstance(m, str) and m:
                active_items.append(m)

        # Extract pre-existing conditions
        conditions = record.get("pre_existing_conditions", []) or []
        for c in conditions:
            if isinstance(c, dict):
                condition = c.get("condition", "")
                if condition:
                    active_items.append(condition)
            elif isinstance(c, str) and c:
                active_items.append(c)

        # Extract allergies
        allergies = record.get("allergies", []) or []
        for a in allergies:
            if isinstance(a, dict):
                allergen = a.get("allergen", "")
                if allergen:
                    active_items.append(f"Allergy: {allergen}")
            elif isinstance(a, str) and a:
                active_items.append(f"Allergy: {a}")

    # 4. ML Model: predict risk probability
    ml_result = predict_risk(target_salt, active_items)
    risk_prob = ml_result["risk_probability"]

    # 5. Determine severity tier from probability
    if risk_prob >= 0.75:
        severity_tier = "Red"
    elif risk_prob >= 0.40:
        severity_tier = "Yellow"
    else:
        severity_tier = "Green"

    # 6. Build response message
    if severity_tier == "Red":
        message = (
            f"CRITICAL: Conflict detected between proposed '{target_salt}' and "
            f"patient's '{ml_result['conflicting_item']}' "
            f"({round(risk_prob * 100, 1)}% risk probability)"
        )
        suggested_alternative = "Consult a specialist for a safer alternative."
    elif severity_tier == "Yellow":
        message = (
            f"MODERATE RISK: Potential interaction between '{target_salt}' and "
            f"'{ml_result['conflicting_item']}' "
            f"({round(risk_prob * 100, 1)}% risk probability). Verify before dispensing."
        )
        suggested_alternative = None
    else:
        message = "No adverse drug interactions or genetic conflict detected."
        suggested_alternative = None

    alert = {
        "severity_tier": severity_tier,
        "message": message,
        "resolved_data": resolved_drug,
        "suggested_alternative": suggested_alternative,
        "risk_probability": risk_prob,
        "ml_details": ml_result["details"],
    }

    # 7. Family History Risk Check (genetic/shared sensitivity)
    if severity_tier == "Green":
        relations = supabase.table("family_relationships").select(
            "relative_id, relationship_type"
        ).eq("patient_id", req.patient_id).execute().data or []

        for rel in relations:
            rel_id = rel["relative_id"]
            rel_type = rel["relationship_type"]

            # Get relative's abha_id
            rel_patient = supabase.table("patients").select("abha_id, name").eq(
                "id", rel_id
            ).execute().data

            if not rel_patient:
                continue

            rel_abha = rel_patient[0].get("abha_id")
            rel_name = rel_patient[0].get("name", "Unknown")

            if not rel_abha:
                continue

            # Fetch relative's ABDM records
            rel_abdm = supabase.table("abdm_mock_records").select(
                "pre_existing_conditions, allergies"
            ).eq("abha_id", rel_abha).execute().data

            if not rel_abdm:
                continue

            rel_record = rel_abdm[0]

            # Check allergies of relative for matching salt
            rel_allergies = rel_record.get("allergies", []) or []
            for a in rel_allergies:
                allergen = a.get("allergen", "") if isinstance(a, dict) else str(a)
                if allergen and (
                    target_salt.lower() in allergen.lower()
                    or allergen.lower() in target_salt.lower()
                ):
                    return {
                        "severity_tier": "Red",
                        "message": (
                            f"CRITICAL: Family risk detected. Relative ({rel_type}) "
                            f"{rel_name} has a recorded sensitivity to {allergen}. "
                            f"Use with extreme caution."
                        ),
                        "resolved_data": resolved_drug,
                        "suggested_alternative": "Consult a specialist for genomic-appropriate alternatives.",
                        "risk_probability": 0.95,
                        "ml_details": ml_result["details"],
                    }

            # G6PD deficiency check
            rel_conditions = rel_record.get("pre_existing_conditions", []) or []
            conditions_str = str(rel_conditions).lower()
            if "g6pd" in conditions_str and "aspirin" in target_salt.lower():
                return {
                    "severity_tier": "Red",
                    "message": (
                        f"CRITICAL: Family history of G6PD deficiency "
                        f"({rel_type}: {rel_name}). Drugs like {target_salt} "
                        f"may trigger hemolytic anemia in genetically predisposed individuals."
                    ),
                    "resolved_data": resolved_drug,
                    "suggested_alternative": "Acetaminophen (Paracetamol) is generally safer.",
                    "risk_probability": 0.90,
                    "ml_details": ml_result["details"],
                }

    return alert
