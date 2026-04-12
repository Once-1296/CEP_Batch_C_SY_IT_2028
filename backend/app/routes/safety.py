from fastapi import APIRouter

from app.controllers.safety_controller import check_drug_safety
from app.controllers.schema import DrugCheckRequest


router = APIRouter()


@router.post("/api/check-drug")
async def check_drug_safety_route(req: DrugCheckRequest):
    return await check_drug_safety(req)
