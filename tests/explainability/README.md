# 🔍 Explainability Engine Tests (VEE)

Test suite per il Vitruvyan Explainability Engine (VEE 3.0).

## Obiettivo

Verificare che VEE generi spiegazioni:
- **Multi-livello** (quick, detailed, expert, visual)
- **Domain-agnostic** (zero hardcoded domain knowledge)
- **Template-based** (via ExplainabilityProvider contract)
- **Memory-enriched** (context storico quando disponibile)

## Architettura VEE

```
ExplainabilityProvider (Contract)
         ↓
    VEEEngine (Orchestrator)
         ↓
    ┌────┴────┐
    ↓         ↓         ↓         ↓
Analyzer  Generator  Memory    Formatter
    ↓         ↓         ↓         ↓
  Signals  Templates  Historical  Output
```

## Categorie Test

### 1. Provider Contract (`test_vee_provider_contract.py`)
Verifica che VEE rispetti il contract:
- Accetta qualsiasi provider che implementa `ExplainabilityProvider`
- Non assume valori di default per nessun dominio
- Fallisce gracefully se provider manca

### 2. Multi-Level Narratives (`test_vee_narrative_levels.py`)
Testa generazione per ogni livello:
- **Quick**: 1-2 frasi, high-level insight
- **Detailed**: Paragrafo con cause/effetti
- **Expert**: Analisi tecnica con metriche precise
- **Visual**: Descrizione per grafici (futuro)

### 3. Template Injection (`test_vee_templates.py`)
Valida template system:
- Placeholder replacement: `{entity_id}`, `{metric_value}`, `{signal_type}`
- Condizionali: `{if momentum > 0.5}strong{else}weak{endif}`
- Domain-specific vocabulary injection

### 4. Memory Enrichment (`test_vee_memory.py`)
Verifica context storico:
- Confronto con spiegazioni precedenti
- Pattern temporali (trend, reversal)
- Arricchimento narrativo con "compared to last week..."

### 5. Signal Analysis (`test_vee_analyzer.py`)
Testa VEEAnalyzer:
- Classificazione segnali (bullish, bearish, neutral)
- Intensità (strong, moderate, weak)
- Confidence scoring
- Pattern detection (divergence, breakout, consolidation)

## Esecuzione

```bash
# Tutti i test VEE
pytest tests/explainability/ -v

# Singola categoria
pytest tests/explainability/test_vee_narrative_levels.py -v

# Con coverage VEE engine
pytest tests/explainability/ --cov=vitruvyan_core.core.vpar.vee

# Solo test unitari (no memoria, no persistence)
pytest tests/explainability/ -m "not integration" -v
```

## Metriche Validate

- **Narrative completeness**: tutti i livelli generati
- **Placeholder coverage**: 100% placeholders sostituiti
- **Template fallback**: graceful degradation se template manca
- **Memory enrichment rate**: >70% quando context disponibile
- **Signal detection accuracy**: >85% per pattern comuni

## Note

- Provider di test in `conftest.py`: `MockExplainabilityProvider`
- VEE non fa chiamate LLM (template-based, deterministic)
- Memory tests richiedono Redis (usare `@pytest.mark.integration`)
- Snapshot testing per regressione narrativa (pytest-snapshot)
