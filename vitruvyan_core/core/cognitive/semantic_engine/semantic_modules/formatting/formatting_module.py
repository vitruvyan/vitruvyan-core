import re


def clean_text(text: str) -> str:
    """Pulisce il testo da spazi multipli, simboli inutili, ecc."""
    return re.sub(r"\s+", " ", text.strip())