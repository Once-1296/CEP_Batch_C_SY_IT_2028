import pandas as pd

from app.config.settings import DRUG_INTERACTIONS_CSV, MEDICINES_CSV


brand_to_salt: dict[str, str] = {}
brand_name_list: list[str] = []
ddi_by_drug_a: dict[str, list[dict]] = {}
ddi_by_drug_b: dict[str, list[dict]] = {}


def initialize_csv_data() -> None:
    global brand_to_salt, brand_name_list, ddi_by_drug_a, ddi_by_drug_b

    df_medicines = pd.read_csv(MEDICINES_CSV)

    brand_to_salt = dict(zip(
        df_medicines["brand_name"].str.lower(),
        df_medicines["primary_salt"],
    ))
    brand_name_list = list(brand_to_salt.keys())
    print(f"Loaded {len(brand_name_list)} brand names from medicines_cleaned.csv")

    df_interactions = pd.read_csv(DRUG_INTERACTIONS_CSV)

    ddi_by_drug_a = {}
    ddi_by_drug_b = {}
    for _, row in df_interactions.iterrows():
        row_dict = row.to_dict()
        a_key = str(row["drug_a"]).lower()
        b_key = str(row["drug_b"]).lower()
        ddi_by_drug_a.setdefault(a_key, []).append(row_dict)
        ddi_by_drug_b.setdefault(b_key, []).append(row_dict)
    print(f"Loaded {len(df_interactions)} drug interaction rules from drug_interactions_cleaned.csv")


def get_brand_to_salt() -> dict[str, str]:
    return brand_to_salt


def get_brand_name_list() -> list[str]:
    return brand_name_list


def get_ddi_by_drug_a() -> dict[str, list[dict]]:
    return ddi_by_drug_a


def get_ddi_by_drug_b() -> dict[str, list[dict]]:
    return ddi_by_drug_b
