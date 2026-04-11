from fastapi import HTTPException

from app.config.supabase import get_supabase
from app.schemas.auth import LoginRequest
from app.utils.security import hash_password


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
            }

    raise HTTPException(status_code=401, detail="Invalid username or password")
