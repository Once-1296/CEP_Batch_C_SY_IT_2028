from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import (
	CORS_ALLOW_CREDENTIALS,
	CORS_ALLOW_HEADERS,
	CORS_ALLOW_METHODS,
	CORS_ALLOW_ORIGINS,
)
from app.config.abdm import close_abdm_http_client, initialize_abdm_http_client
from app.config.supabase import initialize_supabase_clients
from app.config.data import initialize_csv_data
from app.middleware.auth import register_auth_middleware
from app.middleware.error_handler import register_error_handlers
from app.middleware.logging import register_logging_middleware
from app.middleware.request_context import register_request_context_middleware
from app.middleware.transform import register_transform_middleware
from app.nlp.pipeline import initialize_nlp_model
from app.nlp.cdss import initialize_cdss_model
from app.routes.abdm import router as abdm_router
from app.routes.admin import router as admin_router
from app.routes.auth import router as auth_router
from app.routes.patients import router as patients_router
from app.routes.safety import router as safety_router


app = FastAPI(title="Ayush-Guard API")

# Pura middleware
app.add_middleware(
	CORSMiddleware,
	allow_origins=CORS_ALLOW_ORIGINS,
	allow_credentials=CORS_ALLOW_CREDENTIALS,
	allow_methods=CORS_ALLOW_METHODS,
	allow_headers=CORS_ALLOW_HEADERS,
)
register_error_handlers(app)
register_request_context_middleware(app)
register_logging_middleware(app)
register_transform_middleware(app)
register_auth_middleware(app)
# Yaha tak.

@app.on_event("startup")
async def startup_abdm():
    await initialize_abdm_http_client()

@app.on_event("shutdown")
async def shutdown_abdm():
    await close_abdm_http_client()

# DB Connection.
initialize_supabase_clients()

print("Loading datasets and models...")
try:
	initialize_csv_data()
	initialize_nlp_model()
	initialize_cdss_model()
except Exception as e:
	print(f"Startup Error: {e}. Did you run setup_data.py and download spaCy model?")

# Routing.
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(patients_router)
app.include_router(safety_router)
app.include_router(abdm_router)
