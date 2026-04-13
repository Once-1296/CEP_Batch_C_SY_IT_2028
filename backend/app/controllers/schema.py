from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class AddPharmacistRequest(BaseModel):
    name: str
    username: str
    password: str
    phone: str


class AddAdminRequest(BaseModel):
    name: str
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class CreatePatientRequest(BaseModel):
    name: str
    phone: str
    password: str
    current_medications: List[str] = []
    current_conditions: List[str] = []
    added_by: str


class UpdatePatientRequest(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    current_medications: Optional[List[str]] = None
    current_conditions: Optional[List[str]] = None


class VerifyPatientRequest(BaseModel):
    patient_id: int
    password: str

class DrugCheckRequest(BaseModel):
    pharmacist_query: str
    patient_id: str


class ABDMConsentInitRequest(BaseModel):
    abha_id: str


class ABDMWebhookBase(BaseModel):
    class Config:
        extra = "allow"


class ABDMGatewayError(BaseModel):
    code: Optional[Any] = None
    message: Optional[str] = None
    details: Optional[Any] = None


class ABDMConsentStatusWebhook(ABDMWebhookBase):
    request_id: Optional[str] = None
    transaction_id: Optional[str] = None
    consent_request_id: Optional[str] = None
    consent_artifact_id: Optional[str] = None
    consent_status: Optional[str] = None
    status: Optional[str] = None
    error: Optional[ABDMGatewayError] = None
    payload: Optional[Dict[str, Any]] = None
    data: Optional[Dict[str, Any]] = None
    consent: Optional[Dict[str, Any]] = None


class ABDMHealthDataWebhook(ABDMWebhookBase):
    request_id: Optional[str] = None
    transaction_id: Optional[str] = None
    consent_request_id: Optional[str] = None
    consent_artifact_id: Optional[str] = None
    health_request_id: Optional[str] = None
    error: Optional[ABDMGatewayError] = None
    key_material: Optional[Dict[str, Any]] = None
    encrypted_payload: Optional[Any] = None
    encrypted_bundle: Optional[Any] = None
    encrypted_data: Optional[Any] = None
    ciphertext: Optional[Any] = None
    iv: Optional[Any] = None
    aad: Optional[Any] = None
    fhir_bundle: Optional[Any] = None
    payload: Optional[Any] = None
    response: Optional[Any] = None
    data: Optional[Any] = None