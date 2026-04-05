import pandas as pd
import json
import re

def process_dataset():
    print("Loading raw dataset...")
    # Load dataset - adjust 'dataset.csv' if your filename is different
    df = pd.read_csv('dataset.csv')

    # 1. Select only the columns critical for our prototype
    columns_to_keep = ['id', 'name', 'short_composition1', 'Therapeutic Class', 'use0']
    df = df[columns_to_keep].copy()

    # 2. Rename columns for easier backend referencing
    df.rename(columns={
        'short_composition1': 'generic_salt', 
        'use0': 'primary_condition', 
        'Therapeutic Class': 'therapeutic_class'
    }, inplace=True)

    # 3. Handle empty/NaN values
    df.fillna('Unknown', inplace=True)

    # 4. Clean the generic salt column using Regex to strip out dosages 
    # Example: "Amoxycillin  (500mg)" becomes "Amoxycillin"
    def clean_salt(salt_string):
        if salt_string == 'Unknown':
            return salt_string
        # Remove anything inside parentheses and strip extra whitespace
        clean_text = re.sub(r'\(.*?\)', '', salt_string)
        return clean_text.strip()

    df['generic_salt'] = df['generic_salt'].apply(clean_salt)

    # Save the ready-to-use dataset
    df.to_csv('medicines_cleaned.csv', index=False)
    print("Saved preprocessed dataset to 'medicines_cleaned.csv'")

def generate_mock_files():
    # MOCK RULES based on the sample data you provided (Amoxycillin & Fexofenadine)
    mock_rules = {
        "drug_condition_interactions": [
            {
                "salt": "Fexofenadine",
                "condition": "Kidney Disease",
                "severity": "Red",
                "alert_message": "CRITICAL: Severe renal impairment detected. Fexofenadine dosage needs strict adjustment or avoidance to prevent toxicity.",
                "suggested_alternative_class": "RESPIRATORY"
            }
        ],
        "drug_drug_interactions": [
            {
                "salt_a": "Amoxycillin",
                "salt_b": "Methotrexate",
                "severity": "Red",
                "alert_message": "CRITICAL: Amoxycillin can decrease the renal excretion of Methotrexate, potentially leading to fatal toxic levels.",
                "suggested_alternative_class": "ANTI INFECTIVES"
            },
            {
                "salt_a": "Ambroxol",
                "salt_b": "Antibiotics",
                "severity": "Yellow",
                "alert_message": "NOTE: Ambroxol increases antibiotic concentration in lung tissue. Usually beneficial, but monitor patient.",
                "suggested_alternative_class": None
            }
        ]
    }

    with open('mock_rules.json', 'w') as f:
        json.dump(mock_rules, f, indent=4)
    print("Generated 'mock_rules.json'")

    # MOCK PATIENTS (Simulated ABDM data)
    mock_patients = {
        "ABHA-1234-5678": {
            "name": "Rajesh Kumar",
            "age": 58,
            "active_conditions": ["Kidney Disease", "Hypertension"],
            "current_medications": ["Amlodipine", "Methotrexate"]
        },
        "ABHA-8765-4321": {
            "name": "Priya Sharma",
            "age": 32,
            "active_conditions": ["Asthma"],
            "current_medications": ["Salbutamol"]
        }
    }

    with open('mock_patients.json', 'w') as f:
        json.dump(mock_patients, f, indent=4)
    print("Generated 'mock_patients.json'")

if __name__ == "__main__":
    process_dataset()
    generate_mock_files()
    print("Phase 1 Data Prep Complete! Ready for Phase 2.")