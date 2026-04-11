def strip_dosage(salt: str) -> str:
    if not salt:
        return salt
    return salt.split('(')[0].strip()
