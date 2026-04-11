import time
import uuid

from fastapi import FastAPI, Request


def register_request_context_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next):
        request.state.request_id = str(uuid.uuid4())
        request.state.request_start = time.perf_counter()
        request.state.user = None
        return await call_next(request)
