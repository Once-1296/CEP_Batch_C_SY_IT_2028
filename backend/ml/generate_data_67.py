import os
import uuid
import random
import urllib.request
import zipfile
import pandas as pd
from faker import Faker
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from tdc.multi_pred import DDI

fake = Faker('en_IN')

# ==========================================
# 1. PYDANTIC MODELS (Schema Enforcement)
# ==========================================
class PatientModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    abha_id: str
    name: str
    phone: str
    password: str
    registered_by: str

class ABDMMockRecordModel(BaseModel):
    abha_id: str
    basic_health_details: Dict[str, Any] = Field(default_factory=dict)
    pre_existing_conditions: List[Dict[str, Any]] = Field(default_factory=list)
    medication_history: List[Dict[str, Any]] = Field(default_factory=list)
    allergies: List[Dict[str, Any]] = Field(default_factory=list)

class FamilyRelationshipModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    relative_id: str
    relationship_type: str

# ==========================================
# 2. DATASET FETCHERS
# ==========================================
def fetch_tdc_ddi_data(sample_size=200):
    print("Fetching real DDI data from TDCommons (DrugBank)...")
    data = DDI(name='DrugBank')
    df = data.get_data()
    # Randomly sample unique interactions
    df_sampled = df.sample(n=sample_size, random_state=42)
    return df_sampled.to_dict('records')

def fetch_pharmgkb_genetic_data(sample_size=100):
    print("Fetching real Genetic Risk data from PharmGKB...")

    zip_url = "https://api.pharmgkb.org/v1/download/file/data/annotations.zip"
    zip_path = "annotations.zip"
    extract_dir = "pharmgkb_data"

    os.makedirs(extract_dir, exist_ok=True)

    # -------------------------------
    # 1. DOWNLOAD
    # -------------------------------
    if not os.path.exists(zip_path):
        print("Downloading annotations.zip...")
        req = urllib.request.Request(zip_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(zip_path, 'wb') as f:
            f.write(response.read())

    # -------------------------------
    # 2. EXTRACT FILES
    # -------------------------------
    ann_path, meta_path = None, None

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for f in zip_ref.namelist():
            name = f.lower()

            if "clinical_ann.tsv" in name and "metadata" not in name:
                ann_path = zip_ref.extract(f, extract_dir)

            elif "clinical_ann_metadata.tsv" in name:
                meta_path = zip_ref.extract(f, extract_dir)

    if not ann_path or not meta_path:
        raise ValueError("Required PharmGKB files not found in ZIP")

    # -------------------------------
    # 3. LOAD DATA
    # -------------------------------
    ann_df = pd.read_csv(ann_path, sep='\t', on_bad_lines='skip', low_memory=False)
    meta_df = pd.read_csv(meta_path, sep='\t', on_bad_lines='skip', low_memory=False)

    # Clean column names
    ann_df.columns = ann_df.columns.str.strip()
    meta_df.columns = meta_df.columns.str.strip()

    # -------------------------------
    # 4. TYPE NORMALIZATION
    # -------------------------------
    ann_df['Genotype-Phenotype ID'] = ann_df['Genotype-Phenotype ID'].astype(str)

    meta_df['Genotype-Phenotype IDs'] = (
        meta_df['Genotype-Phenotype IDs']
        .astype(str)
        .str.split(',')
    )

    # explode multi-ID column
    meta_df = meta_df.explode('Genotype-Phenotype IDs')
    meta_df['Genotype-Phenotype IDs'] = meta_df['Genotype-Phenotype IDs'].str.strip()

    # -------------------------------
    # 5. MERGE
    # -------------------------------
    merged = ann_df.merge(
        meta_df,
        left_on='Genotype-Phenotype ID',
        right_on='Genotype-Phenotype IDs',
        how='inner'
    )

    if merged.empty:
        raise ValueError("Merge failed: no matching IDs")

    # -------------------------------
    # 6. FILTER HIGH EVIDENCE
    # -------------------------------
    if 'Level of Evidence' in merged.columns:
        filtered = merged[merged['Level of Evidence'].isin(['1A', '1B'])]
        if filtered.empty:
            print("WARNING: No 1A/1B evidence found, using all data")
            filtered = merged
    else:
        print("WARNING: 'Level of Evidence' missing, skipping filter")
        filtered = merged

    # -------------------------------
    # 7. CLEAN
    # -------------------------------
    filtered = filtered.dropna(
        subset=['Gene', 'Related Chemicals', 'Clinical Phenotype']
    )

    if filtered.empty:
        raise ValueError("No usable rows after cleaning")

    # Deduplicate (important after explode)
    filtered = filtered.drop_duplicates(
        subset=['Gene', 'Related Chemicals', 'Clinical Phenotype']
    )

    # -------------------------------
    # 8. SAMPLE
    # -------------------------------
    df_sampled = filtered.sample(
        n=sample_size,
        replace=True,
        random_state=42
    )

    # -------------------------------
    # 9. FORMAT OUTPUT
    # -------------------------------
    result = []
    for _, row in df_sampled.iterrows():
        result.append({
            "Gene": str(row['Gene']),
            "Drug(s)": str(row['Related Chemicals']),
            "Phenotype(s)": str(row['Clinical Phenotype'])
        })

    return result
# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
def generate_abha():
    return f"91-{random.randint(1000,9999)}-{random.randint(1000,9999)}-{random.randint(1000,9999)}"

def generate_vitals():
    blood_groups = ['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-']
    return {
        "blood_group": random.choice(blood_groups),
        "height_cm": random.randint(150, 185),
        "weight_kg": random.randint(50, 90),
        "last_vitals": {
            "blood_pressure": f"{random.randint(110, 130)}/{random.randint(70, 85)}",
            "heart_rate_bpm": random.randint(65, 90)
        }
    }

# ==========================================
# 4. GENERATOR LOGIC (600 - 200 - 200)
# ==========================================
def generate_1000_dataset(pharmacist_id: str, default_password: str):
    patients, abdm_records, family_rels = [], [], []

    # Load Real Datasets
    ddi_pool = fetch_tdc_ddi_data(sample_size=200)
    genetic_pool = fetch_pharmgkb_genetic_data(sample_size=100)

    print("\nGenerating Bucket A: 600 Safe Patients...")
    for _ in range(600):
        abha = generate_abha()
        patients.append(PatientModel(abha_id=abha, name=fake.name(), phone=fake.phone_number(), password=default_password, registered_by=pharmacist_id).model_dump())
        abdm_records.append(ABDMMockRecordModel(abha_id=abha, basic_health_details=generate_vitals(), pre_existing_conditions=[], medication_history=[], allergies=[]).model_dump())

    print("Generating Bucket B: 200 Active DDI Risk Patients...")
    for record in ddi_pool:
        abha = generate_abha()
        # TDC Dataset has Drug1 and Drug2. We assign Drug1 as the active medication.
        active_drug = record.get('Drug1', 'Unknown Drug') 
        
        patients.append(PatientModel(abha_id=abha, name=fake.name(), phone=fake.phone_number(), password=default_password, registered_by=pharmacist_id).model_dump())
        abdm_records.append(ABDMMockRecordModel(
            abha_id=abha, 
            basic_health_details=generate_vitals(), 
            medication_history=[{"medication_name": active_drug, "status": "active", "time_period": "current", "note": "High risk for DDI"}]
        ).model_dump())

    print("Generating Bucket C: 200 Family Risk Patients (100 Pairs)...")
    for record in genetic_pool:
        father_abha, son_abha = generate_abha(), generate_abha()
        last_name = fake.last_name()
        
        gene = str(record.get('Gene', 'Unknown Gene'))
        drug = str(record.get('Drug(s)', 'Unknown Drug'))
        phenotype = str(record.get('Phenotype(s)', 'Toxicity/Adverse Reaction'))

        # --- FATHER ---
        father = PatientModel(abha_id=father_abha, name=f"{fake.first_name_male()} {last_name}", phone=fake.phone_number(), password=default_password, registered_by=pharmacist_id)
        patients.append(father.model_dump())
        abdm_records.append(ABDMMockRecordModel(
            abha_id=father_abha, 
            basic_health_details=generate_vitals(), 
            pre_existing_conditions=[{"condition": f"Genetic Variant: {gene}", "clinical_status": "active"}],
            allergies=[{"allergen": drug, "reaction": phenotype, "severity": "severe"}]
        ).model_dump())

        # --- SON ---
        son = PatientModel(abha_id=son_abha, name=f"{fake.first_name_male()} {last_name}", phone=fake.phone_number(), password=default_password, registered_by=pharmacist_id)
        patients.append(son.model_dump())
        abdm_records.append(ABDMMockRecordModel(abha_id=son_abha, basic_health_details=generate_vitals()).model_dump())

        # --- RELATIONSHIP LINK ---
        family_rels.append(FamilyRelationshipModel(patient_id=son.id, relative_id=father.id, relationship_type="FATHER").model_dump())

    return patients, abdm_records, family_rels

# ==========================================
# 5. EXECUTION
# ==========================================
if __name__ == "__main__":
    MOCK_PHARMACIST_ID = str(uuid.uuid4())
    DEFAULT_PASS = "hashed_password_placeholder"

    print("--- Starting Large-Scale Procedural Patient Generation ---")
    patients_data, abdm_data, family_data = generate_1000_dataset(MOCK_PHARMACIST_ID, DEFAULT_PASS)
    
    print(f"\n✅ Successfully generated:")
    print(f"- {len(patients_data)} Patient Profiles")
    print(f"- {len(abdm_data)} ABDM Medical Records")
    print(f"- {len(family_data)} Family Links")
    import json
    # Save to local storage for ML Training
    with open('patients_data.json', 'w') as f:
        json.dump(patients_data, f)
    with open('abdm_records.json', 'w') as f:
        json.dump(abdm_data, f)
    with open('family_rels.json', 'w') as f:
        json.dump(family_data, f)

    print("✅ Files saved: patients_data.json, abdm_records.json, family_rels.json")