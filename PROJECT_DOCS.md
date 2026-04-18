# Ayush-Guard: Clinical Decision Support System (CDSS)

## 1. Idea & Concept
Ayush-Guard is a prototype **Clinical Decision Support System (CDSS)** specifically aimed at reconciling cross-disciplinary medication regimes (e.g., Allopathic and Ayurvedic medicines). The core problem it solves is adverse Drug-Drug Interactions (DDIs) and genetic sensitivity conflicts when a pharmacist attempts to dispense a new medicine without a holistic view of the patient's existing health profile.

By integrating with the conceptual **ABDM (Ayushman Bharat Digital Mission)** framework, the platform extracts a patient's historical medical records—including active medications, diagnosed pre-existing conditions, and known allergies. A statically stored dataset (cleaned from multiple online datasets including DrugBank, PharmGKB,A-Z Indian medicines, etc.) then steps in to evaluate the safety of the proposed new drug against the patient's accumulated health profile.

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
- **Role:** Deterministic safety scoring, data mapping, and database management.
- **Key Modules:**
  - `app/controllers/safety_controller.py`: The core engine. Loads pre-processed JSON maps into memory and performs multi-stage safety checks (Allergies, DDI, Clinical, Genomic, and Family Inheritance).
  - `app/controllers/abdm_controller.py`: Manages FHIR-like patient records and medication histories.
  - `app/routes/*.py`: Clean API routing using FastAPI’s `APIRouter`.
- **Why FastAPI?** Unmatched async HTTP performance and seamless integration with the deterministic data dictionaries.

---

## 3. Database Schema & Data Strategy Integration
We use **Supabase (PostgreSQL)** to represent our data layer. 

### Core Schema Overview
1. **`patients`**: Stores structural identity data (`name`, `abha_id`, `registered_by` linking to pharmacist). *No medical history is stored here.*
2. **`abdm_mock_records`**: A JSONB representation of the external ABDM gateway. It holds arrays of `medication_history`, `pre_existing_conditions`, and `allergies`.
3. **`access_requests`**: Connects `patients` to `pharmacists` representing the consent framework (PENDING, ACCEPTED, REJECTED).
4. **`family_relationships`**: Maps recursive patient IDs (e.g., Father to Son) to propagate genetic sensitivity warnings (e.g., G6PD Deficiency inheritance).

### Data Dictionary & ETL Pipeline (The `backend/ml/` Ecosystem)
- **Source Data:** We leverage global standards from **DrugBank** (Drug-Drug Interactions), **PharmGKB** (Clinical/Genomic evidence), and a custom **Brand-to-Salt** dataset.
- **`final_generate.py` (ETL Pipeline):** The "brain" of our data strategy. It ingests thousands of records from raw TSVs/CSVs and transforms them into three optimized, memory-resident JSON dictionaries:
  - `brand_to_salt.json`: Maps common brand names (e.g., "Augmentin") to active ingredients.
  - `ddi_map.json`: A bi-directional hash map of hazardous drug pairs.
  - `clinical_map.json`: Maps drugs to contraindicated conditions and genomic markers (rsIDs).
- **Demo Sync:** The pipeline injects explicit "Demo Guarantees" to ensure standard test cases (like Warfarin + Aspirin) always trigger predictable alerts for presentation.

---

## 4. Primary API Routes
- `POST /api/check-drug`: Takes `pharmacist_query` and `abha_id`. Resolves the brand to its salt(s), cross-references the patient's ABDM profile (active meds, conditions, genotypes) against the JSON maps, and outputs a `{"severity_tier": "Red", "risk_probability": 0.89, "message": "..."}` payload.
- `GET /api/patients`: Fetches all patients in the pharmacist's radius. Aggregates `abdm_mock_records` and family history inline only if `access_requests` registers an `"ACCEPTED"` state.
- `POST /api/admin/upload-abdm-record`: The administrative entry point to write massive semi-structured clinical JSON dumps into the native database representing incoming FHIR bundles.

---

## 5. Future Possible Improvements
1. **Real ABDM Gateway Connectivity**: Swapping `abdm_mock_records` for actual HTTPS requests to the National Health Authority (NHA) gateway endpoints, decrypting real FHIR JSONs via Diffie-Hellman keys.
2. **Deep Learning Embeddings**: Rather than relying purely on text matches, passing drug strings through a medical BERT model (e.g., ClinicalBERT) to identify semantic similarities between unstructured physician notes and drug classifications.
3. **Advanced Frontend State Management**: Utilizing React Query or Redux to cache patient histories locally, reducing redundant API trips for users with multiple prescriptions.
4. **Dosage-Specific Risk**: Upgrading the ML model to require drug strength arrays. (e.g., 50mg is safe, but 500mg triggers toxicity warnings).
