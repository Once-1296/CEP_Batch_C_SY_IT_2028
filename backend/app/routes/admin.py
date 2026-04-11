from fastapi import APIRouter

from app.controllers.admin_controller import add_admin, add_pharmacist
from app.schemas.admin import AddAdminRequest, AddPharmacistRequest


router = APIRouter()


@router.post("/api/admin/add-pharmacist")
async def add_pharmacist_route(req: AddPharmacistRequest):
    return await add_pharmacist(req)


@router.post("/api/admin/add-admin")
async def add_admin_route(req: AddAdminRequest):
    return await add_admin(req)
