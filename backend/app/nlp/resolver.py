from fuzzywuzzy import process

from app.data.loaders import get_brand_name_list, get_brand_to_salt
from app.nlp.normalizer import normalize_input
from app.config.settings import strip_dosage


def resolve_entity(clean_query: str):
    brand_name_list = get_brand_name_list()
    if not brand_name_list:
        return None

    best_match, score = process.extractOne(clean_query, brand_name_list)[:2]

    if score > 70:
        raw_salt = get_brand_to_salt().get(best_match)
        primary_salt = strip_dosage(raw_salt) if raw_salt else raw_salt

        return {
            "brand_matched": best_match,
            "generic_salt": primary_salt,
            "match_score": score,
        }
    return None


def resolve_patient_meds_to_salts(medications: list) -> list:
    resolved_salts = []
    for med_name in medications:
        clean_query = normalize_input(med_name)
        resolved_drug = resolve_entity(clean_query)

        if resolved_drug and resolved_drug["generic_salt"]:
            resolved_salts.append(resolved_drug["generic_salt"])
        else:
            resolved_salts.append(strip_dosage(med_name))

    return resolved_salts
