# 🔗 Test di Integrazione

## Cosa sono

Test che verificano la **collaborazione tra moduli** — non il singolo componente.
A differenza dei test unitari, qui i moduli reali sono collegati tra loro,
ma le dipendenze esterne (database, API, rete) restano mockate.

| File | Cosa verifica |
|------|---------------|
| `test_vpar_pipeline.py` | Pipeline VPAR completa: VEE → VARE → VWRE su stessa entità |
| `test_domain_contracts.py` | Che i contratti ABC siano implementabili e funzionanti |
| `test_neural_engine_pipeline.py` | Il Neural Engine con provider/strategy mockati |

## Differenza da unit e e2e

```
Unit        →  singolo metodo/classe, tutto mockato
Integration →  più moduli reali collegati, infrastruttura mockata  ← QUI
E2E         →  tutto reale, Docker running, API live
```

## Come eseguire

```bash
pytest tests/integration/ -v
pytest -m integration -v
```

## Requisiti

- `vitruvyan_core` nel PYTHONPATH (il conftest.py lo fa automaticamente)
- NESSUN Docker necessario
- NESSUN database necessario
- Le API LLM sono mockate
