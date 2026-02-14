# Layer LLM / AI (LLMAgent)

<p class="kb-subtitle">Gateway canonico per tutte le chiamate LLM: cache, rate limiting, circuit breaker, tool use e metriche — senza incorporare prompt nel core.</p>

## A cosa serve

- Impone un **punto di ingresso unico** per le chiamate LLM: `get_llm_agent()` → `LLMAgent`.
- Fornisce primitive operative di sicurezza:
  - **rate limiting** per evitare throttling del provider
  - **circuit breaker** per degradazione controllata
  - **cache** come layer di ottimizzazione (Redis-backed quando disponibile)
  - **metriche** per latenza/token/cache hit rate
- Supporta più stili di interazione:
  - `complete()` per prompt semplice + system prompt opzionale
  - `complete_with_messages()` per array messaggi completi
  - `complete_with_tools()` per function calling / tool execution

## Contratto core

### “Gateway, non cervello”

- `LLMAgent` è un **gateway**: non possiede logica di business, prompt di dominio o regole di verità.
- I chiamanti (nodi/servizi) possiedono:
  - prompt e schemi
  - validazione (Truth layer) e decisioni di governance
  - cosa persistere o emettere sul bus

### Configurazione (risoluzione modello)

Catena di priorità:

`VITRUVYAN_LLM_MODEL` → `GRAPH_LLM_MODEL` → `OPENAI_MODEL` → `gpt-4o-mini`

Segreto richiesto:

`OPENAI_API_KEY`

Codice: `vitruvyan_core/core/agents/llm_agent.py`

## Uso tipico

```python
from core.agents.llm_agent import get_llm_agent

llm = get_llm_agent()
text = llm.complete(
    prompt="Classifica l’intento per: 'analizza NVDA momentum'",
    system_prompt="Restituisci una label breve.",
    temperature=0.0,
)
```

## Failure modes (comportamento previsto)

- Se il provider throttla: il **rate limiter** blocca preventivamente (stima token).
- Se i fallimenti aumentano: il **circuit breaker** si apre per evitare errori a cascata, poi si resetta dopo il cooldown.
- Se Redis/cache non è disponibile: la cache viene **disabilitata** automaticamente (warning a log), le chiamate proseguono.

## Punti di integrazione

Nell’architettura corrente `LLMAgent` è usato da nodi di orchestrazione e servizi che richiedono:

- classificazione intenti / parsing
- tool routing ed estrazione strutturata
- composizione conversazionale

Vedi: `docs/architecture/MAPPA_ARCHITETTURALE_MODULI.md`

## Riferimenti (approfondimento)

- Gateway LLM: `vitruvyan_core/core/agents/llm_agent.py`
- Contesto conversational layer: `.github/Vitruvyan_Appendix_F_Conversational_Layer.md`

