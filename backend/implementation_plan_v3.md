# Integrate CDSS ML Model + New Schema (v3 — Final)

*All decisions locked in based on feedback.*

---

## Decisions Summary

| Decision | Resolution |
|----------|-----------|
| Patient creation | **Admin only** — pharmacists only request access |
| Medical data (ABDM records) | **JSON upload** by admin with template + validation |
| ML output | **Probabilities** (`predict_proba`) — % displayed, color-coded |
| CSV DDI engine | **Removed** — ML model handles DDI; `drug_interactions_cleaned.csv` no longer needed |
| Brand resolution CSV | **Kept** — `medicines_cleaned.csv` still needed for brand → salt mapping |
| Safety request format | **Unchanged** — `pharmacist_query` (brand name) + `patient_id` + `abha_id`. ML model only uses `"{salt} \| {item}"` features — dosage/frequency from `eval_data.py` format is unused |
| Python interpreter | `backend/venv/bin/python` |
| Directory cleanup | ML files → `backend/ml/` (no code changes, only path updates in loader) |
| Seeder | Unified `seed_demo.py` — imports from `backend/ml/generate_data_67.py` |
| ABDM controller | Writes to `abdm_mock_records` instead of non-existent patients columns |

---

## Proposed Changes

---

### Phase 1: Directory Cleanup

#### Move files to `backend/ml/`

```
backend/ml/
├── cdss_model.joblib          (trained model)
├── train_cdss_model.py        (training script)
├── eval_data.py               (standalone evaluation — reference only)
├── generate_data_67.py        (data generator — imported by seeder)
├── abdm_records.json          (generated training data)
├── patients_data.json         (generated patient data)
├── family_rels.json           (generated relationships)
├── clinical_ann.tsv           (PharmGKB training data)
├── annotations.zip            (DrugBank annotations)
├── dataset.csv                (large training dataset)
├── pharmgkb_data/             (PharmGKB directory)
└── preprocess.py              (preprocessing script)
```

**Stays in `backend/`:**
- `main.py`, `app/`, `requirements.txt`, `.env`, `.gitignore`
- `medicines_cleaned.csv` (runtime: brand → salt resolution)

**Deleted from `backend/`:**
- `drug_interactions_cleaned.csv` (no longer needed — ML replaces CSV DDI)
- `make_admin.py`, `seed.py` (replaced by `seed_demo.py`)

---

### Phase 2: Backend — Schemas

#### [MODIFY] [schema.py](file:///home/archuserbtw/CEP_Batch_C_SY_IT_2028/backend/app/controllers/schema.py)

```diff
 class CreatePatientRequest(BaseModel):
     name: str
     abha_id: str
     phone: str
     password: str
-    current_medications: List[str] = []
-    current_conditions: List[str] = []
-    added_by: str
+    registered_by: str  # pharmacist UUID

 class UpdatePatientRequest(BaseModel):
     name: Optional[str] = None
     phone: Optional[str] = None
-    current_medications: Optional[List[str]] = None
-    current_conditions: Optional[List[str]] = None

 class DrugCheckRequest(BaseModel):
     pharmacist_query: str
     patient_id: str
+    abha_id: str

+class ABDMRecordUploadRequest(BaseModel):
+    """JSON uploaded by admin for abdm_mock_records"""
+    abha_id: str
+    basic_health_details: Dict[str, Any] = {}
+    pre_existing_conditions: List[Any] = []
+    medication_history: List[Any] = []
+    allergies: List[Any] = []
```

---

### Phase 3: Backend — Remove CSV DDI Engine

#### [DELETE] [ddi_engine.py](file:///home/archuserbtw/CEP_Batch_C_SY_IT_2028/backend/app/nlp/ddi_engine.py)

No longer needed — ML model handles drug-drug interaction detection.

#### [MODIFY] [data.py](file:///home/archuserbtw/CEP_Batch_C_SY_IT_2028/backend/app/config/data.py)

- Remove `DRUG_INTERACTIONS_CSV` import and all DDI-related globals (`ddi_by_drug_a`, `ddi_by_drug_b`) and their initialization.
- Keep brand-to-salt initialization from `medicines_cleaned.csv`.

#### [MODIFY] [settings.py](file:///home/archuserbtw/CEP_Batch_C_SY_IT_2028/backend/app/config/settings.py)

- Remove `DRUG_INTERACTIONS_CSV` constant.

---

### Phase 4: Backend — ML Model Loader

#### [NEW] [cdss.py](file:///home/archuserbtw/CEP_Batch_C_SY_IT_2028/backend/app/nlp/cdss.py)

```python
"""
CDSS ML Model Loader & Evaluator
Loads cdss_model.joblib at startup, exposes predict_risk().
"""
import os
import joblib

_model = None
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'ml', 'cdss_model.joblib')

def initialize_cdss_model():
    global _model
    _model = joblib.load(MODEL_PATH)
    print(f"CDSS model loaded from {MODEL_PATH}")

def get_cdss_model():
    return _model

def predict_risk(proposed_salt: str, active_items: list[str]) -> dict:
    """
    Evaluate proposed drug against all active meds/conditions/allergies.
    Returns: {
        "status": "SAFE" | "DANGER",
        "risk_probability": float (0.0-1.0, max across all items),
        "conflicting_item": str | None,
        "details": list of { item, probability }
    }
    """
    if not _model or not active_items:
        return {"status": "SAFE", "risk_probability": 0.0,
                "conflicting_item": None, "details": []}
    
    max_prob = 0.0
    worst_item = None
    details = []
    
    for item in active_items:
        if not item:
            continue
        feature_text = f"{proposed_salt} | {item}"
        proba = _model.predict_proba([feature_text])[0]
        # Index 1 = DANGER class probability
        danger_prob = float(proba[1]) if len(proba) > 1 else 0.0
        details.append({"item": item, "probability": round(danger_prob, 4)})
        
        if danger_prob > max_prob:
            max_prob = danger_prob
            worst_item = item
    
    return {
        "status": "DANGER" if max_prob >= 0.40 else "SAFE",
        "risk_probability": round(max_prob, 4),
        "conflicting_item": worst_item if max_prob >= 0.40 else None,
        "details": details,
    }
```

---

### Phase 5: Backend — Safety Controller Rewrite

#### [MODIFY] [safety_controller.py](file:///home/archuserbtw/CEP_Batch_C_SY_IT_2028/backend/app/controllers/safety_controller.py)

Complete rewrite of `check_drug_safety()`:

```
Flow:
  1. NLP normalize pharmacist_query → resolve to generic salt
  2. Fetch abdm_mock_records by abha_id
  3. Extract active items: medication_history (active), pre_existing_conditions, allergies
  4. ML predict_proba for each: "{proposed_salt} | {item}"
  5. Compute max danger probability
  6. Severity thresholds:
       ≥ 0.75 → "Red" (Critical)
       ≥ 0.40 → "Yellow" (Moderate)  
       < 0.40 → "Green" (Safe)
  7. Family history check (genetic risk) — from family_relationships + relative's abdm_mock_records
  8. Return response (same shape + risk_probability)
```

**Removed:** DDI engine import, `get_ddi_match_alert()`, patient CSV-based salt resolution.
**Added:** `predict_risk()` from `app.nlp.cdss`, `abdm_mock_records` fetch.

**Response shape:**
```json
{
  "severity_tier": "Red" | "Yellow" | "Green",
  "message": "Conflict detected between Aspirin and Warfarin (87.3% risk)",
  "resolved_data": { "brand_matched": "...", "generic_salt": "...", "match_score": 92 },
  "suggested_alternative": "Paracetamol" | null,
  "risk_probability": 0.873
}
```

---

### Phase 6: Backend — Patient Controller Alignment

#### [MODIFY] [patient_controller.py](file:///home/archuserbtw/CEP_Batch_C_SY_IT_2028/backend/app/controllers/patient_controller.py)

- **`create_patient()`**: Insert only `name, abha_id, phone, password, registered_by`. No medical columns.
- **`update_patient()`**: Only `name`, `phone` updatable.
- **`list_patients()`**: For ACCEPTED-access patients, fetch `abdm_mock_records` by `abha_id` and merge into response.
- **`get_patient_details()`**: When full access, fetch + attach `abdm_mock_records` → `medication_history`, `pre_existing_conditions`, `allergies`.

---

### Phase 7: Backend — Admin Controller

#### [MODIFY] [admin_controller.py](file:///home/archuserbtw/CEP_Batch_C_SY_IT_2028/backend/app/controllers/admin_controller.py)

- **`add_patient()`**: Remove `current_medications` / `current_conditions`. Only schema-valid fields.
- **New: `upload_abdm_record(req: ABDMRecordUploadRequest)`**:
  - Validates `abha_id` exists in `patients` table.
  - Upserts into `abdm_mock_records` with the JSONB fields.
  - Returns success/error.

#### [MODIFY] [admin.py](file:///home/archuserbtw/CEP_Batch_C_SY_IT_2028/backend/app/routes/admin.py) (routes)

- Add: `POST /api/admin/upload-abdm-record`

---

### Phase 8: Backend — ABDM Controller Fix

#### [MODIFY] [abdm_controller.py](file:///home/archuserbtw/CEP_Batch_C_SY_IT_2028/backend/app/controllers/abdm_controller.py)

- **`_update_patient_abdm_fields()`**: Change from
  ```python
  supabase.table("patients").update({"medical_history": ..., "medicines_to_avoid": ...})
  ```
  to
  ```python
  supabase.table("abdm_mock_records").upsert({"abha_id": ..., "pre_existing_conditions": ..., "medication_history": ..., "allergies": ...})
  ```

---

### Phase 9: Backend — Main Entry

#### [MODIFY] [main.py](file:///home/archuserbtw/CEP_Batch_C_SY_IT_2028/backend/main.py)

- Add `from app.nlp.cdss import initialize_cdss_model` → call at startup.
- Remove `DRUG_INTERACTIONS_CSV` related init if still referenced.

---

### Phase 10: Frontend — Safety Hook

#### [MODIFY] [useSafetyCheck.js](file:///home/archuserbtw/CEP_Batch_C_SY_IT_2028/frontend/src/hooks/useSafetyCheck.js)

- `runCheck(rawInput, patientId, abhaId)` — 3rd param.
- POST body: `{ pharmacist_query, patient_id, abha_id }`.
- Pipeline steps: `['Input normalization', 'Brand-to-generic mapping', 'Patient record retrieval', 'ML model classification', 'Risk output']`.
- Result object: include `risk_probability` from response.

---

### Phase 11: Frontend — SafetyResult (Probability Display)

#### [MODIFY] [SafetyResult.jsx](file:///home/archuserbtw/CEP_Batch_C_SY_IT_2028/frontend/src/components/SafetyResult.jsx)

Add a **risk probability bar/badge** below the existing severity badge:
- Shows `"Risk: 87.3%"` with a small progress bar.
- Color coded: ≥75% red, ≥40% amber, <40% green.
- Small text: `"ML confidence based on patient's active medications and conditions"`.
- No other structural changes.

---

### Phase 12: Frontend — DashboardPanel

#### [MODIFY] [DashboardPanel.jsx](file:///home/archuserbtw/CEP_Batch_C_SY_IT_2028/frontend/src/components/DashboardPanel.jsx)

- Pass `abhaId` to `runCheck()` from selected patient's `abha_id` field.
- Patient info strip: display `medication_history` items (extract `medication_name` from JSONB objects) and `pre_existing_conditions` items (extract `condition` from JSONB objects).
- Remove old `current_medications` / `current_conditions` references.

---

### Phase 13: Frontend — PatientPanel

#### [MODIFY] [PatientPanel.jsx](file:///home/archuserbtw/CEP_Batch_C_SY_IT_2028/frontend/src/components/PatientPanel.jsx)

- **Display mode**: Read `medication_history`, `pre_existing_conditions`, `allergies` from merged API response.
- **Edit mode**: Only `name` + `phone`. Remove medication/condition editing.
- **Add patient form**: Remove entirely (admin-only via AdminPanel).
- Show `abha_id` in record info.

---

### Phase 14: Frontend — AdminPanel

#### [MODIFY] [AdminPanel.jsx](file:///home/archuserbtw/CEP_Batch_C_SY_IT_2028/frontend/src/components/AdminPanel.jsx)

- **Add Patient form**: Remove `current_medications`, `current_conditions` fields. Add `abha_id` field. Send `registered_by` (pharmacist UUID) instead of `added_by`.
- **New section: Upload ABDM Record**:
  - Textarea for JSON paste + file upload button.
  - Template example displayed in a collapsible `<details>`:
    ```json
    {
      "abha_id": "12-3456-7890-1234",
      "basic_health_details": { "blood_group": "O+", "height_cm": 170 },
      "pre_existing_conditions": [
        { "condition": "Hypertension", "severity": "moderate" }
      ],
      "medication_history": [
        { "medication_name": "Amlodipine", "dosage": "5mg", "status": "active" }
      ],
      "allergies": [
        { "allergen": "Penicillin", "reaction": "Rash" }
      ]
    }
    ```
  - Client-side JSON parse validation before sending.
  - POST to `/api/admin/upload-abdm-record`.

---

### Phase 15: Unified Seeder

#### [NEW] [seed_demo.py](file:///home/archuserbtw/CEP_Batch_C_SY_IT_2028/backend/seed_demo.py)

Combines `make_admin.py` + `seed.py`. Imports helper functions from `ml/generate_data_67.py`.

**Inserts into Supabase:**

| Entity | Count | Details |
|--------|-------|---------|
| Admin | 1 | `admin / admin123` |
| Pharmacist | 1 | `pharma1 / pharma123`, license `PH-DEMO-001` |
| Patients | 10 | ABHA IDs, registered_by → pharmacist |
| abdm_mock_records | 10 | 6 safe + 2 DDI risk + 2 genetic risk |
| access_requests | 10 | pharma1 → all patients, ACCEPTED |
| family_relationships | 2 | Links genetic risk patients together |

**Patient profiles:**
- **Safe (6):** Common meds (paracetamol, metformin, etc.), no conflicts with demo drugs
- **DDI Risk (2):** e.g., Patient on Warfarin (check Aspirin → DANGER), Patient on Methotrexate (check Ibuprofen → DANGER)
- **Genetic Risk (2):** e.g., G6PD deficiency in family, CYP2D6 poor metabolizer

**Run:** `cd backend && venv/bin/python seed_demo.py`

---

## Execution Order

1. Phase 1: Directory cleanup (move files)
2. Phase 2-3: Backend schema + remove DDI engine
3. Phase 4-5: ML model loader + safety controller
4. Phase 6-9: Patient/admin/ABDM controllers + main.py
5. Phase 10-14: Frontend adjustments
6. Phase 15: Seeder

---

## Verification Plan

### Automated (after seeding)
```bash
# Start backend
cd backend && venv/bin/python -m uvicorn main:app --reload

# Test login
curl -X POST localhost:8000/api/login -H "Content-Type: application/json" \
  -d '{"username":"pharma1","password":"pharma123"}'

# Test safety check (DDI-risk patient)
curl -X POST localhost:8000/api/check-drug \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer fake-jwt-pharma1" \
  -d '{"pharmacist_query":"Aspirin","patient_id":"<uuid>","abha_id":"<abha>"}'
# Expected: severity_tier=Red, risk_probability ≥ 0.75

# Test safety check (safe patient)  
# Expected: severity_tier=Green, risk_probability < 0.40
```

### Browser Verification
1. Admin login → add patient with ABHA ID → upload ABDM JSON → verify saved
2. Pharmacist login → select DDI-risk patient → run safety check → verify Red + probability %
3. Pharmacist → select safe patient → verify Green + low probability
4. Patient login → access request dashboard → accept/reject works
