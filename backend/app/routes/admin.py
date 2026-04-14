from fastapi import APIRouter

from app.controllers.admin_controller import add_admin, add_pharmacist, add_patient
from app.controllers.schema import AddAdminRequest, AddPharmacistRequest, CreatePatientRequest


router = APIRouter()


@router.post("/api/admin/add-pharmacist")
async def add_pharmacist_route(req: AddPharmacistRequest):
    return await add_pharmacist(req)


@router.post("/api/admin/add-admin")
async def add_admin_route(req: AddAdminRequest):
    return await add_admin(req)


@router.post("/api/admin/add-patient")
async def add_patient_route(req: CreatePatientRequest):
    return await add_patient(req)
