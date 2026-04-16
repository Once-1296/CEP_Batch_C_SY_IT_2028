# Ayush-Guard: Clinical Decision Support System (CDSS)

## 1. Idea & Concept
Ayush-Guard is a prototype **Clinical Decision Support System (CDSS)** specifically aimed at reconciling cross-disciplinary medication regimes (e.g., Allopathic and Ayurvedic medicines). The core problem it solves is adverse Drug-Drug Interactions (DDIs) and genetic sensitivity conflicts when a pharmacist attempts to dispense a new medicine without a holistic view of the patient's existing health profile.

By integrating with the conceptual **ABDM (Ayushman Bharat Digital Mission)** framework, the platform extracts a patient's historical medical records—including active medications, diagnosed pre-existing conditions, and known allergies. A machine learning classification model then steps in to evaluate the safety of the proposed new drug against the patient's accumulated health profile.

## 2. Architecture: Frontend & Backend Division
The project strongly separates concerns into a static UI layer and a heavy computational API layer.

### Frontend (React + Vite)
- **Role:** Pure presentation and user interaction.
- **Key Components:**
  - `PatientPanel.jsx`: Displays the selected patient's full clinical profile (read from `abdm_mock_records`).
  - `DashboardPanel.jsx`: The primary interface where a pharmacist initiates a safety check by typing a brand name.
  - `useSafetyCheck.js` (Hook): The bridge to the backend, tracking the NLP/ML pipeline stages visually while the network request is in flight.
- **Why Vite/React?** Provides highly responsive Single Page Application (SPA) mechanics, heavily stylized without page reloads.

### Backend (Python + FastAPI)
- **Role:** NLP normalizations, ML probability scoring, and database interactions.
- **Key Modules:**
  - `app/nlp/cdss.py`: Loads the Scikit-learn `joblib` dump. Evaluates input arrays and calculates a maximum danger probability (`predict_proba`).
  - `app/nlp/normalizer.py` & `resolver.py`: Cleans raw text using `spaCy` NLP and maps brand names to active generic salts using `fuzzywuzzy`.
  - `app/controllers/*.py`: Handles the core business workflows (fetching ABDM JSON payloads, parsing nested conditions, merging family trees).
- **Why FastAPI?** Unmatched async HTTP performance and robust dependency injection for machine learning data loading on startup.

---

## 3. Database Schema & Data Strategy Integration
We use **Supabase (PostgreSQL)** to represent our data layer. 

### Core Schema Overview
1. **`patients`**: Stores structural identity data (`name`, `abha_id`, `registered_by` linking to pharmacist). *No medical history is stored here.*
2. **`abdm_mock_records`**: A JSONB representation of the external ABDM gateway. It holds arrays of `medication_history`, `pre_existing_conditions`, and `allergies`.
3. **`access_requests`**: Connects `patients` to `pharmacists` representing the consent framework (PENDING, ACCEPTED, REJECTED).
4. **`family_relationships`**: Maps recursive patient IDs (e.g., Father to Son) to propagate genetic sensitivity warnings (e.g., G6PD Deficiency inheritance).

### ML Training & Datasets (The `backend/ml/` Ecosystem)
- We used datasets from **DrugBank** (standard DDIs) and **PharmGKB** (Level 1A genetic evidence linking drugs to adverse phenotypes).
- `generate_data_67.py`: Procedurally generates 1000 synthetic `abdm_mock_records` representing the distribution of safe combinations alongside known DrugBank interactions (e.g., Warfarin + Aspirin) and genetic mismatches.
- A `RandomForestClassifier` was trained on text features `"{Proposed Salt} | {Existing Medical Item}"`. Predicting $1$ means the combination was sourced from the hazardous pairs. 
- The resulting tree (`cdss_model.joblib`) is queried by the backend via `predict_proba()` to yield percentage-based confidence bands.

---

## 4. Primary API Routes
- `POST /api/check-drug`: Takes `pharmacist_query` and `abha_id`. Normalizes the drug string, pulls the `abdm_mock_records` via ABHA ID, vectors all active conditions against the proposed drug via the ML model, and outputs a `{"severity_tier": "Red", "risk_probability": 0.89}` payload.
- `GET /api/patients`: Fetches all patients in the pharmacist's radius. Aggregates `abdm_mock_records` and family history inline only if `access_requests` registers an `"ACCEPTED"` state.
- `POST /api/admin/upload-abdm-record`: The administrative entry point to write massive semi-structured clinical JSON dumps into the native database representing incoming FHIR bundles.

---

## 5. Future Possible Improvements
1. **Real ABDM Gateway Connectivity**: Swapping `abdm_mock_records` for actual HTTPS requests to the National Health Authority (NHA) gateway endpoints, decrypting real FHIR JSONs via Diffie-Hellman keys.
2. **Deep Learning Embeddings**: Rather than relying purely on text matches, passing drug strings through a medical BERT model (e.g., ClinicalBERT) to identify semantic similarities between unstructured physician notes and drug classifications.
3. **Advanced Frontend State Management**: Utilizing React Query or Redux to cache patient histories locally, reducing redundant API trips for users with multiple prescriptions.
4. **Dosage-Specific Risk**: Upgrading the ML model to require drug strength arrays. (e.g., 50mg is safe, but 500mg triggers toxicity warnings).
