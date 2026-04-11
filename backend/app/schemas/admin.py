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
