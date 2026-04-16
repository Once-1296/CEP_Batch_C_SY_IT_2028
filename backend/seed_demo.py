#!/usr/bin/env python3
"""
seed_demo.py — Unified seeder for Ayush-Guard demo.

Pushes to Supabase:
  - 1 Admin (admin / admin123)
  - 1 Pharmacist (pharma1 / pharma123, license PH-DEMO-001)
  - 10 Patients with ABHA IDs
  - 10 abdm_mock_records (6 safe, 2 DDI risk, 2 genetic risk)
  - 10 access_requests (pharma1 → all patients, ACCEPTED)
  - 2 family_relationships (genetic risk patients linked)

Uses helper functions from ml/generate_data_67.py.

Run: cd backend && venv/bin/python seed_demo.py
"""

import os
import sys
import hashlib
import uuid

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from supabase import create_client

# Import helpers from ml/generate_data_67.py
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ml'))
from generate_data_67 import generate_abha, generate_vitals, PatientModel, ABDMMockRecordModel, FamilyRelationshipModel


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def main():
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("ERROR: Set SUPABASE_URL and SUPABASE_SERVICE_KEY in .env")
        sys.exit(1)

    sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    print("Connected to Supabase.\n")

    # ─── 1. Admin ───
    admin_data = {
        "name": "Admin",
        "username": "admin",
        "password": hash_password("admin123"),
    }
    try:
        sb.table("admins").upsert(admin_data, on_conflict="username").execute()
        print("✅ Admin created: admin / admin123")
    except Exception as e:
        print(f"⚠️  Admin creation: {e}")

    # ─── 2. Pharmacist ───
    pharmacist_id = str(uuid.uuid4())
    pharmacist_data = {
        "id": pharmacist_id,
        "name": "Demo Pharmacist",
        "username": "pharma1",
        "password": hash_password("pharma123"),
        "phone": "9876543210",
        "license_number": "PH-DEMO-001",
    }
    try:
        result = sb.table("pharmacists").upsert(pharmacist_data, on_conflict="username").execute()
        if result.data:
            pharmacist_id = result.data[0]["id"]
        print(f"✅ Pharmacist created: pharma1 / pharma123 (ID: {pharmacist_id})")
    except Exception as e:
        print(f"⚠️  Pharmacist creation: {e}")

    # ─── 3. Patients (10 total) ───
    hashed_pw = hash_password("patient123")

    # 6 Safe patients
    safe_patients = []
    safe_meds_sets = [
        # Each tuple: (meds, conditions, allergies) — common/non-conflicting
        (
            [{"medication_name": "Paracetamol", "dosage": "500mg", "status": "active", "time_period": "current"}],
            [{"condition": "Common Cold", "severity": "mild"}],
            [],
        ),
        (
            [{"medication_name": "Metformin", "dosage": "500mg", "status": "active", "time_period": "current"}],
            [{"condition": "Type 2 Diabetes", "severity": "moderate"}],
            [],
        ),
        (
            [{"medication_name": "Cetirizine", "dosage": "10mg", "status": "active", "time_period": "current"}],
            [{"condition": "Seasonal Allergies", "severity": "mild"}],
            [{"allergen": "Dust", "reaction": "Sneezing", "severity": "mild"}],
        ),
        (
            [{"medication_name": "Omeprazole", "dosage": "20mg", "status": "active", "time_period": "current"}],
            [{"condition": "GERD", "severity": "moderate"}],
            [],
        ),
        (
            [{"medication_name": "Amoxicillin", "dosage": "250mg", "status": "active", "time_period": "current"}],
            [],
            [],
        ),
        (
            [{"medication_name": "Vitamin D3", "dosage": "1000IU", "status": "active", "time_period": "current"}],
            [{"condition": "Vitamin D Deficiency", "severity": "mild"}],
            [],
        ),
    ]

    safe_names = [
        "Ananya Sharma", "Rohan Mehta", "Priya Singh",
        "Arjun Patel", "Sneha Iyer", "Vikram Das"
    ]

    for i, (meds, conds, allg) in enumerate(safe_meds_sets):
        abha = generate_abha()
        patient = PatientModel(
            abha_id=abha, name=safe_names[i],
            phone=f"98765{10000+i}", password=hashed_pw,
            registered_by=pharmacist_id,
        )
        abdm = ABDMMockRecordModel(
            abha_id=abha, basic_health_details=generate_vitals(),
            medication_history=meds, pre_existing_conditions=conds, allergies=allg,
        )
        safe_patients.append((patient, abdm))

    # 2 DDI Risk patients
    ddi_patients = []
    ddi_profiles = [
        # Patient on Warfarin — checking Aspirin should trigger DANGER
        {
            "name": "Rahul Verma (DDI Risk)",
            "meds": [
                {"medication_name": "Warfarin", "dosage": "5mg", "status": "active", "time_period": "current"},
                {"medication_name": "Lisinopril", "dosage": "10mg", "status": "active", "time_period": "current"},
            ],
            "conditions": [{"condition": "Deep Vein Thrombosis", "severity": "moderate"}],
            "allergies": [],
        },
        # Patient on Methotrexate — checking Ibuprofen should trigger DANGER
        {
            "name": "Meera Nair (DDI Risk)",
            "meds": [
                {"medication_name": "Methotrexate", "dosage": "15mg", "status": "active", "time_period": "current"},
                {"medication_name": "Folic Acid", "dosage": "5mg", "status": "active", "time_period": "current"},
            ],
            "conditions": [{"condition": "Rheumatoid Arthritis", "severity": "severe"}],
            "allergies": [],
        },
    ]

    for profile in ddi_profiles:
        abha = generate_abha()
        patient = PatientModel(
            abha_id=abha, name=profile["name"],
            phone=f"99887{70000+len(ddi_patients)}", password=hashed_pw,
            registered_by=pharmacist_id,
        )
        abdm = ABDMMockRecordModel(
            abha_id=abha, basic_health_details=generate_vitals(),
            medication_history=profile["meds"],
            pre_existing_conditions=profile["conditions"],
            allergies=profile["allergies"],
        )
        ddi_patients.append((patient, abdm))

    # 2 Genetic Risk patients (linked as father-son)
    genetic_abha_father = generate_abha()
    genetic_abha_son = generate_abha()

    genetic_father = PatientModel(
        abha_id=genetic_abha_father, name="Suresh Kumar (G6PD Father)",
        phone="9911223344", password=hashed_pw, registered_by=pharmacist_id,
    )
    genetic_father_abdm = ABDMMockRecordModel(
        abha_id=genetic_abha_father, basic_health_details=generate_vitals(),
        pre_existing_conditions=[
            {"condition": "G6PD Deficiency", "clinical_status": "active", "severity": "moderate"},
        ],
        allergies=[
            {"allergen": "Aspirin", "reaction": "Hemolytic Anemia", "severity": "severe"},
        ],
        medication_history=[
            {"medication_name": "Acetaminophen", "dosage": "500mg", "status": "active", "time_period": "current"},
        ],
    )

    genetic_son = PatientModel(
        abha_id=genetic_abha_son, name="Amit Kumar (Genetic Risk Son)",
        phone="9911223355", password=hashed_pw, registered_by=pharmacist_id,
    )
    genetic_son_abdm = ABDMMockRecordModel(
        abha_id=genetic_abha_son, basic_health_details=generate_vitals(),
        pre_existing_conditions=[],
        medication_history=[
            {"medication_name": "Cetirizine", "dosage": "10mg", "status": "active", "time_period": "current"},
        ],
        allergies=[],
    )

    family_rel = FamilyRelationshipModel(
        patient_id=genetic_son.id, relative_id=genetic_father.id,
        relationship_type="FATHER",
    )

    # Combine all patients
    all_patients = (
        safe_patients +
        ddi_patients +
        [(genetic_father, genetic_father_abdm), (genetic_son, genetic_son_abdm)]
    )

    # ─── Insert patients ───
    print(f"\nInserting {len(all_patients)} patients...")
    for patient, abdm in all_patients:
        try:
            sb.table("patients").upsert(patient.model_dump(), on_conflict="abha_id").execute()
            sb.table("abdm_mock_records").upsert(abdm.model_dump(), on_conflict="abha_id").execute()
            print(f"  ✅ {patient.name} ({patient.abha_id})")
        except Exception as e:
            print(f"  ⚠️  {patient.name}: {e}")

    # ─── Insert family relationship ───
    print("\nInserting family relationships...")
    try:
        sb.table("family_relationships").insert(family_rel.model_dump()).execute()
        print(f"  ✅ {genetic_son.name} → FATHER → {genetic_father.name}")
    except Exception as e:
        print(f"  ⚠️  Family rel: {e}")

    # ─── Insert access requests (pharma1 → all patients, ACCEPTED) ───
    print(f"\nCreating access requests (pharma1 → all patients, ACCEPTED)...")
    for patient, _ in all_patients:
        try:
            sb.table("access_requests").upsert({
                "id": str(uuid.uuid4()),
                "pharmacist_id": pharmacist_id,
                "patient_id": patient.id,
                "status": "ACCEPTED",
            }, on_conflict="id").execute()
            print(f"  ✅ pharma1 → {patient.name}")
        except Exception as e:
            print(f"  ⚠️  Access request for {patient.name}: {e}")

    # ─── Summary ───
    print("\n" + "="*60)
    print("🎉 SEEDING COMPLETE!")
    print("="*60)
    print(f"\nCredentials:")
    print(f"  Admin:      admin / admin123")
    print(f"  Pharmacist: pharma1 / pharma123")
    print(f"  Patients:   <abha_id> / patient123 (all 10 patients)")
    print(f"\nTest scenarios:")
    print(f"  SAFE:     Search 'Crocin' on any safe patient → Green")
    print(f"  DDI RISK: Search 'Aspirin' on '{ddi_patients[0][0].name}' → Red (Warfarin conflict)")
    print(f"  DDI RISK: Search 'Ibuprofen' on '{ddi_patients[1][0].name}' → Red (Methotrexate conflict)")
    print(f"  GENETIC:  Search 'Aspirin' on '{genetic_son.name}' → Red (Father has G6PD)")
    print(f"\nPharmacist ID: {pharmacist_id}")


if __name__ == "__main__":
    main()
