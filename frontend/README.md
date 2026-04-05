# Ayush-Guard — Frontend Prototype

Point-of-Sale Clinical Decision Support System  
**B.Tech IT Community Engineering Project — VJTI Mumbai**

## Tech Stack
- **React 18** (Vite)
- **Tailwind CSS v3**
- **JavaScript (ES Modules)**

## Project Structure

```
ayush-guard/
├── index.html                   # Vite HTML entry
├── vite.config.js               # Vite + React plugin
├── tailwind.config.js           # Tailwind theme config
├── postcss.config.js            # PostCSS (autoprefixer)
├── package.json
└── src/
    ├── main.jsx                 # ReactDOM.createRoot entry
    ├── App.jsx                  # Root component — tab routing
    ├── index.css                # Tailwind directives + global styles
    │
    ├── data/
    │   └── mockData.js          # All mock DB data (drugs, patient, DDI, schema)
    │
    ├── hooks/
    │   └── useSafetyCheck.js    # Custom hook — simulates FastAPI pipeline
    │
    └── components/
        ├── Header.jsx           # Top nav bar with ABDM status
        ├── Tabs.jsx             # Tab navigation
        ├── AlertBox.jsx         # Reusable alert (critical/warn/safe/info)
        ├── Badge.jsx            # Reusable status badge pill
        ├── PipelineSteps.jsx    # Animated 6-step processing pipeline
        ├── SafetyResult.jsx     # Renders DDI/contraindication check output
        ├── DashboardPanel.jsx   # Tab 1 — Pharmacist dashboard
        ├── PatientPanel.jsx     # Tab 2 — ABDM patient profile + FHIR preview
        ├── SchemaPanel.jsx      # Tab 3 — DB schema viewer (4 tables + RLS)
        └── SubstitutionPanel.jsx# Tab 4 — Safety swap engine demo
```

## Setup & Run

```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build
```

Open http://localhost:5173 in your browser.

## Demo Usage

On the **Pharmacist Dashboard** tab, try typing any of these and pressing Enter or clicking "Run safety check":

| Input | Expected Result |
|---|---|
| `Dolo 650` | ✅ Safe (Paracetamol — no conflicts) |
| `Brufen` | 🔴 Critical (Ibuprofen — conflicts with CKD + Hypertension + Amlodipine) |
| `Combiflam` | 🔴 Critical (NSAID combo — same conflicts) |
| `Metformin` | ⚠️ Moderate (duplicate therapy — patient already on it) |
| `Ecosprin` | ⚠️ Moderate (Aspirin + Metformin DDI + Hypertension conflict) |
| `Crocin` | ✅ Safe |

## Mock Data

All data lives in `src/data/mockData.js` and simulates:
- **`DRUGS`** — brand → generic salt mapping (medicines_master table)
- **`PATIENT`** — ABDM FHIR R4 sandbox record (Ravi Verma, 55M)
- **`DDI`** — drug-drug interaction rules (drug_interactions table)
- **`CONTRAINDICATIONS`** — drug-condition conflict map (condition_salt_map table)
- **`SUBSTITUTES`** — safe alternative suggestions
- **`DB_SCHEMA`** — table definitions for the schema viewer
- **`PIPELINE_STEPS`** — labels for the 6-step processing animation

## Notes for Production

- Replace `useSafetyCheck.js` mock logic with real `fetch()` calls to your **FastAPI** backend
- Replace `mockData.js` patient record with live **ABDM HIU API** FHIR calls
- Connect `SchemaPanel` to your actual **Supabase/PostgreSQL** schema via PostgREST
