# 🧪 Vitruvyan Core — Test Suite

Struttura organizzata per **tipologia di test**, non per modulo.  
Ogni cartella ha il suo README che spiega cosa contiene e perché.

## Struttura

```
tests/
├── conftest.py              ← Fixture globali + mock provider (condivisi da tutti i test)
├── pytest.ini               ← (nella root del repo) Configurazione pytest, markers
│
├── unit/                    ← Test PURI — zero I/O, zero Docker, zero rete
│   ├── algorithms/          ← VPAR: VEE, VARE, VSGS, VWRE
│   ├── agents/              ← LLMAgent (singleton, rate limiter, circuit breaker)
│   ├── orchestration/       ← IntentRegistry, PromptRegistry, GraphState
│   └── llm/                 ← Cache manager, prompt formatting
│
├── conversational/          ← Test CAPACITÀ DISCORSIVE — CAN node, follow-up, routing
│   ├── test_can_context_integration.py
│   ├── test_can_followup_quality.py (futuro)
│   ├── test_can_empathy.py (futuro)
│   └── test_can_routing.py (futuro)
│
├── explainability/          ← Test EXPLAINABILITY ENGINE — VEE multi-livello
│   ├── test_vee_narrative_levels.py
│   ├── test_vee_provider_contract.py (futuro)
│   ├── test_vee_templates.py (futuro)
│   └── test_vee_memory.py (futuro)
│
├── integration/             ← Test CROSS-MODULE — mock di servizi, no Docker
│   ├── test_neural_engine_pipeline.py
│   ├── test_langgraph_flow.py
│   └── test_sacred_orders_contracts.py
│
├── architectural/           ← Test STATICI — analisi AST, invarianti strutturali
│   ├── test_orchestration_contract.py (esistente)
│   ├── test_import_boundaries.py
│   └── test_sacred_order_structure.py
│
└── e2e/                     ← Test END-TO-END — richiedono servizi attivi
    └── (futuro: test con Docker compose)
```

## Come eseguire

```bash
# Tutti i test unitari (veloci, nessuna dipendenza esterna)
pytest tests/unit/ -v

# Solo gli algoritmi VPAR
pytest tests/unit/algorithms/ -v

# Solo i test architetturali
pytest tests/architectural/ -v

# Tutto tranne e2e
pytest -m "not e2e" -v

# Con marker specifico
pytest -m algorithms -v
pytest -m agents -v

# Test conversazionali (CAN node + discourse)
pytest tests/conversational/ -v

# Test explainability (VEE engine)
pytest tests/explainability/ -v

# Un singolo file
pytest tests/unit/algorithms/test_vee_engine.py -v
pytest tests/conversational/test_can_context_integration.py -v
```

## Fixtures disponibili (da conftest.py)

| Fixture | Tipo | Usato da |
|---------|------|----------|
| `mock_explainability_provider` | `ExplainabilityProvider` | Test VEE |
| `mock_risk_provider` | `RiskProvider` | Test VARE |
| `mock_aggregation_provider` | `AggregationProvider` | Test VWRE |
| `mock_data_provider` | `IDataProvider` | Test Neural Engine |
| `mock_scoring_strategy` | `IScoringStrategy` | Test Neural Engine |
| `sample_metrics` | `Dict[str, float]` | Test VEE, metriche generiche |
| `sample_factors` | `Dict[str, float]` | Test VWRE, fattori generici |
| `sample_risk_data` | `Dict` | Test VARE, dati di rischio |

## Convenzioni

- **Naming**: `test_<module>_<what>.py` — es. `test_vee_engine.py`
- **Classi**: `Test<Module><Aspect>` — es. `TestVEEExplain`, `TestVAREEdgeCases`
- **Markers**: ogni test ha un marker (`@pytest.mark.unit`, `@pytest.mark.algorithms`)
- **No hardcoded paths**: usa fixture, non stringhe literali
- **No I/O nei unit**: se un test tocca rete/disco, va in `integration/`
