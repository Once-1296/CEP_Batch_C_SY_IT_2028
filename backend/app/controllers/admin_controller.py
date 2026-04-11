from fastapi import HTTPException

from app.config.supabase import get_supabase, get_supabase_admin
from app.schemas.admin import AddAdminRequest, AddPharmacistRequest
from app.utils.security import hash_password


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
