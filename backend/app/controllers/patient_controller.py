from fastapi import HTTPException

from app.config.supabase import get_supabase
from app.controllers.schema import CreatePatientRequest, UpdatePatientRequest, VerifyPatientRequest
from app.config.settings import hash_password


async def list_patients(user: dict):
    supabase = get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    if user["role"] == "admin":
        result = supabase.table("patients").select("*").execute()
        patients = result.data or []
        # For admin, also fetch abdm_mock_records for each patient
        for p in patients:
            abha_id = p.get("abha_id")
            if abha_id:
                abdm = supabase.table("abdm_mock_records").select("*").eq("abha_id", abha_id).execute()
                if abdm.data:
                    p["abdm_record"] = abdm.data[0]
        return {"patients": patients}
    else:
        # Pharmacists see basic info for all, but full info for consented ones
        all_patients = supabase.table("patients").select("id, name, abha_id, phone").execute().data or []

        # Get accepted requests for this pharmacist
        accepted_reqs = supabase.table("access_requests")\
            .select("patient_id")\
            .eq("pharmacist_id", user["id"])\
            .eq("status", "ACCEPTED").execute().data or []

        accepted_ids = {r["patient_id"] for r in accepted_reqs}

        final_patients = []
        for p in all_patients:
            p_id = p["id"]
            if p_id in accepted_ids:
                # Fetch full patient data
                full_p = supabase.table("patients").select("*").eq("id", p_id).execute().data[0]
                full_p["access_status"] = "ACCEPTED"
                # Also fetch abdm_mock_records
                abha_id = full_p.get("abha_id")
                if abha_id:
                    abdm = supabase.table("abdm_mock_records").select("*").eq("abha_id", abha_id).execute()
                    if abdm.data:
                        full_p["abdm_record"] = abdm.data[0]
                final_patients.append(full_p)
            else:
                p["access_status"] = "NONE"
                # Check for pending status
                pending_check = supabase.table("access_requests")\
                    .select("status")\
                    .eq("pharmacist_id", user["id"])\
                    .eq("patient_id", p_id).execute().data
                if pending_check:
                    p["access_status"] = pending_check[0]["status"]
                final_patients.append(p)

        return {"patients": final_patients}


async def get_patient_details(patient_id: str, requester: dict):
    supabase = get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    has_full_access = False
    if requester["role"] == "admin":
        has_full_access = True
    elif requester["role"] == "patient" and requester["id"] == patient_id:
        has_full_access = True
    elif requester["role"] == "pharmacist":
        perm = supabase.table("access_requests").select("status")\
            .eq("pharmacist_id", requester["id"])\
            .eq("patient_id", patient_id)\
            .eq("status", "ACCEPTED").execute()
        if perm.data and len(perm.data) > 0:
            has_full_access = True

    if has_full_access:
        result = supabase.table("patients").select("*").eq("id", patient_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Patient not found")
        patient_data = result.data[0]

        # Fetch abdm_mock_records by abha_id
        abha_id = patient_data.get("abha_id")
        if abha_id:
            abdm = supabase.table("abdm_mock_records").select("*").eq("abha_id", abha_id).execute()
            if abdm.data:
                patient_data["abdm_record"] = abdm.data[0]

        # Also fetch family relationships
        family = supabase.table("family_relationships").select("*").eq("patient_id", patient_id).execute()
        patient_data["family"] = family.data or []
        return {"access": "granted", "patient": patient_data}
    else:
        result = supabase.table("patients").select("id, name, abha_id").eq("id", patient_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Patient not found")
        return {"access": "restricted", "patient": result.data[0], "message": "Access request required for medical details"}


async def request_access(patient_id: str, pharmacist_id: str):
    supabase = get_supabase()
    # Prevent duplicate requests
    existing = supabase.table("access_requests").select("id, status")\
        .eq("pharmacist_id", pharmacist_id)\
        .eq("patient_id", patient_id).execute()

    if existing.data and len(existing.data) > 0:
        return {"status": "exists", "request": existing.data[0]}

    insert_data = {
        "pharmacist_id": pharmacist_id,
        "patient_id": patient_id,
        "status": "PENDING"
    }
    result = supabase.table("access_requests").insert(insert_data).execute()
    return {"status": "success", "request": result.data[0]}


async def get_access_requests(patient_id: str):
    supabase = get_supabase()
    # Join with pharmacists to show who is asking
    result = supabase.table("access_requests").select("id, status, created_at, pharmacist_id, pharmacists(name)")\
        .eq("patient_id", patient_id).execute()

    return {
        "requests": result.data or [],
        "warning": "Granting access allows the pharmacist to see your data and your family's records. Only approve if you fully trust them."
    }


async def respond_to_access_request(request_id: str, status: str, patient_id: str):
    supabase = get_supabase()
    # Verify the request belongs to the patient
    req_check = supabase.table("access_requests").select("patient_id").eq("id", request_id).execute()
    if not req_check.data or req_check.data[0]["patient_id"] != patient_id:
        raise HTTPException(status_code=403, detail="Not authorized to respond to this request")

    result = supabase.table("access_requests").update({"status": status, "updated_at": "now()"})\
        .eq("id", request_id).execute()
    return {"status": "success", "request": result.data[0]}


async def create_patient(req: CreatePatientRequest):
    supabase = get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    insert_data = {
        "name": req.name,
        "abha_id": req.abha_id,
        "phone": req.phone,
        "password": hash_password(req.password),
        "registered_by": req.registered_by,
    }
    result = supabase.table("patients").insert(insert_data).execute()

    if result.data and len(result.data) > 0:
        return {"status": "success", "patient": result.data[0]}
    raise HTTPException(status_code=500, detail="Failed to create patient")


async def update_patient(patient_id: str, req: UpdatePatientRequest):
    supabase = get_supabase()
    update_data = {}
    if req.name is not None: update_data["name"] = req.name
    if req.phone is not None: update_data["phone"] = req.phone

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = supabase.table("patients").update(update_data).eq("id", patient_id).execute()
    if result.data and len(result.data) > 0:
        return {"status": "success", "patient": result.data[0]}
    raise HTTPException(status_code=404, detail="Patient not found")


async def verify_patient(req: VerifyPatientRequest):
    supabase = get_supabase()
    result = supabase.table("patients").select("id, password").eq("id", req.patient_id).execute()

    if not result.data or len(result.data) == 0:
        raise HTTPException(status_code=404, detail="Patient not found")

    stored_hash = result.data[0]["password"]
    return {"verified": stored_hash == hash_password(req.password)}
