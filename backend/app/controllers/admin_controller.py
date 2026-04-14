from fastapi import HTTPException
from app.config.supabase import get_supabase, get_supabase_admin
from app.controllers.schema import AddAdminRequest, AddPharmacistRequest, CreatePatientRequest
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
    ph_check = supabase.table("pharmacists").select("id").eq("id", req.added_by).execute()
    if not ph_check.data or len(ph_check.data) == 0:
        raise HTTPException(status_code=400, detail="Specified pharmacist (registered_by) does not exist")

    insert_data = {
        "name": req.name,
        "abha_id": req.abha_id,
        "phone": req.phone,
        "password": hash_password(req.password),
        "current_medications": req.current_medications,
        "current_conditions": req.current_conditions,
        "registered_by": req.added_by,
    }
    supabase_admin.table("patients").insert(insert_data).execute()

    return {"status": "success", "message": f"Patient '{req.name}' registered successfully"}
