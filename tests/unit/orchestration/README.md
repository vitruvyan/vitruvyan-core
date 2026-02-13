# 🎯 Test Unitari — Orchestration

## Cosa sono

Test **unitari** per i componenti di orchestrazione del sistema cognitivo.

| File | Componente | Cosa verifica |
|------|------------|---------------|
| `test_intent_registry.py` | IntentRegistry | Registrazione intent, normalizzazione sinonimi, costruzione prompt GPT, parsing risposta classificazione |
| `test_prompt_registry.py` | PromptRegistry | Registrazione domini, template identity/scenario, sostituzioni variabili, traduzioni, clear() per test |

## Principi

1. **Pura configurazione**: entrambi i componenti sono oggetti puri (zero I/O, zero LLM, zero rete).
2. **Deterministici**: i test usano registrazioni controllate → output prevedibile.
3. **Isolamento**: PromptRegistry usa `clear()` nel setup per evitare contaminazione da stato globale (è un singleton di classe).

## Come eseguire

```bash
pytest tests/unit/orchestration/ -v
pytest -m orchestration -v
```

## Note per sviluppatori

- **IntentRegistry** registra automaticamente gli intent "soft" e "unknown" nel costruttore. Non serve registrarli manualmente.
- **PromptRegistry** è un singleton con classmethods — stato condiviso tra tutti gli usi. Il metodo `clear()` è fornito esplicitamente per il testing.
- Per aggiungere un dominio: creare `domains/<domain>/intent_config.py` con `create_<domain>_registry()`.
