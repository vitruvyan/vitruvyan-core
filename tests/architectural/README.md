# Test Architetturali (`tests/architectural/`)

## Scopo

I test architetturali **non eseguono logica di business**: verificano che la struttura
del repository rispetti gli invarianti definiti nel `SACRED_ORDER_PATTERN.md` e nelle
linee guida di Copilot. Sono **analisi statica** del codice sorgente.

## Cosa verificano

| File | Invariante |
|------|-----------|
| `test_import_boundaries.py` | Nessun import circolare tra Sacred Order; nessun import `from services.*` in LIVELLO 1; nessun `openai.OpenAI()` fuori da `llm_agent.py` |
| `test_sacred_order_structure.py` | Presenza delle 10 directory obbligatorie per ogni Sacred Order; assenza di `.py` in root (escluso `__init__.py`); `charter.md` in `philosophy/` |

## Marker pytest

```bash
# Solo test architetturali
pytest tests/architectural/ -m architectural -v
```

## Quando eseguirli

- **CI/CD**: su ogni pull request (sono velocissimi — niente I/O)
- **Pre-commit**: dopo refactoring di una Sacred Order
- **Audit periodico**: verifica conformità pattern

## Come aggiungere test

1. Crea un nuovo file `test_<invariante>.py`
2. Usa il marker `@pytest.mark.architectural`
3. Usa `pathlib.Path` o `ast` per analisi statica — **nessun import di moduli runtime**
