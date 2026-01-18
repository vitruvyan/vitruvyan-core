from typing import Dict, List
from ..entity.entity_module import get_company_names

def enrich_entities(parsed_input: Dict) -> Dict:
    """
    Aggiunge metadati come nomi delle aziende basati sui entity_id estratti.
    """
    entity_ids = parsed_input.get("entity_ids", [])
    company_names = get_company_names(entity_ids)

    return {
        **parsed_input,
        "company_names": company_names
    }


# Test standalone
if __name__ == "__main__":
    test_input = {"entity_ids": ["EXAMPLE_ENTITY_4", "PLTR"]}
    enriched = enrich_entities(test_input)
    print(enriched)