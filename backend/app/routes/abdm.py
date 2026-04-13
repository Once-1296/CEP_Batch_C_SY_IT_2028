from fastapi import APIRouter, Request

from app.controllers.abdm_controller import (
    handle_consent_status_callback,
    handle_health_data_callback,
    request_abdm_consent,
)
from app.controllers.schema import ABDMConsentInitRequest, ABDMConsentStatusWebhook, ABDMHealthDataWebhook


router = APIRouter()


@router.post("/api/abdm/request-consent")
async def request_consent_route(req: ABDMConsentInitRequest, request: Request):
    return await request_abdm_consent(req, request)


@router.post("/api/callbacks/consent-status")
async def consent_status_callback_route(req: ABDMConsentStatusWebhook):
    return await handle_consent_status_callback(req)


@router.post("/api/callbacks/health-data")
async def health_data_callback_route(req: ABDMHealthDataWebhook):
    return await handle_health_data_callback(req)