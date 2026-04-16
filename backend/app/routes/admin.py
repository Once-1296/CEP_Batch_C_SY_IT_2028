from fastapi import APIRouter

from app.controllers.admin_controller import add_admin, add_pharmacist, add_patient, upload_abdm_record
from app.controllers.schema import AddAdminRequest, AddPharmacistRequest, CreatePatientRequest, ABDMRecordUploadRequest


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


@router.post("/api/admin/upload-abdm-record")
async def upload_abdm_record_route(req: ABDMRecordUploadRequest):
    return await upload_abdm_record(req)
