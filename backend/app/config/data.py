import pandas as pd

from app.config.settings import MEDICINES_CSV


brand_to_salt: dict[str, str] = {}
brand_name_list: list[str] = []


def initialize_csv_data() -> None:
    global brand_to_salt, brand_name_list

    df_medicines = pd.read_csv(MEDICINES_CSV)

    brand_to_salt = dict(zip(
        df_medicines["brand_name"].str.lower(),
        df_medicines["primary_salt"],
    ))
    brand_name_list = list(brand_to_salt.keys())
    print(f"Loaded {len(brand_name_list)} brand names from medicines_cleaned.csv")


def get_brand_to_salt() -> dict[str, str]:
    return brand_to_salt


def get_brand_name_list() -> list[str]:
    return brand_name_list
