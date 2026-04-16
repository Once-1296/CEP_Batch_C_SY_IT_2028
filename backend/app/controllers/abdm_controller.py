from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple
from uuid import uuid4

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from app.config.abdm import (
    ABDM_CONSENT_STATUS_CALLBACK_PATH,
    ABDM_DEFAULT_HI_TYPES,
    ABDM_DEFAULT_PURPOSE_CODE,
    ABDM_DEFAULT_PURPOSE_TEXT,
    ABDM_HEALTH_DATA_CALLBACK_PATH,
    ABDM_HIU_ID,
    ABDM_HIU_NAME,
    ABDM_SESSION_TABLE,
    ABDM_TRACKING_TABLE,
    abdm_gateway_request,
    build_callback_url,
    resolve_callback_base_url,
)
from app.config.abdm_crypto import AbdmCurve25519KeyPair, format_abdm_timestamp
from app.config.supabase import get_supabase_admin
from app.controllers.schema import ABDMConsentInitRequest, ABDMConsentStatusWebhook, ABDMHealthDataWebhook


ABDM_APPROVED_STATUSES = {
    "APPROVED",
    "GRANTED",
    "ACCEPTED",
    "SUCCESS",
    "SUCCESSFUL",
    "CONSENT-APPROVED",
    "CONSENT_GRANTED",
}

ABDM_TRACKING_CACHE_BY_ABHA_ID: Dict[str, Dict[str, Any]] = {}
ABDM_TRACKING_CACHE_BY_CONSENT_REQUEST_ID: Dict[str, Dict[str, Any]] = {}
ABDM_TRACKING_CACHE_BY_CONSENT_ARTIFACT_ID: Dict[str, Dict[str, Any]] = {}
ABDM_TRACKING_CACHE_BY_HEALTH_REQUEST_ID: Dict[str, Dict[str, Any]] = {}


def _now_iso() -> str:
    return format_abdm_timestamp(datetime.now(timezone.utc))


def _dump_model(model: Any) -> Dict[str, Any]:
    dump_method = getattr(model, "model_dump", None)
    if callable(dump_method):
        return dump_method(exclude_none=True)

    legacy_dump = getattr(model, "dict", None)
    if callable(legacy_dump):
        return legacy_dump(exclude_none=True)

    if isinstance(model, dict):
        return {key: value for key, value in model.items() if value is not None}

    raise TypeError("Unsupported model type for ABDM payload extraction")


def _clean_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or None
    if isinstance(value, (int, float, bool)):
        return str(value).strip() or None
    return None


def _first_non_empty(*values: Any) -> Optional[str]:
    for value in values:
        cleaned = _clean_text(value)
        if cleaned:
            return cleaned
    return None


def _deep_lookup(data: Any, path: Tuple[str, ...]) -> Any:
    current = data
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _deep_lookup_string(data: Any, path: Tuple[str, ...]) -> Optional[str]:
    return _clean_text(_deep_lookup(data, path))


def _require_supabase_admin():
    supabase = get_supabase_admin()
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase admin client is not configured")
    return supabase


def _cache_tracking_record(record: Dict[str, Any]) -> Dict[str, Any]:
    cached_record = dict(record)

    abha_id = _clean_text(cached_record.get("abha_id"))
    consent_request_id = _clean_text(cached_record.get("consent_request_id"))
    consent_artifact_id = _clean_text(cached_record.get("consent_artifact_id"))
    health_request_id = _clean_text(cached_record.get("health_request_id"))

    if abha_id:
        ABDM_TRACKING_CACHE_BY_ABHA_ID[abha_id] = cached_record
    if consent_request_id:
        ABDM_TRACKING_CACHE_BY_CONSENT_REQUEST_ID[consent_request_id] = cached_record
    if consent_artifact_id:
        ABDM_TRACKING_CACHE_BY_CONSENT_ARTIFACT_ID[consent_artifact_id] = cached_record
    if health_request_id:
        ABDM_TRACKING_CACHE_BY_HEALTH_REQUEST_ID[health_request_id] = cached_record

    return cached_record


def _store_tracking_record_in_supabase(record: Dict[str, Any]) -> None:
    supabase = _require_supabase_admin()

    # Keep the persisted row compact. The in-memory cache carries the full
    # request/response payloads, while the database row gives us durable
    # correlation across callbacks and restarts.
    db_record = {
        "abha_id": record.get("abha_id"),
        "consent_request_id": record.get("consent_request_id"),
        "consent_artifact_id": record.get("consent_artifact_id"),
        "health_request_id": record.get("health_request_id"),
        "consent_status": record.get("consent_status"),
    }

    try:
        supabase.table(ABDM_TRACKING_TABLE).upsert(db_record, on_conflict="abha_id").execute()
    except Exception as exc:
        # The optional tracking table is useful for persistence, but the local
        # cache still keeps the flow functional during early sandbox testing.
        print(f"ABDM tracking persistence skipped: {exc}")


def _update_tracking_record_in_supabase(record: Dict[str, Any]) -> None:
    supabase = _require_supabase_admin()

    db_record = {
        "consent_request_id": record.get("consent_request_id"),
        "consent_artifact_id": record.get("consent_artifact_id"),
        "health_request_id": record.get("health_request_id"),
        "consent_status": record.get("consent_status"),
    }

    try:
        supabase.table(ABDM_TRACKING_TABLE).update(db_record).eq("abha_id", record.get("abha_id")).execute()
    except Exception as exc:
        print(f"ABDM tracking update skipped: {exc}")


def _lookup_cached_record(**identifiers: Optional[str]) -> Optional[Dict[str, Any]]:
    abha_id = _clean_text(identifiers.get("abha_id"))
    if abha_id and abha_id in ABDM_TRACKING_CACHE_BY_ABHA_ID:
        return dict(ABDM_TRACKING_CACHE_BY_ABHA_ID[abha_id])

    consent_request_id = _clean_text(identifiers.get("consent_request_id"))
    if consent_request_id and consent_request_id in ABDM_TRACKING_CACHE_BY_CONSENT_REQUEST_ID:
        return dict(ABDM_TRACKING_CACHE_BY_CONSENT_REQUEST_ID[consent_request_id])

    consent_artifact_id = _clean_text(identifiers.get("consent_artifact_id"))
    if consent_artifact_id and consent_artifact_id in ABDM_TRACKING_CACHE_BY_CONSENT_ARTIFACT_ID:
        return dict(ABDM_TRACKING_CACHE_BY_CONSENT_ARTIFACT_ID[consent_artifact_id])

    health_request_id = _clean_text(identifiers.get("health_request_id"))
    if health_request_id and health_request_id in ABDM_TRACKING_CACHE_BY_HEALTH_REQUEST_ID:
        return dict(ABDM_TRACKING_CACHE_BY_HEALTH_REQUEST_ID[health_request_id])

    return None


def _session_record_from_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "transaction_id": row.get("transaction_id"),
        "consent_request_id": row.get("consent_request_id"),
        "consent_artifact_id": row.get("consent_artifact_id"),
        "abha_id": row.get("abha_id"),
        "callback_base_url": row.get("callback_base_url"),
        "health_request_id": row.get("health_request_id"),
        "private_key_hex": row.get("private_key_hex"),
        "nonce_hex": row.get("nonce_hex"),
        "status": row.get("status"),
        "error_message": row.get("error_message"),
    }


def _upsert_abdm_session(record: Dict[str, Any]) -> Dict[str, Any]:
    supabase = _require_supabase_admin()

    transaction_id = _clean_text(record.get("transaction_id"))
    if not transaction_id:
        raise HTTPException(status_code=500, detail="ABDM session upsert requires a transaction_id")

    db_record = {
        "transaction_id": transaction_id,
        "consent_request_id": _clean_text(record.get("consent_request_id")),
        "consent_artifact_id": _clean_text(record.get("consent_artifact_id")),
        "abha_id": _clean_text(record.get("abha_id")),
        "callback_base_url": _clean_text(record.get("callback_base_url")),
        "health_request_id": _clean_text(record.get("health_request_id")),
        "private_key_hex": _clean_text(record.get("private_key_hex")),
        "nonce_hex": _clean_text(record.get("nonce_hex")),
        "status": _clean_text(record.get("status")) or "PENDING",
        "error_message": _clean_text(record.get("error_message")),
        "updated_at": _now_iso(),
    }

    try:
        result = supabase.table(ABDM_SESSION_TABLE).upsert(db_record, on_conflict="transaction_id").execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to persist ABDM session: {exc}") from exc

    if result.data and len(result.data) > 0:
        return _session_record_from_row(result.data[0])
    return db_record


def _find_abdm_session(**identifiers: Optional[str]) -> Optional[Dict[str, Any]]:
    supabase = _require_supabase_admin()

    lookup_order = (
        ("transaction_id", identifiers.get("transaction_id")),
        ("consent_artifact_id", identifiers.get("consent_artifact_id")),
        ("consent_request_id", identifiers.get("consent_request_id")),
    )

    for column, value in lookup_order:
        cleaned_value = _clean_text(value)
        if not cleaned_value:
            continue
        try:
            result = supabase.table(ABDM_SESSION_TABLE).select("*").eq(column, cleaned_value).limit(1).execute()
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to read ABDM session: {exc}") from exc

        if result.data and len(result.data) > 0:
            return _session_record_from_row(result.data[0])

    return None


def _update_abdm_session(**updates: Any) -> Optional[Dict[str, Any]]:
    transaction_id = _clean_text(updates.get("transaction_id"))
    if not transaction_id:
        return None

    existing = _find_abdm_session(transaction_id=transaction_id)
    if not existing:
        existing = {"transaction_id": transaction_id}

    merged = {**existing, **updates}
    merged["updated_at"] = _now_iso()
    return _upsert_abdm_session(merged)


def _clear_abdm_private_material(
    transaction_id: str,
    *,
    status: str = "COMPLETED",
    error_message: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    return _update_abdm_session(
        transaction_id=transaction_id,
        private_key_hex=None,
        nonce_hex=None,
        status=status,
        error_message=error_message,
    )


def _mark_abdm_session_failed(transaction_id: Optional[str], error_message: str, **identifiers: Optional[str]) -> Optional[Dict[str, Any]]:
    normalized_transaction_id = _clean_text(transaction_id)
    session = None

    if normalized_transaction_id:
        session = _find_abdm_session(transaction_id=normalized_transaction_id)

    if not session:
        session = _find_abdm_session(
            consent_artifact_id=identifiers.get("consent_artifact_id"),
            consent_request_id=identifiers.get("consent_request_id"),
        )

    if not session:
        return None

    return _update_abdm_session(
        transaction_id=session["transaction_id"],
        consent_request_id=session.get("consent_request_id"),
        consent_artifact_id=session.get("consent_artifact_id"),
        abha_id=session.get("abha_id"),
        callback_base_url=session.get("callback_base_url"),
        health_request_id=session.get("health_request_id"),
        private_key_hex=session.get("private_key_hex"),
        nonce_hex=session.get("nonce_hex"),
        status="FAILED",
        error_message=error_message,
    )


def _lookup_tracking_record_in_supabase(column: str, value: Optional[str]) -> Optional[Dict[str, Any]]:
    if not value:
        return None

    supabase = _require_supabase_admin()
    try:
        result = supabase.table(ABDM_TRACKING_TABLE).select("*").eq(column, value).limit(1).execute()
    except Exception as exc:
        print(f"ABDM tracking lookup skipped: {exc}")
        return None

    if result.data and len(result.data) > 0:
        return dict(result.data[0])
    return None


def _resolve_tracking_record(**identifiers: Optional[str]) -> Optional[Dict[str, Any]]:
    cached_record = _lookup_cached_record(**identifiers)
    if cached_record:
        return cached_record

    lookup_order = (
        ("consent_artifact_id", identifiers.get("consent_artifact_id")),
        ("consent_request_id", identifiers.get("consent_request_id")),
        ("health_request_id", identifiers.get("health_request_id")),
        ("abha_id", identifiers.get("abha_id")),
    )

    for column, value in lookup_order:
        record = _lookup_tracking_record_in_supabase(column, _clean_text(value))
        if record:
            return record

    return None


def _merge_tracking_record(existing: Optional[Dict[str, Any]], updates: Dict[str, Any]) -> Dict[str, Any]:
    merged: Dict[str, Any] = dict(existing or {})
    for key, value in updates.items():
        if value is not None:
            merged[key] = value
    return merged


def _extract_consent_artifact_id(payload: Dict[str, Any]) -> Optional[str]:
    return _first_non_empty(
        payload.get("consent_artifact_id"),
        payload.get("consentArtifactId"),
        payload.get("consent_id"),
        payload.get("consentId"),
        _deep_lookup_string(payload, ("consent", "artifact", "id")),
        _deep_lookup_string(payload, ("consent", "artifactId")),
        _deep_lookup_string(payload, ("consent", "id")),
        _deep_lookup_string(payload, ("artifact", "id")),
        _deep_lookup_string(payload, ("data", "consent_artifact_id")),
        _deep_lookup_string(payload, ("data", "consentArtifactId")),
    )


def _extract_consent_status(payload: Dict[str, Any]) -> Optional[str]:
    return _first_non_empty(
        payload.get("consent_status"),
        payload.get("consentStatus"),
        payload.get("status"),
        payload.get("eventStatus"),
        _deep_lookup_string(payload, ("consent", "status")),
        _deep_lookup_string(payload, ("data", "status")),
    )


def _extract_request_id(payload: Dict[str, Any]) -> Optional[str]:
    return _first_non_empty(
        payload.get("request_id"),
        payload.get("requestId"),
        payload.get("transaction_id"),
        payload.get("transactionId"),
        _deep_lookup_string(payload, ("data", "requestId")),
        _deep_lookup_string(payload, ("response", "requestId")),
    )


def _extract_encrypted_payload(payload: Dict[str, Any]) -> Any:
    for key in (
        "encrypted_payload",
        "encryptedBundle",
        "encrypted_bundle",
        "fhir_bundle",
        "fhirBundle",
        "bundle",
        "payload",
        "data",
    ):
        value = payload.get(key)
        if value is not None:
            return value

    nested_data = payload.get("data")
    if nested_data is not None:
        return nested_data

    return None


def _extract_transaction_id(payload: Dict[str, Any]) -> Optional[str]:
    return _first_non_empty(
        payload.get("transaction_id"),
        payload.get("transactionId"),
        payload.get("request_id"),
        payload.get("requestId"),
    )


def _normalize_error_payload(error_payload: Any) -> Optional[Dict[str, Any]]:
    if error_payload is None:
        return None

    dump_method = getattr(error_payload, "model_dump", None)
    if callable(dump_method):
        error_payload = dump_method(exclude_none=True)

    if isinstance(error_payload, dict):
        normalized_error: Dict[str, Any] = {}
        code = error_payload.get("code")
        message = error_payload.get("message")
        details = error_payload.get("details")
        if code is not None:
            normalized_error["code"] = code
        if message is not None:
            normalized_error["message"] = message
        if details is not None:
            normalized_error["details"] = details
        return normalized_error or None

    if isinstance(error_payload, str):
        return {"message": error_payload}

    return {"message": str(error_payload)}


def _extract_webhook_error(payload: Dict[str, Any], model_error: Any = None) -> Optional[Dict[str, Any]]:
    error_candidates: List[Any] = [model_error]

    for candidate_key in ("error",):
        error_candidates.append(payload.get(candidate_key))

    for nested_key in ("payload", "data", "response", "hiResponse", "hi_response"):
        nested_payload = payload.get(nested_key)
        if isinstance(nested_payload, dict):
            error_candidates.append(nested_payload.get("error"))

    for candidate in error_candidates:
        normalized_error = _normalize_error_payload(candidate)
        if normalized_error:
            return normalized_error

    return None


def _error_message_from_payload(error_payload: Dict[str, Any]) -> str:
    code = _clean_text(error_payload.get("code"))
    message = _clean_text(error_payload.get("message"))
    details = error_payload.get("details")

    if code and message:
        return f"{code}: {message}"
    if message:
        return message
    if code:
        return code
    if details is not None:
        return str(details)
    return "ABDM gateway returned an error payload"


def _ack_webhook(status_code: int, content: Dict[str, Any]) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=content)


def _extract_fhir_display_text(resource: Dict[str, Any]) -> Optional[str]:
    code = resource.get("code")
    if isinstance(code, dict):
        coding = code.get("coding")
        if isinstance(coding, list) and coding:
            first_coding = coding[0]
            if isinstance(first_coding, dict):
                coding_display = _first_non_empty(first_coding.get("display"), first_coding.get("code"))
                if coding_display:
                    return coding_display

        code_text = _clean_text(code.get("text"))
        if code_text:
            return code_text

    if isinstance(code, list) and code:
        first_coding = code[0]
        if isinstance(first_coding, dict):
            coding_display = _first_non_empty(first_coding.get("display"), first_coding.get("code"))
            if coding_display:
                return coding_display

    return _clean_text(resource.get("display"))


def _decrypt_abdm_payload_placeholder(encrypted_payload: Any) -> Dict[str, Any]:
    # Placeholder only: replace this helper with the real ABDM envelope
    # decryption step once you have the sandbox/public-private key material.
    if isinstance(encrypted_payload, dict):
        if encrypted_payload.get("resourceType") == "Bundle" or "entry" in encrypted_payload:
            return encrypted_payload

        for key in ("bundle", "fhir_bundle", "fhirBundle", "payload", "data"):
            nested_value = encrypted_payload.get(key)
            if isinstance(nested_value, dict):
                if nested_value.get("resourceType") == "Bundle" or "entry" in nested_value:
                    return nested_value
            if isinstance(nested_value, str):
                try:
                    parsed_value = json.loads(nested_value)
                except ValueError:
                    continue
                if isinstance(parsed_value, dict):
                    if parsed_value.get("resourceType") == "Bundle" or "entry" in parsed_value:
                        return parsed_value

    if isinstance(encrypted_payload, str):
        try:
            parsed_payload = json.loads(encrypted_payload)
        except ValueError:
            parsed_payload = None

        if isinstance(parsed_payload, dict):
            if parsed_payload.get("resourceType") == "Bundle" or "entry" in parsed_payload:
                return parsed_payload

    raise HTTPException(
        status_code=501,
        detail=(
            "ABDM decryption is still a placeholder. Replace this helper with the "
            "real ABDM payload decryption logic before using live encrypted HIP payloads."
        ),
    )


def _extract_codeable_concept_text(value: Any) -> Optional[str]:
    if isinstance(value, dict):
        direct_text = _clean_text(value.get("text"))
        if direct_text:
            return direct_text

        coding = value.get("coding")
        if isinstance(coding, list):
            for item in coding:
                if isinstance(item, dict):
                    display = _first_non_empty(item.get("display"), item.get("code"))
                    if display:
                        return display

    if isinstance(value, list):
        for item in value:
            extracted_text = _extract_codeable_concept_text(item)
            if extracted_text:
                return extracted_text

    return None


def _deduplicate_preserve_order(values: Iterable[str]) -> List[str]:
    seen: set[str] = set()
    deduplicated_values: List[str] = []
    for value in values:
        cleaned_value = _clean_text(value)
        if not cleaned_value:
            continue
        normalized_value = cleaned_value.lower()
        if normalized_value in seen:
            continue
        seen.add(normalized_value)
        deduplicated_values.append(cleaned_value)
    return deduplicated_values


def _extract_medical_history_and_avoid_list(bundle: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    medical_history: List[str] = []
    medicines_to_avoid: List[str] = []

    entries = bundle.get("entry")
    if not isinstance(entries, list):
        return medical_history, medicines_to_avoid

    for entry in entries:
        if not isinstance(entry, dict):
            continue

        resource = entry.get("resource")
        if not isinstance(resource, dict):
            continue

        resource_type = _clean_text(resource.get("resourceType"))
        if resource_type == "Condition":
            condition_text = _extract_fhir_display_text(resource)
            if condition_text:
                medical_history.append(condition_text)

        elif resource_type == "AllergyIntolerance":
            allergy_text = _extract_fhir_display_text(resource)
            if allergy_text:
                medicines_to_avoid.append(allergy_text)

    return (
        _deduplicate_preserve_order(medical_history),
        _deduplicate_preserve_order(medicines_to_avoid),
    )


def _update_patient_abdm_fields(abha_id: str, medical_history: List[str], medicines_to_avoid: List[str]) -> Dict[str, Any]:
    supabase = _require_supabase_admin()

    # Verify the patient exists
    patient_check = supabase.table("patients").select("id").eq("abha_id", abha_id).execute()
    if not patient_check.data or len(patient_check.data) == 0:
        raise HTTPException(status_code=404, detail=f"Patient with abha_id '{abha_id}' was not found")

    # Write to abdm_mock_records instead of patients table
    upsert_data = {
        "abha_id": abha_id,
        "pre_existing_conditions": [{"condition": c} for c in medical_history] if medical_history else [],
        "allergies": [{"allergen": a} for a in medicines_to_avoid] if medicines_to_avoid else [],
    }

    result = supabase.table("abdm_mock_records").upsert(
        upsert_data, on_conflict="abha_id"
    ).execute()

    if not result.data or len(result.data) == 0:
        raise HTTPException(status_code=500, detail=f"Failed to update ABDM records for '{abha_id}'")

    return dict(result.data[0])


def _build_consent_init_payload(abha_id: str, consent_request_id: str, callback_base_url: str) -> Dict[str, Any]:
    # This payload is intentionally isolated so you can align the exact field
    # names with the current ABDM sandbox contract without touching the route
    # flow. The surrounding code only depends on the request identifiers.
    return {
        "requestId": consent_request_id,
        "timestamp": _now_iso(),
        "hiu": {
            "id": ABDM_HIU_ID,
            "name": ABDM_HIU_NAME,
        },
        "consent": {
            "patient": {
                "id": abha_id,
            },
            "purpose": {
                "code": ABDM_DEFAULT_PURPOSE_CODE,
                "text": ABDM_DEFAULT_PURPOSE_TEXT,
            },
            "hiTypes": list(ABDM_DEFAULT_HI_TYPES),
        },
        "callbackUrl": {
            "consentStatus": build_callback_url(ABDM_CONSENT_STATUS_CALLBACK_PATH, callback_base_url),
            "healthData": build_callback_url(ABDM_HEALTH_DATA_CALLBACK_PATH, callback_base_url),
        },
    }


def _build_health_request_payload(
    consent_request_id: str,
    consent_artifact_id: str,
    callback_base_url: str,
) -> Tuple[str, AbdmCurve25519KeyPair, Dict[str, Any]]:
    # The health-information request is also wrapped here so the request body
    # can be aligned with the current ABDM sandbox documentation in one place.
    health_request_id = str(uuid4())
    crypto_session = AbdmCurve25519KeyPair.generate()
    request_payload = {
        "requestId": health_request_id,
        "transactionId": health_request_id,
        "timestamp": _now_iso(),
        "hiRequest": {
            "consent": {
                "id": consent_artifact_id,
            },
            "reference": {
                "consentRequestId": consent_request_id,
            },
            "dateRange": {
                "from": format_abdm_timestamp(datetime.now(timezone.utc) - timedelta(days=3650)),
                "to": _now_iso(),
            },
            "dataPushUrl": build_callback_url(ABDM_HEALTH_DATA_CALLBACK_PATH, callback_base_url),
            "keyMaterial": crypto_session.request_key_material(),
        },
    }
    return health_request_id, crypto_session, request_payload


async def request_abdm_consent(req: ABDMConsentInitRequest, request: Request) -> Dict[str, Any]:
    supabase = _require_supabase_admin()

    abha_id = _clean_text(req.abha_id)
    if not abha_id:
        raise HTTPException(status_code=400, detail="abha_id is required")

    patient_result = supabase.table("patients").select(
        "id, abha_id"
    ).eq("abha_id", abha_id).limit(1).execute()

    if not patient_result.data:
        raise HTTPException(status_code=404, detail=f"Patient with abha_id '{abha_id}' was not found")

    patient = dict(patient_result.data[0])
    consent_request_id = str(uuid4())
    callback_base_url = resolve_callback_base_url(str(request.base_url))

    if not callback_base_url or any(
        marker in callback_base_url.lower()
        for marker in ("localhost", "127.0.0.1", "0.0.0.0")
    ):
        raise HTTPException(
            status_code=500,
            detail=(
                "Set ABDM_CALLBACK_BASE_URL to your public ngrok URL so ABDM can "
                "reach the webhook endpoints."
            ),
        )

    consent_payload = _build_consent_init_payload(abha_id, consent_request_id, callback_base_url)

    _upsert_abdm_session(
        {
            "transaction_id": consent_request_id,
            "consent_request_id": consent_request_id,
            "abha_id": abha_id,
            "callback_base_url": callback_base_url,
            "status": "CONSENT_REQUESTED",
            "error_message": None,
            "private_key_hex": None,
            "nonce_hex": None,
            "health_request_id": None,
        }
    )

    try:
        gateway_response = await abdm_gateway_request(
            "POST",
            "/v0.5/consent-requests/init",
            json_payload=consent_payload,
        )
    except Exception as exc:
        _update_abdm_session(
            transaction_id=consent_request_id,
            consent_request_id=consent_request_id,
            consent_artifact_id=None,
            abha_id=abha_id,
            callback_base_url=callback_base_url,
            health_request_id=None,
            status="FAILED",
            error_message=str(exc),
            private_key_hex=None,
            nonce_hex=None,
        )
        raise HTTPException(status_code=502, detail=f"ABDM consent init failed: {exc}") from exc

    tracked_record = _merge_tracking_record(
        _resolve_tracking_record(abha_id=abha_id),
        {
            "abha_id": abha_id,
            "patient_id": patient.get("id"),
            "callback_base_url": callback_base_url,
            "consent_request_id": _first_non_empty(
                _extract_request_id(gateway_response),
                consent_request_id,
            ),
            "consent_artifact_id": _first_non_empty(
                _extract_consent_artifact_id(gateway_response),
                _extract_consent_artifact_id(consent_payload),
            ),
            "consent_status": _first_non_empty(_extract_consent_status(gateway_response), "pending"),
            "health_request_id": None,
            "request_payload": consent_payload,
            "gateway_response": gateway_response,
        },
    )

    _cache_tracking_record(tracked_record)
    _store_tracking_record_in_supabase(tracked_record)

    return {
        "status": "success",
        "abha_id": abha_id,
        "consent_request_id": tracked_record.get("consent_request_id"),
        "consent_artifact_id": tracked_record.get("consent_artifact_id"),
        "gateway_response": gateway_response,
        "callback_urls": {
            "consent_status": build_callback_url(ABDM_CONSENT_STATUS_CALLBACK_PATH, callback_base_url),
            "health_data": build_callback_url(ABDM_HEALTH_DATA_CALLBACK_PATH, callback_base_url),
        },
        "patient": patient,
    }


async def handle_consent_status_callback(req: ABDMConsentStatusWebhook) -> JSONResponse:
    payload = _dump_model(req)
    transaction_id = _extract_transaction_id(payload)
    consent_artifact_id = _extract_consent_artifact_id(payload)
    consent_request_id = _clean_text(
        req.consent_request_id or payload.get("consent_request_id") or payload.get("consentRequestId")
    )
    consent_status = _clean_text(_extract_consent_status(payload))
    webhook_error = _extract_webhook_error(payload, getattr(req, "error", None))

    session = _find_abdm_session(
        transaction_id=transaction_id,
        consent_artifact_id=consent_artifact_id,
        consent_request_id=consent_request_id,
    )

    if webhook_error:
        error_message = _error_message_from_payload(webhook_error)
        if session:
            _update_abdm_session(
                transaction_id=session["transaction_id"],
                consent_request_id=session.get("consent_request_id"),
                consent_artifact_id=consent_artifact_id or session.get("consent_artifact_id"),
                abha_id=session.get("abha_id"),
                callback_base_url=session.get("callback_base_url"),
                health_request_id=session.get("health_request_id"),
                private_key_hex=session.get("private_key_hex"),
                nonce_hex=session.get("nonce_hex"),
                status="FAILED",
                error_message=error_message,
            )
        else:
            _mark_abdm_session_failed(transaction_id, error_message, consent_artifact_id=consent_artifact_id, consent_request_id=consent_request_id)

        return _ack_webhook(
            202,
            {
                "status": "accepted",
                "message": "ABDM consent error payload acknowledged",
                "transaction_id": transaction_id,
                "consent_artifact_id": consent_artifact_id,
                "error": webhook_error,
            },
        )

    if not session:
        return _ack_webhook(
            202,
            {
                "status": "accepted",
                "message": "ABDM consent callback acknowledged",
                "detail": "No matching ABDM session row was found",
                "transaction_id": transaction_id,
                "consent_artifact_id": consent_artifact_id,
            },
        )

    normalized_status = (consent_status or session.get("status") or "RECEIVED").upper()
    approved = normalized_status in ABDM_APPROVED_STATUSES or normalized_status in {"APPROVED", "GRANTED", "SUCCESS", "SUCCESSFUL", "ACCEPTED"}

    _update_abdm_session(
        transaction_id=session["transaction_id"],
        consent_request_id=session.get("consent_request_id"),
        consent_artifact_id=consent_artifact_id or session.get("consent_artifact_id"),
        abha_id=session.get("abha_id"),
        callback_base_url=session.get("callback_base_url"),
        health_request_id=session.get("health_request_id"),
        private_key_hex=session.get("private_key_hex"),
        nonce_hex=session.get("nonce_hex"),
        status="CONSENT_GRANTED" if approved else normalized_status,
        error_message=None,
    )

    if not approved:
        return _ack_webhook(
            200,
            {
                "status": "ok",
                "message": "ABDM consent status processed",
                "transaction_id": session["transaction_id"],
                "consent_artifact_id": consent_artifact_id or session.get("consent_artifact_id"),
                "consent_status": normalized_status,
            },
        )

    callback_base_url = _clean_text(session.get("callback_base_url")) or resolve_callback_base_url()
    resolved_consent_artifact_id = _clean_text(consent_artifact_id or session.get("consent_artifact_id"))
    if not resolved_consent_artifact_id:
        error_message = "Consent was approved but no consent_artifact_id could be resolved"
        _mark_abdm_session_failed(session["transaction_id"], error_message, consent_request_id=session.get("consent_request_id"))
        return _ack_webhook(
            202,
            {
                "status": "accepted",
                "message": "ABDM consent callback acknowledged",
                "detail": error_message,
                "transaction_id": session["transaction_id"],
            },
        )

    health_transaction_id, crypto_session, health_request_payload = _build_health_request_payload(
        session.get("consent_request_id") or session["transaction_id"],
        resolved_consent_artifact_id,
        callback_base_url=callback_base_url,
    )

    _upsert_abdm_session(
        {
            "transaction_id": health_transaction_id,
            "consent_request_id": session.get("consent_request_id") or session["transaction_id"],
            "consent_artifact_id": resolved_consent_artifact_id,
            "abha_id": session.get("abha_id"),
            "callback_base_url": callback_base_url,
            "health_request_id": health_transaction_id,
            "private_key_hex": crypto_session.private_key_hex,
            "nonce_hex": crypto_session.nonce_hex,
            "status": "HEALTH_REQUESTED",
            "error_message": None,
        }
    )

    try:
        health_request_response = await abdm_gateway_request(
            "POST",
            "/v0.5/health-information/cm/request",
            json_payload=health_request_payload,
        )
    except Exception as exc:
        error_message = f"ABDM health-information request failed: {exc}"
        _clear_abdm_private_material(health_transaction_id, status="FAILED", error_message=error_message)
        _mark_abdm_session_failed(
            health_transaction_id,
            error_message,
            consent_artifact_id=resolved_consent_artifact_id,
            consent_request_id=session.get("consent_request_id"),
        )
        return _ack_webhook(
            202,
            {
                "status": "accepted",
                "message": "ABDM consent callback acknowledged",
                "detail": error_message,
                "transaction_id": session["transaction_id"],
                "health_request_id": health_transaction_id,
            },
        )

    _update_abdm_session(
        transaction_id=health_transaction_id,
        consent_request_id=session.get("consent_request_id") or session["transaction_id"],
        consent_artifact_id=resolved_consent_artifact_id,
        abha_id=session.get("abha_id"),
        callback_base_url=callback_base_url,
        health_request_id=health_transaction_id,
        private_key_hex=crypto_session.private_key_hex,
        nonce_hex=crypto_session.nonce_hex,
        status="HEALTH_REQUEST_SENT",
        error_message=None,
    )

    _update_abdm_session(
        transaction_id=session["transaction_id"],
        consent_request_id=session.get("consent_request_id") or session["transaction_id"],
        consent_artifact_id=resolved_consent_artifact_id,
        abha_id=session.get("abha_id"),
        callback_base_url=callback_base_url,
        health_request_id=health_transaction_id,
        status="CONSENT_GRANTED",
        error_message=None,
    )

    return _ack_webhook(
        200,
        {
            "status": "success",
            "message": "ABDM consent status processed",
            "transaction_id": session["transaction_id"],
            "consent_artifact_id": resolved_consent_artifact_id,
            "health_request_id": health_transaction_id,
            "health_request_response": health_request_response,
        },
    )


async def handle_health_data_callback(req: ABDMHealthDataWebhook) -> JSONResponse:
    payload = _dump_model(req)
    transaction_id = _extract_transaction_id(payload)
    consent_artifact_id = _extract_consent_artifact_id(payload)
    consent_request_id = _clean_text(
        req.consent_request_id or payload.get("consent_request_id") or payload.get("consentRequestId")
    )
    webhook_error = _extract_webhook_error(payload, getattr(req, "error", None))

    session = _find_abdm_session(
        transaction_id=transaction_id,
        consent_artifact_id=consent_artifact_id,
        consent_request_id=consent_request_id,
    )

    if webhook_error:
        error_message = _error_message_from_payload(webhook_error)
        if session:
            _clear_abdm_private_material(
                session["transaction_id"],
                status="FAILED",
                error_message=error_message,
            )
        return _ack_webhook(
            202,
            {
                "status": "accepted",
                "message": "ABDM health-data error payload acknowledged",
                "transaction_id": transaction_id,
                "consent_artifact_id": consent_artifact_id,
                "error": webhook_error,
            },
        )

    if not session:
        return _ack_webhook(
            202,
            {
                "status": "accepted",
                "message": "ABDM health-data callback acknowledged",
                "detail": "No matching ABDM session row was found",
                "transaction_id": transaction_id,
                "consent_artifact_id": consent_artifact_id,
            },
        )

    private_key_hex = _clean_text(session.get("private_key_hex"))
    nonce_hex = _clean_text(session.get("nonce_hex"))
    if not private_key_hex or not nonce_hex:
        error_message = "Missing Curve25519 key material in Supabase session row"
        _update_abdm_session(
            transaction_id=session["transaction_id"],
            consent_request_id=session.get("consent_request_id"),
            consent_artifact_id=session.get("consent_artifact_id"),
            abha_id=session.get("abha_id"),
            callback_base_url=session.get("callback_base_url"),
            health_request_id=session.get("health_request_id") or transaction_id,
            private_key_hex=session.get("private_key_hex"),
            nonce_hex=session.get("nonce_hex"),
            status="FAILED",
            error_message=error_message,
        )
        return _ack_webhook(
            202,
            {
                "status": "accepted",
                "message": "ABDM health-data callback acknowledged",
                "detail": error_message,
                "transaction_id": session["transaction_id"],
            },
        )

    crypto_session = AbdmCurve25519KeyPair.from_hex_storage(private_key_hex, nonce_hex)

    try:
        decrypted_bundle = crypto_session.decrypt_json_bundle(payload)
    except Exception as exc:
        error_message = str(exc)
        _clear_abdm_private_material(transaction_id or session["transaction_id"], status="FAILED", error_message=error_message)
        _mark_abdm_session_failed(
            transaction_id or session["transaction_id"],
            error_message,
            consent_artifact_id=consent_artifact_id or session.get("consent_artifact_id"),
            consent_request_id=session.get("consent_request_id"),
        )
        return _ack_webhook(
            202,
            {
                "status": "accepted",
                "message": "ABDM health-data callback acknowledged",
                "detail": error_message,
                "transaction_id": transaction_id or session["transaction_id"],
            },
        )

    # Remove the private key material immediately after the payload has been
    # decrypted successfully. The nonce is cleared as well because it is no
    # longer needed once the bundle has been processed.
    _clear_abdm_private_material(transaction_id or session["transaction_id"], status="COMPLETED", error_message=None)

    medical_history, medicines_to_avoid = _extract_medical_history_and_avoid_list(decrypted_bundle)

    resolved_abha_id = _clean_text(session.get("abha_id"))
    if not resolved_abha_id:
        error_message = "Could not resolve the patient's abha_id from the Supabase session row"
        _mark_abdm_session_failed(
            transaction_id or session["transaction_id"],
            error_message,
            consent_artifact_id=consent_artifact_id or session.get("consent_artifact_id"),
            consent_request_id=session.get("consent_request_id"),
        )
        return _ack_webhook(
            202,
            {
                "status": "accepted",
                "message": "ABDM health-data callback acknowledged",
                "detail": error_message,
                "transaction_id": transaction_id or session["transaction_id"],
            },
        )

    try:
        updated_patient = _update_patient_abdm_fields(resolved_abha_id, medical_history, medicines_to_avoid)
    except Exception as exc:
        error_message = f"Failed to update patient rows: {exc}"
        _mark_abdm_session_failed(
            transaction_id or session["transaction_id"],
            error_message,
            consent_artifact_id=consent_artifact_id or session.get("consent_artifact_id"),
            consent_request_id=session.get("consent_request_id"),
        )
        return _ack_webhook(
            202,
            {
                "status": "accepted",
                "message": "ABDM health-data callback acknowledged",
                "detail": error_message,
                "transaction_id": transaction_id or session["transaction_id"],
            },
        )

    _update_abdm_session(
        transaction_id=transaction_id or session["transaction_id"],
        consent_request_id=session.get("consent_request_id"),
        consent_artifact_id=consent_artifact_id or session.get("consent_artifact_id"),
        abha_id=resolved_abha_id,
        callback_base_url=session.get("callback_base_url"),
        health_request_id=transaction_id or session["transaction_id"],
        private_key_hex=None,
        nonce_hex=None,
        status="COMPLETED",
        error_message=None,
    )

    tracked_record = _merge_tracking_record(
        _resolve_tracking_record(abha_id=resolved_abha_id),
        {
            "abha_id": resolved_abha_id,
            "health_request_id": transaction_id or session["transaction_id"],
            "medical_history": medical_history,
            "medicines_to_avoid": medicines_to_avoid,
        },
    )
    _cache_tracking_record(tracked_record)
    _update_tracking_record_in_supabase(tracked_record)

    return _ack_webhook(
        200,
        {
            "status": "success",
            "message": "ABDM health-data callback processed",
            "transaction_id": transaction_id or session["transaction_id"],
            "abha_id": resolved_abha_id,
            "medical_history": medical_history,
            "medicines_to_avoid": medicines_to_avoid,
            "patient": updated_patient,
        },
    )