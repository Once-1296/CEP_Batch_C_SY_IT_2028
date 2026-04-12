from fastapi import APIRouter

from app.controllers.auth_controller import login
from app.controllers.schema import LoginRequest


router = APIRouter()


@router.post("/api/login")
async def login_route(req: LoginRequest):
    return await login(req)
