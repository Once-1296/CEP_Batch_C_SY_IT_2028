from __future__ import annotations

import asyncio
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import httpx

# Switch ABDM_ENVIRONMENT between "sandbox" and "production" when you move
# from the development gateway to the live ABDM gateway.
ABDM_ENVIRONMENT = os.getenv("ABDM_ENVIRONMENT", "sandbox").strip().lower()

# Keep both URLs explicit so the sandbox-to-production swap stays obvious.
ABDM_SANDBOX_GATEWAY_BASE_URL = os.getenv(
    "ABDM_SANDBOX_GATEWAY_BASE_URL",
    "https://dev.abdm.gov.in/gateway",
)
ABDM_PRODUCTION_GATEWAY_BASE_URL = os.getenv(
    "ABDM_PRODUCTION_GATEWAY_BASE_URL",
    "https://gateway.abdm.gov.in",
)
ABDM_GATEWAY_BASE_URL = (
    ABDM_PRODUCTION_GATEWAY_BASE_URL
    if ABDM_ENVIRONMENT == "production"
    else ABDM_SANDBOX_GATEWAY_BASE_URL
).rstrip("/")

ABDM_CLIENT_ID = os.getenv("ABDM_CLIENT_ID")
ABDM_CLIENT_SECRET = os.getenv("ABDM_CLIENT_SECRET")
ABDM_HIU_ID = os.getenv("ABDM_HIU_ID", "ayush-guard-hiu")
ABDM_HIU_NAME = os.getenv("ABDM_HIU_NAME", "Ayush-Guard")
ABDM_CM_ID = os.getenv("ABDM_CM_ID", "sbx")

# The callback base URL must be public HTTPS. When you are using ngrok, set
# this to the ngrok domain so ABDM can reach your local FastAPI server.
ABDM_CALLBACK_BASE_URL = os.getenv("ABDM_CALLBACK_BASE_URL", "").rstrip("/")

# These paths stay the same between sandbox and production. Only the public
# callback base URL needs to change when you move environments.
ABDM_CONSENT_STATUS_CALLBACK_PATH = os.getenv(
    "ABDM_CONSENT_STATUS_CALLBACK_PATH",
    "/api/callbacks/consent-status",
)
ABDM_HEALTH_DATA_CALLBACK_PATH = os.getenv(
    "ABDM_HEALTH_DATA_CALLBACK_PATH",
    "/api/callbacks/health-data",
)

ABDM_TRACKING_TABLE = os.getenv("ABDM_TRACKING_TABLE", "abdm_consent_requests")
ABDM_SESSION_TABLE = os.getenv("ABDM_SESSION_TABLE", "abdm_sessions")
ABDM_REQUEST_TIMEOUT_SECONDS = float(os.getenv("ABDM_REQUEST_TIMEOUT_SECONDS", "30"))
ABDM_TOKEN_REFRESH_SKEW_SECONDS = int(os.getenv("ABDM_TOKEN_REFRESH_SKEW_SECONDS", "60"))
ABDM_TOKEN_MAX_AGE_SECONDS = int(os.getenv("ABDM_TOKEN_MAX_AGE_SECONDS", "900"))
ABDM_DEFAULT_PURPOSE_CODE = os.getenv("ABDM_DEFAULT_PURPOSE_CODE", "CAREMGT")
ABDM_DEFAULT_PURPOSE_TEXT = os.getenv(
    "ABDM_DEFAULT_PURPOSE_TEXT",
    "Clinical decision support",
)
ABDM_DEFAULT_HI_TYPES = tuple(
    item.strip()
    for item in os.getenv(
        "ABDM_DEFAULT_HI_TYPES",
        "Prescription,DischargeSummary,OPConsultation,DiagnosticReport,ImmunizationRecord,WellnessRecord",
    ).split(",")
    if item.strip()
)

_abdm_http_client: Optional[httpx.AsyncClient] = None
_abdm_token_cache: Dict[str, Any] = {
    "access_token": None,
    "created_at": None,
    "expires_at": None,
}
_abdm_token_lock = asyncio.Lock()


def _current_utc() -> datetime:
    return datetime.now(timezone.utc)


def resolve_callback_base_url(request_base_url: str | None = None) -> str:
    base_url = ABDM_CALLBACK_BASE_URL or (request_base_url or "")
    return base_url.rstrip("/")


def build_callback_url(path: str, request_base_url: str | None = None) -> str:
    base_url = resolve_callback_base_url(request_base_url)
    normalized_path = path if path.startswith("/") else f"/{path}"
    if base_url:
        return f"{base_url}{normalized_path}"
    return normalized_path


async def get_abdm_http_client() -> httpx.AsyncClient:
    global _abdm_http_client

    if _abdm_http_client is None:
        _abdm_http_client = httpx.AsyncClient(
            base_url=ABDM_GATEWAY_BASE_URL,
            timeout=ABDM_REQUEST_TIMEOUT_SECONDS,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )
    return _abdm_http_client


async def initialize_abdm_http_client() -> None:
    await get_abdm_http_client()


async def close_abdm_http_client() -> None:
    global _abdm_http_client

    if _abdm_http_client is not None:
        await _abdm_http_client.aclose()
        _abdm_http_client = None


def _token_is_valid() -> bool:
    expires_at = _abdm_token_cache.get("expires_at")
    created_at = _abdm_token_cache.get("created_at")
    access_token = _abdm_token_cache.get("access_token")
    if not access_token or not isinstance(created_at, datetime):
        return False

    token_age_seconds = (_current_utc() - created_at).total_seconds()
    if token_age_seconds >= ABDM_TOKEN_MAX_AGE_SECONDS:
        return False

    if isinstance(expires_at, datetime):
        return _current_utc() < (expires_at - timedelta(seconds=ABDM_TOKEN_REFRESH_SKEW_SECONDS))

    return True


def _extract_first_string(payload: Any, keys: tuple[str, ...]) -> Optional[str]:
    if not isinstance(payload, dict):
        return None

    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    nested_payload = payload.get("data")
    if isinstance(nested_payload, dict):
        for key in keys:
            value = nested_payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

    nested_response = payload.get("response")
    if isinstance(nested_response, dict):
        for key in keys:
            value = nested_response.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

    return None


def _extract_expiry_seconds(payload: Any) -> int:
    if not isinstance(payload, dict):
        return 3600

    for key in ("expires_in", "expiresIn", "ttl", "expires"):
        value = payload.get(key)
        if isinstance(value, int) and value > 0:
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)

    nested_payload = payload.get("data")
    if isinstance(nested_payload, dict):
        return _extract_expiry_seconds(nested_payload)

    nested_response = payload.get("response")
    if isinstance(nested_response, dict):
        return _extract_expiry_seconds(nested_response)

    return 3600


async def get_abdm_bearer_token(force_refresh: bool = False) -> str:
    if not ABDM_CLIENT_ID or not ABDM_CLIENT_SECRET:
        raise RuntimeError(
            "ABDM_CLIENT_ID and ABDM_CLIENT_SECRET must be set before requesting a gateway session."
        )

    if not force_refresh and _token_is_valid():
        cached_token = _abdm_token_cache.get("access_token")
        if isinstance(cached_token, str) and cached_token.strip():
            return cached_token.strip()

    async with _abdm_token_lock:
        if not force_refresh and _token_is_valid():
            cached_token = _abdm_token_cache.get("access_token")
            if isinstance(cached_token, str) and cached_token.strip():
                return cached_token.strip()

        client = await get_abdm_http_client()

        # ABDM session payloads can vary slightly across sandbox revisions.
        # Keep the body isolated here so you can align it with the latest docs
        # without touching the rest of the code path.
        request_body = {
            "clientId": ABDM_CLIENT_ID,
            "clientSecret": ABDM_CLIENT_SECRET,
        }

        response = await client.post(
            "/v0.5/sessions",
            json=request_body,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-CM-ID": ABDM_CM_ID,
            },
        )
        response.raise_for_status()

        try:
            response_data = response.json()
        except ValueError as exc:
            raise RuntimeError("ABDM session endpoint returned a non-JSON response.") from exc

        access_token = _extract_first_string(
            response_data,
            ("accessToken", "access_token", "token", "jwt"),
        )
        if not access_token:
            raise RuntimeError(
                "ABDM session endpoint did not return an access token. "
                f"Response keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'unknown'}"
            )

        expires_in = _extract_expiry_seconds(response_data)
        _abdm_token_cache["access_token"] = access_token
        _abdm_token_cache["created_at"] = _current_utc()
        _abdm_token_cache["expires_at"] = _current_utc() + timedelta(seconds=expires_in)
        return access_token


async def abdm_gateway_request(
    method: str,
    path: str,
    *,
    json_payload: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    authenticated: bool = True,
    retry_on_unauthorized: bool = True,
) -> Dict[str, Any]:
    client = await get_abdm_http_client()

    request_headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-CM-ID": ABDM_CM_ID,
    }
    if headers:
        request_headers.update(headers)

    if authenticated:
        request_headers["Authorization"] = f"Bearer {await get_abdm_bearer_token()}"

    response = await client.request(method, path, json=json_payload, headers=request_headers)

    if response.status_code == 401 and authenticated and retry_on_unauthorized:
        _abdm_token_cache["access_token"] = None
        _abdm_token_cache["created_at"] = None
        _abdm_token_cache["expires_at"] = None
        request_headers["Authorization"] = f"Bearer {await get_abdm_bearer_token(force_refresh=True)}"
        response = await client.request(method, path, json=json_payload, headers=request_headers)

    response.raise_for_status()

    if not response.content:
        return {}

    try:
        return response.json()
    except ValueError:
        return {"raw_text": response.text}


def reset_abdm_token_cache() -> None:
    _abdm_token_cache["access_token"] = None
    _abdm_token_cache["created_at"] = None
    _abdm_token_cache["expires_at"] = None