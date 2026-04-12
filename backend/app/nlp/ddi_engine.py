from fuzzywuzzy import fuzz, process

from app.data.loaders import get_ddi_by_drug_a, get_ddi_by_drug_b
from app.config.settings import strip_dosage


def get_ddi_match_alert(target_salt: str, patient_salts: list[str]):
    if not target_salt:
        return None

    target_salt_lower = target_salt.lower()

    ddi_by_drug_a = get_ddi_by_drug_a()
    ddi_by_drug_b = get_ddi_by_drug_b()

    matched_rows = []

    all_ddi_keys_a = list(ddi_by_drug_a.keys())
    all_ddi_keys_b = list(ddi_by_drug_b.keys())

    matches_a = [match for match, score in process.extract(target_salt_lower, all_ddi_keys_a, limit=None) if score >= 85]
    matches_b = [match for match, score in process.extract(target_salt_lower, all_ddi_keys_b, limit=None) if score >= 85]

    for key in matches_a:
        matched_rows.extend(ddi_by_drug_a.get(key, []))
    for key in matches_b:
        matched_rows.extend(ddi_by_drug_b.get(key, []))

    for row in matched_rows:
        drug_a = str(row.get("drug_a", ""))
        drug_b = str(row.get("drug_b", ""))

        score_a = fuzz.ratio(drug_a.lower(), target_salt_lower)
        score_b = fuzz.ratio(drug_b.lower(), target_salt_lower)

        if score_a >= score_b:
            interacting_salt = drug_b
        else:
            interacting_salt = drug_a

        interacting_salt = strip_dosage(interacting_salt)

        for pat_salt in patient_salts:
            score_pat = fuzz.ratio(interacting_salt.lower(), pat_salt.lower())
            if score_pat >= 85:
                csv_severity = row.get("severity", "Moderate")
                severity_map = {"Major": "Red", "Moderate": "Yellow", "Minor": "Green"}
                return {
                    "severity_tier": severity_map.get(csv_severity, csv_severity),
                    "message": row.get("clinical_effect", "Drug interaction detected."),
                    "suggested_alternative": row.get("safer_alternative"),
                }

    return None
