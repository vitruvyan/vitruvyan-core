# 🤖 Test Unitari — Agents

## Cosa sono

Test **unitari** per gli agenti di sistema di Vitruvyan Core.

| File | Agente | Cosa verifica |
|------|--------|---------------|
| `test_llm_agent.py` | LLMAgent (v2.0) | Singleton, RateLimiter, CircuitBreaker, LLMMetrics, metodi complete/complete_json/complete_with_tools/complete_with_messages |

## Principi

1. **Zero chiamate API reali**: ogni chiamata a OpenAI è mockata con `unittest.mock.patch`.
2. **Singleton testato correttamente**: dopo ogni test il singleton viene resettato per evitare contaminazione.
3. **Componenti interni isolati**: RateLimiter, CircuitBreaker, LLMMetrics hanno i loro test unitari separati.
4. **Errori espliciti**: si verifica che `LLMError`, `LLMCircuitOpenError`, `LLMRateLimitError` vengano sollevati correttamente.

## Come eseguire

```bash
# Tutti i test agents
pytest tests/unit/agents/ -v

# Solo con marker
pytest -m agents -v
```

## Nota sulle credenziali

Nessun test usa API key reali. L'`OPENAI_API_KEY` è impostata a un valore fittizio
nel setup dei test. Se OpenAI non è installato, i test vengono saltati con `pytest.skip()`.
