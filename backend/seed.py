import os
import sys
import uuid
from supabase import create_client, Client

# ==========================================
# PATH & IMPORTS CONFIGURATION
# ==========================================
# Add the current directory to sys.path so we can import 'app'
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__))))

from app.config.supabase import SUPABASE_URL, SUPABASE_SERVICE_KEY
from app.config.settings import hash_password

# ==========================================
# SUPABASE INITIALIZATION
# ==========================================
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# ==========================================
# STATIC UUIDs FOR RELATIONAL MAPPING
# ==========================================
pharma_id = str(uuid.uuid4())
patient_safe_id = str(uuid.uuid4())        # Case 1
patient_ddi_id = str(uuid.uuid4())         # Case 3
patient_family_id = str(uuid.uuid4())      # Case 2 (Son)
patient_father_id = str(uuid.uuid4())      # Case 2 (Father)

# ==========================================
# DATA DEFINITIONS
# ==========================================

# Using your hash_password function for realistic seeding
default_password = hash_password("securepassword123")

pharmacists_data = [
    {
        "id": pharma_id,
        "name": "Dr. Ramesh Sharma",
        "username": "ramesh_rx",
        "password": default_password, 
        "phone": "+919876543210",
        "license_number": "RX-MH-10293"
    }
]

patients_data = [
    # Case 1: Safe Patient
    # Rahul has mild hypertension, takes Amlodipine.
    {
        "id": patient_safe_id,
        "abha_id": "91-1111-1111-1111",
        "name": "Rahul Verma",
        "phone": "+919999999991",
        "password": default_password,
        "current_medications": ["Amlodipine 5mg"],
        "current_conditions": ["Hypertension"],
        "registered_by": pharma_id
    },
    # Case 3: Drug-Drug Interaction (Warfarin)
    # Sita is actively taking Warfarin (Blood thinner).
    {
        "id": patient_ddi_id,
        "abha_id": "91-2222-2222-2222",
        "name": "Sita Desai",
        "phone": "+919999999992",
        "password": default_password,
        "current_medications": ["Warfarin 5mg"],
        "current_conditions": ["Atrial Fibrillation"],
        "registered_by": pharma_id
    },
    # Case 2: Unsafe Family History (Son)
    {
        "id": patient_family_id,
        "abha_id": "91-3333-3333-3333",
        "name": "Aryan Singh",
        "phone": "+919999999993",
        "password": default_password,
        "current_medications": [],
        "current_conditions": [],
        "registered_by": pharma_id
    },
    # Case 2: Unsafe Family History (Father - has G6PD deficiency)
    {
        "id": patient_father_id,
        "abha_id": "91-4444-4444-4444",
        "name": "Vikram Singh",
        "phone": "+919999999994",
        "password": default_password,
        "current_conditions": ["Glucose-6-phosphate dehydrogenase (G6PD) deficiency"],
        "medicines_to_avoid": ["Aspirin"],
        "registered_by": pharma_id
    }
]

family_relationships_data = [
    {
        "patient_id": patient_family_id,
        "relative_id": patient_father_id,
        "relationship_type": "FATHER"
    }
]

# ==========================================
# EXECUTION PIPELINE
# ==========================================
def seed_database():
    print("Starting database seed...")

    try:
        # 0. Cleanup existing test data (Idempotency)
        print("Cleaning up old test data...")
        # Since relationships depend on patients, and patients on pharmacists, delete in order
        supabase.table("access_requests").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        supabase.table("family_relationships").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        supabase.table("patients").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        supabase.table("pharmacists").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()

        # 1. Insert Pharmacist
        print("Inserting Pharmacists...")
        supabase.table("pharmacists").insert(pharmacists_data).execute()

        # 2. Insert Patients
        print("Inserting Patients...")
        supabase.table("patients").insert(patients_data).execute()

        # 3. Insert Family Relationships
        print("Inserting Family Relationships...")
        supabase.table("family_relationships").insert(family_relationships_data).execute()

        print("✅ Database successfully seeded!")

        print("\n--- TEST SCENARIOS READY ---")
        print("Case 1 (Safe): Login as 'ramesh_rx' -> Search Rahul Verma -> Try prescribing Augmentin.")
        print("Case 3 (DDI Risk): Search Sita Desai -> Try prescribing Ibuprofen. Should flag Warfarin conflict.")
        print("Case 2 (Family Risk): Search Aryan Singh -> Try prescribing Aspirin. Should flag Father's G6PD deficiency.")

    except Exception as e:
        print(f"❌ Error during seeding: {e}")

if __name__ == "__main__":
    seed_database()