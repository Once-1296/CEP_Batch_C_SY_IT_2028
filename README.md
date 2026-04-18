# 🛡️ Ayush-Guard: Clinical Decision Support System

**Ayush-Guard** is a sophisticated safety layer designed to reconcile cross-disciplinary medication regimes (e.g., Allopathic and Ayurvedic medicines). It prevents adverse Drug-Drug Interactions (DDIs) and genetic sensitivity conflicts by analyzing a patient's historical medical profile against proposed prescriptions.

---

## 🏗️ Project Structure

```text
.
├── backend/                # Python + FastAPI Backend
│   ├── app/                # Core application logic
│   │   ├── controllers/    # Deterministic safety engine & business logic
│   │   ├── routes/         # API endpoints
│   │   └── config/         # Supabase & Auth configurations
│   ├── ml/                 # Data Science & ETL Pipeline
│   │   ├── final_generate.py # The ETL brain (converts DrugBank/PharmGKB to JSON)
│   │   └── ...
│   ├── data/               # Generated deterministic JSON maps
│   └── main.py             # Server entry point
│
├── frontend/               # React + Vite + Tailwind CSS
│   ├── src/
│   │   ├── components/     # UI Panels (Dashboard, Patient, Safety)
│   │   ├── hooks/          # API interaction hooks
│   │   └── ...
│   └── ...
│
├── PROJECT_DOCS.md         # Detailed Architectural Documentation
└── README.md               # Quick Start Guide
```

---

## 🚀 Quick Start

### 1. Backend Setup

1. **Navigate to backend**:
   ```bash
   cd backend
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**:
   Create a `.env` file in the `backend/` directory:
   ```env
   SUPABASE_URL=your_project_url
   SUPABASE_KEY=your_anon_key
   ```

4. **Run the ETL Pipeline** (Critical):
   Hydrate the safety maps from raw medical datasets:
   ```bash
   python ml/final_generate.py
   ```

5. **Start the API Server**:
   ```bash
   uvicorn main:app --reload
   ```

---

### 2. Frontend Setup

1. **Navigate to frontend**:
   ```bash
   cd frontend
   ```

2. **Install Dependencies**:
   ```bash
   npm install
   ```

3. **Start the Development Server**:
   ```bash
   npm run dev
   ```

---

## 🧪 Demo Scenarios

The system is seeded with specific "Demo Guarantees" to showcase its safety detection capabilities:

| Scenario | Input | Expected Result |
| :--- | :--- | :--- |
| **Drug-Drug Interaction** | `Warfarin` (for patient on `Aspirin`) | 🔴 **Critical DDI**: Severe bleeding risk. |
| **Genomic Risk** | `Aspirin` (for patient with `G6PD Deficiency`) | 🔴 **Critical Genomic**: Risk of acute hemolytic anemia. |
| **Inherited Allergy** | `Amoxicillin` (for relative with Allergy) | 🟡 **Warning**: Family history of penicillin allergy. |
| **Standard Check** | `Crocin` | ✅ **Safe**: No conflicts detected. |

---

## 🛠️ Technology Stack

- **Frontend**: React 18, Vite, Tailwind CSS, Heroicons.
- **Backend Architecture**: FastAPI, Pydantic, Python 3.9+.
- **Database**: Supabase (PostgreSQL) with JSONB for ABDM mocking.
- **Safety Engine**: Deterministic Mapping Engine powered by PharmGKB & DrugBank evidence.

---

## 📄 Documentation

For a deep dive into the architecture, data strategy, and API specifications, please refer to [PROJECT_DOCS.md](PROJECT_DOCS.md) and[Project Report](Project_Report_AyushGuard.docx).
