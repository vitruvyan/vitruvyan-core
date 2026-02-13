# 🔬 Test Unitari — Algoritmi VPAR

## Cosa sono

Test **unitari puri** per i 4 motori VPAR (Vitruvyan Processing, Analysis & Reasoning):

| File | Motore | Cosa verifica |
|------|--------|---------------|
| `test_vee_engine.py` | VEE (Explainability Engine) | `explain()`, `explain_comprehensive()`, `analyze_only()`, fallback su errori |
| `test_vare_engine.py` | VARE (Adaptive Risk Engine) | `assess_risk()`, `batch_assess()`, `adjust()`, normalizzazione score, categorie di rischio |
| `test_vsgs_engine.py` | VSGS (Semantic Grounding) | `ground()` con config disabilitata/abilitata, input vuoti, `embed_only()`, classificazione qualità match |
| `test_vwre_engine.py` | VWRE (Weighted Reverse Engineering) | `analyze()`, `compare()`, `batch_analyze()`, verifica residui, narrativa z-score |

## Principi

1. **Zero I/O**: nessun test tocca rete, disco, database. Ogni dipendenza esterna è mockata.
2. **Provider-driven**: ogni motore riceve un `MockProvider` (definito in `conftest.py`) che implementa il contratto ABC del dominio.
3. **Deterministici**: i mock restituiscono sempre gli stessi dati → risultati prevedibili e asserzioni precise.
4. **Edge cases**: ogni file testa anche input vuoti, metriche mancanti, errori di provider, e comportamento di fallback.

## Come eseguire

```bash
# Tutti gli algoritmi
pytest tests/unit/algorithms/ -v

# Un singolo motore
pytest tests/unit/algorithms/test_vee_engine.py -v

# Solo con marker
pytest -m algorithms -v
```

## Fixtures usate (da conftest.py)

| Fixture | Contratto | Usata da |
|---------|-----------|----------|
| `mock_explainability_provider` | `ExplainabilityProvider` | `test_vee_engine.py` |
| `mock_risk_provider` | `RiskProvider` | `test_vare_engine.py` |
| `mock_aggregation_provider` | `AggregationProvider` | `test_vwre_engine.py` |
| `sample_metrics` | — | `test_vee_engine.py` |
| `sample_factors` | — | `test_vwre_engine.py` |
| `sample_risk_data` | — | `test_vare_engine.py` |

## Cosa NON testano

- Integrazione con database reale (PostgreSQL, Qdrant) → vedi `tests/integration/`
- Pipeline LangGraph completa → vedi `tests/integration/`
- Struttura dei file/import → vedi `tests/architectural/`
