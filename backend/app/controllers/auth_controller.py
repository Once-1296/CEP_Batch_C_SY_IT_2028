from fastapi import HTTPException

from app.config.supabase import get_supabase
from app.controllers.schema import LoginRequest
from app.config.settings import hash_password


async def login(req: LoginRequest):
    supabase = get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    hashed = hash_password(req.password)

    admin_res = supabase.table("admins").select("id, name, username, password").eq("username", req.username).execute()
    if admin_res.data and len(admin_res.data) > 0:
        admin = admin_res.data[0]
        if admin["password"] == hashed:
            return {
                "status": "success",
                "token": f"fake-jwt-{req.username}",
                "role": "admin",
                "name": admin["name"],
            }

    pharm_res = supabase.table("pharmacists").select("id, name, username, password").eq("username", req.username).execute()
    if pharm_res.data and len(pharm_res.data) > 0:
        pharmacist = pharm_res.data[0]
        if pharmacist["password"] == hashed:
            return {
                "status": "success",
                "token": f"fake-jwt-{req.username}",
                "role": "pharmacist",
                "name": pharmacist["name"],
                "id": pharmacist["id"],
            }

    # Patient login: use abha_id as username
    patient_res = supabase.table("patients").select("id, name, abha_id, password").eq("abha_id", req.username).execute()
    if patient_res.data and len(patient_res.data) > 0:
        patient = patient_res.data[0]
        if patient["password"] == hashed:
            return {
                "status": "success",
                "token": f"fake-jwt-{req.username}",
                "role": "patient",
                "name": patient["name"],
                "id": patient["id"],
            }

    raise HTTPException(status_code=401, detail="Invalid username or password")
