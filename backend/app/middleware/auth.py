from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config.supabase import get_supabase


PUBLIC_PATHS = {
    "/api/login",
    "/docs",
    "/openapi.json",
    "/redoc",
}


def _is_admin_path(path: str) -> bool:
    return path.startswith("/api/admin/")


def _is_pharmacist_protected_path(path: str) -> bool:
    return path.startswith("/api/patients") or path == "/api/check-drug"


def _is_public_path(path: str) -> bool:
    return path in PUBLIC_PATHS


def _extract_username_from_bearer(auth_header: str | None) -> str | None:
    if not auth_header:
        return None

    prefix = "Bearer "
    if not auth_header.startswith(prefix):
        return None

    token = auth_header[len(prefix):].strip()
    token_prefix = "fake-jwt-"
    if not token.startswith(token_prefix):
        return None

    username = token[len(token_prefix):].strip()
    return username or None


def register_auth_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def auth_middleware(request: Request, call_next):
        path = request.url.path

        if _is_public_path(path):
            return await call_next(request)

        if not (_is_admin_path(path) or _is_pharmacist_protected_path(path)):
            return await call_next(request)

        username = _extract_username_from_bearer(request.headers.get("Authorization"))
        if not username:
            return JSONResponse(status_code=401, content={"detail": "Missing or invalid Authorization token"})

        supabase = get_supabase()
        if not supabase:
            return JSONResponse(status_code=500, content={"detail": "Supabase not configured"})

        admin_res = supabase.table("admins").select("id, username").eq("username", username).execute()
        if admin_res.data and len(admin_res.data) > 0:
            request.state.user = {
                "username": username,
                "role": "admin",
                "verified": True,
            }
            return await call_next(request)

        pharmacist_res = supabase.table("pharmacists").select("id, username, status").eq("username", username).execute()
        if not pharmacist_res.data or len(pharmacist_res.data) == 0:
            return JSONResponse(status_code=401, content={"detail": "Invalid user token"})

        pharmacist = pharmacist_res.data[0]
        status_value = str(pharmacist.get("status", "")).strip().lower()
        is_verified = status_value in {"verified", "active", "approved", "true", "1"} or status_value == ""

        request.state.user = {
            "username": username,
            "role": "pharmacist",
            "verified": is_verified,
        }

        if _is_admin_path(path):
            return JSONResponse(status_code=403, content={"detail": "Admin access required"})

        if _is_pharmacist_protected_path(path) and not is_verified:
            return JSONResponse(status_code=403, content={"detail": "Verified pharmacist access required"})

        return await call_next(request)