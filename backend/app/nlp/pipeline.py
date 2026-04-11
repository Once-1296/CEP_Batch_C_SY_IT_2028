import spacy

from app.config.settings import SPACY_MODEL


nlp = None


def initialize_nlp_model() -> None:
    global nlp
    nlp = spacy.load(SPACY_MODEL)


def get_nlp():
    return nlp
