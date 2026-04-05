// ─── Medicines Master Table (mock subset of ~250k brand catalogue) ───────────
export const DRUGS = {
  dolo:        { brand: 'Dolo 650',     salt: 'Paracetamol',              cat: 'Analgesic / Antipyretic',    habit: false },
  crocin:      { brand: 'Crocin',        salt: 'Paracetamol',              cat: 'Analgesic / Antipyretic',    habit: false },
  calpol:      { brand: 'Calpol',        salt: 'Paracetamol',              cat: 'Analgesic / Antipyretic',    habit: false },
  paracetamol: { brand: 'Crocin',        salt: 'Paracetamol',              cat: 'Analgesic / Antipyretic',    habit: false },
  ibuprofen:   { brand: 'Brufen 400',    salt: 'Ibuprofen',                cat: 'NSAID',                      habit: false },
  brufen:      { brand: 'Brufen 400',    salt: 'Ibuprofen',                cat: 'NSAID',                      habit: false },
  combiflam:   { brand: 'Combiflam',     salt: 'Ibuprofen + Paracetamol',  cat: 'NSAID Combo',                habit: false },
  metformin:   { brand: 'Glycomet 500',  salt: 'Metformin',                cat: 'Antidiabetic',               habit: false },
  glycomet:    { brand: 'Glycomet 500',  salt: 'Metformin',                cat: 'Antidiabetic',               habit: false },
  amlodipine:  { brand: 'Amlokind 5',   salt: 'Amlodipine',               cat: 'Calcium Channel Blocker',    habit: false },
  atorvastatin:{ brand: 'Atorva 10',     salt: 'Atorvastatin',             cat: 'Statin',                     habit: false },
  aspirin:     { brand: 'Aspirin 75mg',  salt: 'Aspirin',                  cat: 'Antiplatelet',               habit: false },
  ecosprin:    { brand: 'Ecosprin 75',   salt: 'Aspirin',                  cat: 'Antiplatelet',               habit: false },
}

// ─── Patients — matches backend mock_patients.json exactly ───────────────────
// These ABHA IDs must match the keys in backend/mock_patients.json
export const PATIENTS = {
  'ABHA-1234-5678': {
    name:       'Rajesh Kumar',
    initials:   'RK',
    abha:       'ABHA-1234-5678',
    age:        58,
    gender:     'Male',
    meds:       ['Amlodipine', 'Methotrexate'],
    conditions: ['Kidney Disease', 'Hypertension'],
    consentTime:'10:15 AM',
  },
  'ABHA-8765-4321': {
    name:       'Priya Sharma',
    initials:   'PS',
    abha:       'ABHA-8765-4321',
    age:        32,
    gender:     'Female',
    meds:       ['Salbutamol'],
    conditions: ['Asthma'],
    consentTime:'11:42 AM',
  },
}

// Default patient for display
export const PATIENT = PATIENTS['ABHA-1234-5678']

// ─── Drug-Drug Interaction Table (mock subset of 200+ DDI dataset) ────────────
export const DDI = [
  {
    a: 'Ibuprofen', b: 'Amlodipine',
    severity: 'Critical',
    effect: 'NSAIDs antagonize antihypertensives. Significant blood pressure elevation risk.',
  },
  {
    a: 'Ibuprofen', b: 'Metformin',
    severity: 'Moderate',
    effect: 'NSAIDs reduce renal blood flow, increasing Metformin accumulation and lactic acidosis risk.',
  },
  {
    a: 'Aspirin', b: 'Metformin',
    severity: 'Moderate',
    effect: 'High-dose Aspirin may potentiate hypoglycemia with Metformin.',
  },
  {
    a: 'Atorvastatin', b: 'Amlodipine',
    severity: 'Minor',
    effect: 'Mild elevation in Atorvastatin plasma levels possible.',
  },
]

// ─── Drug-Condition Contraindication Map (250k Medicines dataset) ─────────────
export const CONTRAINDICATIONS = {
  'Ibuprofen':               ['CKD Stage 2', 'Hypertension'],
  'Aspirin':                 ['Hypertension'],
  'Ibuprofen + Paracetamol': ['CKD Stage 2', 'Hypertension'],
}

// ─── Safe Substitution Engine output ─────────────────────────────────────────
export const SUBSTITUTES = {
  'Ibuprofen': {
    name:   'Paracetamol 500mg',
    brands: 'Crocin / Dolo 500',
    reason: 'Safe for CKD Stage 2 and Hypertension. Same analgesic/antipyretic therapeutic outcome. Max 4g/day.',
  },
  'Aspirin': {
    name:   'Paracetamol 500mg',
    brands: 'Crocin / Dolo 500',
    reason: 'If used for pain/fever — safer alternative. For antiplatelet indication, consult physician before switching.',
  },
  'Ibuprofen + Paracetamol': {
    name:   'Paracetamol 500mg',
    brands: 'Crocin / Dolo 500',
    reason: 'Paracetamol component is safe; Ibuprofen component is contraindicated. Switch to plain Paracetamol.',
  },
}

// ─── DB Schema definitions ────────────────────────────────────────────────────
export const DB_SCHEMA = [
  {
    table: 'medicines_master',
    source: 'Kaggle: A-Z Medicines India (~250k brands)',
    columns: [
      { name: 'brand_id',             type: 'UUID',  key: 'PK' },
      { name: 'brand_name',           type: 'TEXT',  note: 'indexed' },
      { name: 'primary_salt',         type: 'TEXT',  key: 'FK' },
      { name: 'manufacturer',         type: 'TEXT' },
      { name: 'therapeutic_category', type: 'TEXT' },
      { name: 'is_habit_forming',     type: 'BOOL' },
    ],
  },
  {
    table: 'drug_interactions',
    source: 'Kaggle: 200+ DDI Dataset',
    columns: [
      { name: 'interaction_id',    type: 'UUID', key: 'PK' },
      { name: 'interacting_drug_a',type: 'TEXT', key: 'FK' },
      { name: 'interacting_drug_b',type: 'TEXT', key: 'FK' },
      { name: 'severity_tier',     type: 'TEXT' },
      { name: 'clinical_effect',   type: 'TEXT' },
      { name: 'safe_substitute',   type: 'TEXT' },
    ],
  },
  {
    table: 'condition_salt_map',
    source: 'Kaggle: 250k Medicines Usage',
    columns: [
      { name: 'mapping_id',        type: 'UUID', key: 'PK' },
      { name: 'generic_salt_name', type: 'TEXT', key: 'FK' },
      { name: 'treated_condition', type: 'TEXT' },
      { name: 'known_side_effect', type: 'TEXT' },
    ],
  },
  {
    table: 'patient_history',
    source: 'ABDM FHIR R4 (sandbox)',
    columns: [
      { name: 'patient_id',           type: 'UUID',  key: 'PK' },
      { name: 'abha_id',              type: 'TEXT' },
      { name: 'active_medications',   type: 'JSONB' },
      { name: 'diagnosed_conditions', type: 'JSONB' },
      { name: 'consent_token',        type: 'TEXT' },
      { name: 'fhir_bundle_raw',      type: 'JSONB' },
    ],
  },
]

// ─── Pipeline step labels ─────────────────────────────────────────────────────
export const PIPELINE_STEPS = [
  'Input normalization (SciSpacy NLP stripping)',
  'Brand → generic salt mapping (FuzzyWuzzy)',
  'Fetching ABDM FHIR records via HIU API',
  'Drug-drug interaction check (DDI dataset)',
  'Drug-condition contraindication check',
  'Risk stratification & output generation',
]
