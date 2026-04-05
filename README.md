# Ayush-Guard — Full Project

Point-of-Sale Clinical Decision Support System
**B.Tech IT Community Engineering Project — VJTI Mumbai**

## Project Structure

```
ayush-guard-full/
├── backend/          # FastAPI Python backend
│   ├── main.py
│   ├── preprocess.py
│   ├── medicines_cleaned.csv
│   ├── mock_patients.json
│   ├── mock_rules.json
│   └── users.db
│
└── frontend/         # React + Tailwind CSS frontend
    ├── src/
    │   ├── components/
    │   ├── hooks/
    │   ├── data/
    │   └── ...
    └── ...
```

---

## How to run

### Step 1 — Start the backend

Open a terminal, go into the backend folder:

```bash
cd backend
pip install fastapi uvicorn pandas spacy fuzzywuzzy python-levenshtein
python -m spacy download en_core_web_sm
uvicorn main:app --reload
```

Backend will run on → http://localhost:8000

---

### Step 2 — Start the frontend

Open a **second terminal**, go into the frontend folder:

```bash
cd frontend
npm install
npm run dev
```

Frontend will run on → http://localhost:5173

---

### Step 3 — Open in browser

Go to **http://localhost:5173**

- Sign up as a new pharmacist, then log in
- Select a patient (Rajesh Kumar or Priya Sharma)
- Type a medicine name and click "Run safety check"

---

## Demo medicines to try

| Medicine | Expected result |
|---|---|
| `Augmentin 625` | 🔴 Critical — DDI with Methotrexate (Rajesh Kumar) |
| `Allegra 120mg` | 🔴 Critical — Kidney Disease contraindication (Rajesh Kumar) |
| `Ascoril LS` | ✅ Safe (Rajesh Kumar) |
| `Azithral 500` | ✅ Safe (Priya Sharma) |
| `Ambroxol` | 🟡 Note — antibiotic interaction (Rajesh Kumar) |
