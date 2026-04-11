import json

from fastapi import FastAPI, Request


def _normalize_payload(value):
    if isinstance(value, dict):
        return {key: _normalize_payload(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_payload(item) for item in value]
    if isinstance(value, str):
        return value.strip()
    return value


def register_transform_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def transform_middleware(request: Request, call_next):
        content_type = request.headers.get("content-type", "")

        if request.method in {"POST", "PUT", "PATCH"} and "application/json" in content_type:
            raw_body = await request.body()
            if raw_body:
                try:
                    payload = json.loads(raw_body)
                    normalized_payload = _normalize_payload(payload)
                    normalized_raw_body = json.dumps(normalized_payload).encode("utf-8")

                    async def receive():
                        return {"type": "http.request", "body": normalized_raw_body, "more_body": False}

                    request._receive = receive
                except json.JSONDecodeError:
                    pass

        return await call_next(request)