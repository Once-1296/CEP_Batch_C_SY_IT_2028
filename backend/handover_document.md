# CDSS ML Pipeline - Handover Context
This document serves as the complete context for continuing the Clinical Decision Support System (CDSS) implementation on the new model/session.

## 1. What Has Been Built So Far
We have successfully replaced the old mocked classification script with a **real NLP + Machine Learning CDSS pipeline**.

### `backend/train_cdss_model.py`
- Inherits `.json` datasets from `generate_data_67.py`.
- Parses real positive Drug-Drug interactions (DDI) from **DrugBank** (`drugbank.tab`) and Genetic conditions from **PharmGKB** (`clinical_ann.tsv`).
- Uses a distinct `generate_negative_samples()` logic to randomly map unassociated drugs/genes together to establish "SAFE" (0) labels.
- **Model Pipeline**: A single pipeline using Scikit-Learn `TfidfVectorizer(analyzer='char_wb', ngram_range=(3,5))` and `LogisticRegression(class_weight={0: 1, 1: 5})`.
- The `class_weight` is intentionally skewed to enforce a **near 100% Recall on Danger classifications** to prevent missing any risk.
- Dumps the output to `backend/cdss_model.joblib`. 

### `backend/eval_data.py` (Draft Implementation)
- Loads the `cdss_model.joblib`.
- Currently reads `backend/abdm_records.json` and evaluates a specific JSON format containing a `"proposed_prescription"` against the found active meds & genetic conditions.
- Uses strict normalization logic to parse dosage strings.
- Converts the proposed drug + existing patient records into paired text strings, running them through the model. It breaks execution on the first predicted DANGER (1) class.

## 2. The Next Step (Your Goal)
The next session will need to:
1. **Connect to the Actual API Controllers:**
   - Migrate/refactor the isolated logic from `backend/eval_data.py` directly into the system's actual backend, specifically into `app/controller/safety_controller` (or similar).
2. **Schema Migration:**
   - The current draft reads natively from static `abdm_records.json`. The new model needs to map the patient data retrieval over to the SQL Database structure defined in `latest_schema.sql`.
   - Specifically, patient medical history is currently stored in `abdm_mock_records`, linked natively by `abha_id`.
   - Update the input schemas in Pydantic to cleanly bind with this controller.

## 3. Database Schema Context (from `latest_schema.sql`)
The actual patient data lookup must occur over the following Postgres schema relation:

```sql
CREATE TABLE public.patients (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  abha_id text NOT NULL UNIQUE,
  ...
);

CREATE TABLE public.abdm_mock_records (
  abha_id text NOT NULL,
  basic_health_details jsonb DEFAULT '{}'::jsonb,
  pre_existing_conditions jsonb DEFAULT '[]'::jsonb,
  medication_history jsonb DEFAULT '[]'::jsonb,
  allergies jsonb DEFAULT '[]'::jsonb,
  raw_fhir_bundle jsonb,
  ...
  CONSTRAINT abdm_mock_records_abha_id_fkey FOREIGN KEY (abha_id) REFERENCES public.patients(abha_id)
);
```

**JSON Structure Note:** Inside `abdm_mock_records`, the `medication_history`, `pre_existing_conditions`, and `allergies` columns natively hold the same JSON structures parsed in `eval_data.py`. When building the SQL query in the backend Safety controller, target `abha_id` directly, unnest or iterate through the JSONB rows, and push them to the ML features loop.
