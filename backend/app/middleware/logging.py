import logging
import time

from fastapi import FastAPI, Request


logger = logging.getLogger("ayush_guard.access")


def register_logging_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def logging_middleware(request: Request, call_next):
        started_at = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)

        user = getattr(request.state, "user", None)
        user_label = user.get("username") if isinstance(user, dict) else "anonymous"
        request_id = getattr(request.state, "request_id", "unknown")

        logger.info(
            "request_id=%s method=%s path=%s status=%s user=%s duration_ms=%s",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            user_label,
            elapsed_ms,
        )
        response.headers["X-Request-ID"] = request_id
        return response