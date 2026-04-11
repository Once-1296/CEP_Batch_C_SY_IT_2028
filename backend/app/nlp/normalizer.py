from app.nlp.pipeline import get_nlp


def normalize_input(query: str) -> str:
    doc = get_nlp()(query.lower())

    noise_words = {"tab", "tablet", "cap", "capsule", "syp", "syrup", "mg", "ml", "drop", "drops"}

    clean_tokens = []
    for token in doc:
        if not token.like_num and not token.is_punct and token.text not in noise_words:
            clean_tokens.append(token.text)

    clean_string = " ".join(clean_tokens)
    return clean_string if clean_string else query.split()[0]
