from fastapi import HTTPException
from app.config.supabase import get_supabase, get_supabase_admin
from app.controllers.schema import AddAdminRequest, AddPharmacistRequest, CreatePatientRequest, ABDMRecordUploadRequest
from app.config.settings import hash_password


async def add_pharmacist(req: AddPharmacistRequest):
    supabase_admin = get_supabase_admin()
    supabase = get_supabase()

    if not supabase_admin:
        raise HTTPException(status_code=500, detail="Supabase service key not configured — cannot write to pharmacists table")

    existing = supabase.table("pharmacists").select("id").eq("username", req.username).execute()
    if existing.data and len(existing.data) > 0:
        raise HTTPException(status_code=400, detail="Username already taken")

    insert_data = {
        "name": req.name,
        "username": req.username,
        "password": hash_password(req.password),
        "phone": req.phone,
        "license_number": req.license_number,
    }
    supabase_admin.table("pharmacists").insert(insert_data).execute()

    return {"status": "success", "message": f"Pharmacist '{req.name}' added successfully"}


async def add_admin(req: AddAdminRequest):
    supabase_admin = get_supabase_admin()
    supabase = get_supabase()

    if not supabase_admin:
        raise HTTPException(status_code=500, detail="Supabase service key not configured — cannot write to admins table")

    existing = supabase.table("admins").select("id").eq("username", req.username).execute()
    if existing.data and len(existing.data) > 0:
        raise HTTPException(status_code=400, detail="Username already taken")

    insert_data = {
        "name": req.name,
        "username": req.username,
        "password": hash_password(req.password),
    }
    supabase_admin.table("admins").insert(insert_data).execute()

    return {"status": "success", "message": f"Admin '{req.name}' added successfully"}


async def add_patient(req: CreatePatientRequest):
    supabase_admin = get_supabase_admin()
    supabase = get_supabase()

    if not supabase_admin:
        raise HTTPException(status_code=500, detail="Supabase service key not configured — cannot write to patients table")

    # Verify pharmacist exists
    ph_check = supabase.table("pharmacists").select("id").eq("id", req.registered_by).execute()
    if not ph_check.data or len(ph_check.data) == 0:
        raise HTTPException(status_code=400, detail="Specified pharmacist (registered_by) does not exist")

    insert_data = {
        "name": req.name,
        "abha_id": req.abha_id,
        "phone": req.phone,
        "password": hash_password(req.password),
        "registered_by": req.registered_by,
    }
    supabase_admin.table("patients").insert(insert_data).execute()

    return {"status": "success", "message": f"Patient '{req.name}' registered successfully"}


async def upload_abdm_record(req: ABDMRecordUploadRequest):
    """Upload / upsert ABDM mock record for a patient (admin only)."""
    supabase_admin = get_supabase_admin()
    supabase = get_supabase()

    if not supabase_admin:
        raise HTTPException(status_code=500, detail="Supabase service key not configured")

    # Verify patient with this abha_id exists
    patient_check = supabase.table("patients").select("id").eq("abha_id", req.abha_id).execute()
    if not patient_check.data or len(patient_check.data) == 0:
        raise HTTPException(
            status_code=400,
            detail=f"No patient found with abha_id '{req.abha_id}'. Register the patient first."
        )

    # Validate that medical data is not completely empty
    if not req.medication_history and not req.pre_existing_conditions and not req.allergies:
        raise HTTPException(
            status_code=400,
            detail="ABDM record must contain at least one of: medication_history, pre_existing_conditions, or allergies."
        )

    upsert_data = {
        "abha_id": req.abha_id,
        "basic_health_details": req.basic_health_details,
        "pre_existing_conditions": req.pre_existing_conditions,
        "medication_history": req.medication_history,
        "allergies": req.allergies,
    }

    supabase_admin.table("abdm_mock_records").upsert(
        upsert_data, on_conflict="abha_id"
    ).execute()

    return {
        "status": "success",
        "message": f"ABDM record for '{req.abha_id}' uploaded successfully",
        "abha_id": req.abha_id,
    }
