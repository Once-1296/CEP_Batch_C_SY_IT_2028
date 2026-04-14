from fastapi import APIRouter, Request, HTTPException
from app.controllers.patient_controller import (
    create_patient, list_patients, update_patient, verify_patient,
    request_access, get_access_requests, respond_to_access_request, get_patient_details
)
from app.controllers.schema import (
    CreatePatientRequest, UpdatePatientRequest, VerifyPatientRequest,
    RequestAccessRequest, RespondAccessRequest
)

router = APIRouter()

@router.get("/api/patients")
async def list_patients_route(request: Request):
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return await list_patients(user)

@router.post("/api/patients")
async def create_patient_route(req: CreatePatientRequest):
    return await create_patient(req)

@router.post("/api/patients/verify")
async def verify_patient_route(req: VerifyPatientRequest):
    return await verify_patient(req)

# --- Access Request Routes ---

@router.get("/api/patients/access-requests")
async def get_access_requests_route(request: Request):
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    if user["role"] != "patient":
        raise HTTPException(status_code=403, detail="Only patients can see their own access requests currently")
    
    return await get_access_requests(user["id"])

@router.post("/api/patients/request-access")
async def request_access_route(req: RequestAccessRequest, request: Request):
    user = getattr(request.state, "user", None)
    if not user or user["role"] != "pharmacist":
        raise HTTPException(status_code=403, detail="Only pharmacists can request access")
    return await request_access(req.patient_id, user["id"])

@router.post("/api/patients/respond-access")
async def respond_to_access_request_route(req: RespondAccessRequest, request: Request):
    user = getattr(request.state, "user", None)
    if not user or user["role"] != "patient":
        raise HTTPException(status_code=403, detail="Only patients can respond to access requests")
    
    return await respond_to_access_request(req.request_id, req.status, user["id"])

# --- Parameterized Routes ({patient_id}) ---

@router.get("/api/patients/{patient_id}")
async def get_patient_details_route(patient_id: str, request: Request):
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return await get_patient_details(patient_id, user)

@router.put("/api/patients/{patient_id}")
async def update_patient_route(patient_id: str, req: UpdatePatientRequest):
    return await update_patient(patient_id, req)
