# 🗣️ Conversational Capabilities Tests

Test suite per validare le capacità discorsive del sistema Vitruvyan.

## Obiettivo

Verificare che il CAN (Conversational Analysis Node) generi:
- **Narrative coerenti** con il contesto utente
- **Follow-up pertinenti** basati su intent e semantic matches
- **Risposte empatiche** allineate con l'emozione rilevata
- **Routing appropriato** (chat, sector, ticker analysis)

## Categorie Test

### 1. Context Integration (`test_can_context_integration.py`)
Verifica l'integrazione di context da:
- **VSGS semantic matches** (top-3 context injection)
- **Pattern Weavers ontology** (concetti estratti)
- **Babel Gardens emotion** (tono emotivo)
- **Intent detection** (routing decisionale)

### 2. Follow-Up Generation (`test_can_followup_quality.py`)
Valuta la qualità dei follow-up:
- Pertinenza con la query originale
- Diversità tra i 3 follow-up suggeriti
- Allineamento con il conversation_type
- Non-ripetizione di domande già implicite

### 3. Empathetic Response (`test_can_empathy.py`)
Testa il tono emotivo delle risposte:
- Frustrazione → mollifying tone
- Curiosità → explorative guidance
- Neutrale → informative clarity
- Urgenza → concise + actionable

### 4. Routing Logic (`test_can_routing.py`)
Verifica correttezza del routing:
- `chat` → conversational dialogue
- `sector` → domain-specific analysis
- `ticker` → entity-focused narrative
- Fallback → semantic search

## Esecuzione

```bash
# Tutti i test conversational
pytest tests/conversational/ -v

# Singola categoria
pytest tests/conversational/test_can_context_integration.py -v

# Con coverage
pytest tests/conversational/ --cov=vitruvyan_core.core.orchestration.langgraph.node.can_node

# Solo test rapidi (no LLM calls reali)
pytest tests/conversational/ -m "not slow" -v
```

## Metriche Validate

- **Narrative length**: 200-2000 chars (user-friendly)
- **Follow-up count**: esattamente 3 suggestions
- **Context usage**: flag `vsgs_context_used` populated
- **Emotional alignment**: tone matches detected emotion (qualitative)
- **Routing accuracy**: >90% consistency with intent

## Note

- Test usano **mock LLM responses** (no OpenAI API calls reali)
- Fixture in `conftest.py`: `mock_llm_agent`, `sample_state`
- Snapshot testing per regressione narrativa (future)
