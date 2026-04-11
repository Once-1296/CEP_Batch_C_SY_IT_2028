# Backend Refactor Blueprint

This document defines the proposed modular structure for splitting the current monolithic `main.py` into maintainable, testable components.

---

## 1) Target Folder Structure

```text
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   └── supabase.py
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── admin.py
│   │   ├── patients.py
│   │   └── safety.py
│   │
│   ├── controllers/
│   │   ├── __init__.py
│   │   ├── auth_controller.py
│   │   ├── admin_controller.py
│   │   ├── patient_controller.py
│   │   └── safety_controller.py
│   │
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── error_handler.py
│   │   └── request_context.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── patient.py
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── admin.py
│   │   ├── patient.py
│   │   └── safety.py
│   │
│   ├── nlp/
│   │   ├── __init__.py
│   │   ├── pipeline.py
│   │   ├── normalizer.py
│   │   ├── resolver.py
│   │   └── ddi_engine.py
│   │
│   ├── data/
│   │   ├── __init__.py
│   │   └── loaders.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── security.py
│       └── text.py
│
├── data/
│   ├── medicines_cleaned.csv
│   └── drug_interactions_cleaned.csv
│
├── scripts/
│   └── preprocess.py
│
├── requirements.txt
├── .env
└── blueprint.md
```

---

## 2) What Goes Where

### `app/main.py`
- Creates `FastAPI` app.
- Registers CORS and middleware.
- Includes route modules.
- Contains no business logic.

### `app/config/`
- `settings.py`: environment variables (`SUPABASE_URL`, keys, CORS origins, model names).
- `supabase.py`: creates and exposes anon/admin Supabase clients.

### `app/routes/`
- HTTP endpoint declarations only.
- Maps endpoints to controller functions.
- Keeps request/response handling lightweight.

### `app/controllers/`
- Core business workflows:
  - login/auth checks
  - admin creation flows
  - patient CRUD
  - drug safety orchestration
- Raises proper HTTP exceptions (or domain errors handled by middleware).

### `app/middleware/`
- Centralized error response formatting.
- Request context/logging hooks (optional first pass).

### `app/models/`
- Domain-level entities and constants.
- Keep simple if Supabase remains source of truth.

### `app/schemas/`
- Pydantic request/response models currently embedded in `main.py`.
- Split by domain (`auth`, `patient`, `safety`, `admin`).

### `app/nlp/`
- `normalizer.py`: `normalize_input`.
- `resolver.py`: fuzzy match + brand/salt resolution.
- `ddi_engine.py`: DDI comparison logic.
- `pipeline.py`: orchestration helper to keep controllers thin.

### `app/data/loaders.py`
- Loads CSV files at startup.
- Builds lookup dictionaries (`brand_to_salt`, `ddi_by_drug_a`, `ddi_by_drug_b`).
- Exposes cached accessors for O(1) reads.

### `app/utils/`
- `security.py`: password hashing.
- `text.py`: helpers like dosage stripping.

---

## 3) Endpoint-to-Module Mapping

- `POST /api/login` → `routes/auth.py` → `controllers/auth_controller.py`
- `POST /api/admin/add-pharmacist` → `routes/admin.py` → `controllers/admin_controller.py`
- `POST /api/admin/add-admin` → `routes/admin.py` → `controllers/admin_controller.py`
- `GET /api/patients` → `routes/patients.py` → `controllers/patient_controller.py`
- `POST /api/patients` → `routes/patients.py` → `controllers/patient_controller.py`
- `PUT /api/patients/{patient_id}` → `routes/patients.py` → `controllers/patient_controller.py`
- `POST /api/patients/verify` → `routes/patients.py` → `controllers/patient_controller.py`
- `POST /api/check-drug` → `routes/safety.py` → `controllers/safety_controller.py`

---

## 4) Startup and Dependency Flow

1. `app/main.py` starts.
2. `config/settings.py` loads env.
3. `config/supabase.py` initializes clients.
4. `data/loaders.py` initializes CSV lookups.
5. `nlp/pipeline.py` initializes spaCy model.
6. Routers are included.

This keeps heavy initialization in dedicated modules and avoids side effects spread across routes.

---

## 5) Migration Plan (Low-Risk)

### Phase 1: Scaffold
- Create folders and `__init__.py` files.
- Keep old `main.py` running.

### Phase 2: Move Schemas + Utils
- Extract Pydantic models to `app/schemas/*`.
- Extract `hash_password`, `strip_dosage` to `app/utils/*`.

### Phase 3: Move Config + Data + NLP
- Extract env + Supabase initialization.
- Extract CSV + lookup dict loading.
- Extract NLP normalize/resolve/DDI helpers.

### Phase 4: Move Endpoints
- Create route modules and wire controllers.
- Keep endpoint paths unchanged for frontend compatibility.

### Phase 5: Final Cutover
- Replace root execution command from:
  - `uvicorn main:app --reload`
- To:
  - `uvicorn main:app --reload`

---

## 6) Coding Rules During Refactor

- Do not change API contracts (paths, keys, response shapes) unless explicitly planned.
- Keep fuzzy thresholds and matching logic identical in first refactor pass.
- Keep Supabase table names and fields unchanged.
- Refactor for structure first; optimize behavior in a separate pass.

---

## 7) Optional Enhancements (After Refactor)

- Add token-based auth middleware and route guards.
- Add unit tests for NLP resolution and DDI engine.
- Add repository layer for Supabase table operations.
- Add structured logging and request IDs.

---

## 8) Proposed First Commit Scope

If starting implementation now, safest first commit:
- Add `app/` structure and router wiring.
- Move schemas + utils only.
- Keep business logic mostly unchanged.

This gives immediate readability wins with minimal break risk.
