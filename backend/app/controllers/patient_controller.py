from fastapi import HTTPException

from app.config.supabase import get_supabase
from app.controllers.schema import CreatePatientRequest, UpdatePatientRequest, VerifyPatientRequest
from app.config.settings import hash_password


async def list_patients(user: dict, page: int = 1, limit: int = 20, search: str = None):
    supabase = get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    try:
        tpage,tlimit = int(page),int(limit)
    except Exception as e:
        raise HTTPException(status_code=422,detail=str(e) + "\n Could not convert page/limit to int")


    offset = (page - 1) * limit

    if user["role"] == "admin":
        query = supabase.table("patients").select("*")
    else:
        query = supabase.table("patients").select("id, name, abha_id, phone")

    if search:
        query = query.or_(f"name.ilike.%{search}%,abha_id.ilike.%{search}%")

    query = query.range(offset, offset + limit - 1)
    
    all_patients = query.execute().data or []
    if not all_patients:
        return {"patients": []}
        
    patient_ids = [p["id"] for p in all_patients]
    abha_ids = [p["abha_id"] for p in all_patients if p.get("abha_id")]

    if user["role"] == "admin":
        if abha_ids:
            abdm_records = supabase.table("abdm_mock_records").select("*").in_("abha_id", abha_ids).execute().data or []
            abdm_dict = {r["abha_id"]: r for r in abdm_records}
            for p in all_patients:
                if p.get("abha_id") in abdm_dict:
                    p["abdm_record"] = abdm_dict[p["abha_id"]]
        return {"patients": all_patients}
    else:
        reqs = supabase.table("access_requests")\
            .select("patient_id, status")\
            .eq("pharmacist_id", user["id"])\
            .in_("patient_id", patient_ids).execute().data or []
            
        status_dict = {r["patient_id"]: r["status"] for r in reqs}
        accepted_ids = {r["patient_id"] for r in reqs if r["status"] == "ACCEPTED"}
        
        full_p_dict = {}
        if accepted_ids:
            full_ps = supabase.table("patients").select("*").in_("id", list(accepted_ids)).execute().data or []
            full_p_dict = {p["id"]: p for p in full_ps}
            
            accepted_abhas = [p["abha_id"] for p in full_ps if p.get("abha_id")]
            if accepted_abhas:
                abdm_recs = supabase.table("abdm_mock_records").select("*").in_("abha_id", accepted_abhas).execute().data or []
                abdm_dict = {r["abha_id"]: r for r in abdm_recs}
                for fp in full_ps:
                    if fp.get("abha_id") in abdm_dict:
                        fp["abdm_record"] = abdm_dict[fp["abha_id"]]
        
        final_patients = []
        for p in all_patients:
            p_id = p["id"]
            if p_id in accepted_ids:
                full_p = full_p_dict.get(p_id, p)
                full_p["access_status"] = "ACCEPTED"
                final_patients.append(full_p)
            else:
                p["access_status"] = status_dict.get(p_id, "NONE")
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
