from fastapi import HTTPException

from app.config.supabase import get_supabase
from app.controllers.schema import CreatePatientRequest, UpdatePatientRequest, VerifyPatientRequest
from app.config.settings import hash_password


async def list_patients():
    supabase = get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    result = supabase.table("patients").select(
        "id, name, phone, current_medications, current_conditions, added_by"
    ).execute()

    return {"patients": result.data or []}


async def create_patient(req: CreatePatientRequest):
    supabase = get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    insert_data = {
        "name": req.name,
        "phone": req.phone,
        "password": hash_password(req.password),
        "current_medications": req.current_medications,
        "current_conditions": req.current_conditions,
        "added_by": req.added_by,
    }
    result = supabase.table("patients").insert(insert_data).execute()

    if result.data and len(result.data) > 0:
        return {"status": "success", "patient": result.data[0]}
    raise HTTPException(status_code=500, detail="Failed to create patient")


async def update_patient(patient_id: int, req: UpdatePatientRequest):
    supabase = get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    update_data = {}
    if req.name is not None:
        update_data["name"] = req.name
    if req.phone is not None:
        update_data["phone"] = req.phone
    if req.current_medications is not None:
        update_data["current_medications"] = req.current_medications
    if req.current_conditions is not None:
        update_data["current_conditions"] = req.current_conditions

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = supabase.table("patients").update(update_data).eq("id", patient_id).execute()

    if result.data and len(result.data) > 0:
        return {"status": "success", "patient": result.data[0]}
    raise HTTPException(status_code=404, detail="Patient not found")


async def verify_patient(req: VerifyPatientRequest):
    supabase = get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    result = supabase.table("patients").select("id, password").eq("id", req.patient_id).execute()

    if not result.data or len(result.data) == 0:
        raise HTTPException(status_code=404, detail="Patient not found")

    stored_hash = result.data[0]["password"]
    input_hash = hash_password(req.password)

    return {"verified": stored_hash == input_hash}
