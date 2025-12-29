from typing import Dict, List
from ..entity.entity_module import get_company_names

def enrich_entities(parsed_input: Dict) -> Dict:
    """
    Aggiunge metadati come nomi delle aziende basati sui ticker estratti.
    """
    tickers = parsed_input.get("tickers", [])
    company_names = get_company_names(tickers)

    return {
        **parsed_input,
        "company_names": company_names
    }


# Test standalone
if __name__ == "__main__":
    test_input = {"tickers": ["MSFT", "PLTR"]}
    enriched = enrich_entities(test_input)
    print(enriched)