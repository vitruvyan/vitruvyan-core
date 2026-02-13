# 🧠 Test Unitari — LLM

## Cosa sono

Test **unitari** per la cache e il preprocessing dei prompt LLM.

| File | Componente | Cosa verifica |
|------|------------|---------------|
| `test_cache_manager.py` | LLMCacheManager | Hit/miss cache, TTL, generazione chiave SHA-256, invalidation |

## Come eseguire

```bash
pytest tests/unit/llm/ -v
pytest -m llm -v
```

## Note

- La cache LLM è lazy-loaded da LLMAgent — se `enable_cache=False`, la cache non viene mai creata.
- Il test usa un mock store (dict in-memory) per isolare il comportamento della cache da Redis/filesystem.
