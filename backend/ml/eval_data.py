import json
import joblib
import pandas as pd

def normalize_prescription(presc_dict):
    """
    Normalizes dosage and frequency into standard units (mg and days).
    """
    val = float(presc_dict.get('dosage_value', 0))
    unit = presc_dict.get('dosage_unit', 'mg').lower().strip()
    freq_map = {"OD": 1, "BD": 2, "TID": 3, "QID": 4, "ONCE": 1}
    freq = freq_map.get(presc_dict.get('frequency', 'OD').upper(), 1)
    duration = int(presc_dict.get('duration_days', 1))

    multiplier = 1.0
    if unit in ['g', 'gram']: multiplier = 1000.0
    elif unit == 'mcg': multiplier = 0.001
    
    daily_dose_mg = val * multiplier * freq
    total_course_mg = daily_dose_mg * duration
    
    return {
        "daily_dose_mg": daily_dose_mg,
        "total_days": duration,
        "total_intake_mg": total_course_mg,
        "salt": presc_dict.get('primary_salt', 'Unknown')
    }

def evaluate_prescription(prescription_json):
    """
    Evaluates a proposed prescription JSON using the trained CDSS ML model.
    """
    try:
        model = joblib.load('cdss_model.joblib')
    except Exception as e:
        return {"status": "ERROR", "reason": "Model cdss_model.joblib not found. Train the model first by running train_cdss_model.py."}

    try:
        with open('abdm_records.json', 'r') as f:
            records = json.load(f)
    except Exception as e:
        return {"status": "ERROR", "reason": "abdm_records.json not found."}

    # Extract proposed drug
    proposed_presc = prescription_json.get('proposed_prescription', {})
    patient_abha_id = prescription_json.get('patient_abha_id')
    
    if not proposed_presc or not patient_abha_id:
        return {"status": "ERROR", "reason": "Invalid prescription JSON format."}

    norm_presc = normalize_prescription(proposed_presc)
    proposed_salt = norm_presc['salt']

    # Find the patient
    patient_record = next((r for r in records if r.get('abha_id') == patient_abha_id), None)
    if not patient_record:
        return {"status": "ERROR", "reason": f"Patient with ABHA ID {patient_abha_id} not found."}

    # Collect existing active medications and conditions
    active_items = []
    
    # Active Meds (DDI checks)
    meds = patient_record.get('medication_history', [])
    for m in meds:
        # Generate data 67.py sets status='active' and time_period='current'
        if m.get('status', '').lower() in ['active', 'current'] or m.get('time_period', '').lower() in ['active', 'current']:
            active_items.append(m.get('medication_name', ''))
            
    # Genetic / Pre-existing conditions
    conditions = patient_record.get('pre_existing_conditions', [])
    for c in conditions:
        if 'condition' in c:
            active_items.append(c['condition'])
            
    allergies = patient_record.get('allergies', [])
    for a in allergies:
        if 'allergen' in a:
            active_items.append(f"Allergy: {a['allergen']}")

    # If nothing active to conflict with
    if not active_items:
        return {
            "status": "SAFE",
            "reason": "No active conditions or medications found for potential conflict."
        }

    # Predict using the model
    # Format of features: "ProposedDrug | ExistingMedOrCondition"
    for item in active_items:
        if not item: continue
        
        feature_text = f"{proposed_salt} | {item}"
        pred = model.predict([feature_text])[0]
        
        if pred == 1:
            return {
                "status": "DANGER", 
                "reason": f"Conflict detected between proposed '{proposed_salt}' and patient's '{item}'"
            }

    return {
        "status": "SAFE",
        "reason": "No adverse drug interactions or genetic conflict detected."
    }

if __name__ == "__main__":
    # Test Evaluation script execution mode
    test_json = {
      "proposed_prescription": {
        "brand_name": "Azithral 500 Tablet",
        "primary_salt": "Azithromycin (500mg)",
        "dosage_value": 500,
        "dosage_unit": "mg",
        "frequency": "OD",
        "duration_days": 5
      },
      "patient_abha_id": "91-XXXX-XXXX-XXXX"
    }
    
    try:
        with open('abdm_records.json', 'r') as f:
            test_records = json.load(f)
            if test_records:
                # We'll test with the first patient's ID
                test_json['patient_abha_id'] = test_records[0]['abha_id']
                print(f"Testing with Patient ABHA: {test_json['patient_abha_id']}")
    except:
        pass
        
    result = evaluate_prescription(test_json)
    print("\n--- CDSS Prescription Check Result ---")
    print(json.dumps(result, indent=2))