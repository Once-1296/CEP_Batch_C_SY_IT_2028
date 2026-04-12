from fastapi import APIRouter

from app.controllers.patient_controller import create_patient, list_patients, update_patient, verify_patient
from app.controllers.schema import CreatePatientRequest, UpdatePatientRequest, VerifyPatientRequest


router = APIRouter()


@router.get("/api/patients")
async def list_patients_route():
    return await list_patients()


@router.post("/api/patients")
async def create_patient_route(req: CreatePatientRequest):
    return await create_patient(req)


@router.put("/api/patients/{patient_id}")
async def update_patient_route(patient_id: int, req: UpdatePatientRequest):
    return await update_patient(patient_id, req)


@router.post("/api/patients/verify")
async def verify_patient_route(req: VerifyPatientRequest):
    return await verify_patient(req)
