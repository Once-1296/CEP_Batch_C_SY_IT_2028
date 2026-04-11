from pydantic import BaseModel


class DrugCheckRequest(BaseModel):
    pharmacist_query: str
    patient_id: str
