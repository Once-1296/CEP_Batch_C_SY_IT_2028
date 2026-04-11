from typing import List, Optional
from pydantic import BaseModel


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
