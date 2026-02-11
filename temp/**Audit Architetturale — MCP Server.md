**Audit Architetturale — MCP Server (`services/api_mcp`) + integrazioni MCP (core)**  
(analysis-only, nessuna modifica al codice)

**1) Domain Leakage Findings**
- `services/api_mcp/schemas/tools.py:9` — Severity: **Critical** — Il contratto pubblico del tool espone tassonomia finance (“momentum/trend/volatility/sentiment/fundamentals”, z-scores) invece di essere vertical-injected/agnostico.
- `services/api_mcp/schemas/tools.py:29` — Severity: **Critical** — Parametro “Investment horizon” nel gateway MCP: assunzione di dominio incorporata nel protocollo tool.
- `services/api_mcp/tools/screen.py:51` — Severity: **Critical** — Il risultato è normalizzato in fattori finance (`momentum_z`, `trend_z`, `volatility_z`, `sentiment_z`, `fundamental_z`).
- `services/api_mcp/tools/screen.py:58` — Severity: **Critical** — Espone `vare.risk_score/risk_category`: il gateway si porta dietro semantica risk/finance.
- `services/api_mcp/tools/vee.py:25` — Severity: **Medium** — Prompt template “analizza {entity_id} momentum…” (domain language) hardcoded nell’executor.
- `services/api_mcp/tools/sentiment.py:25` — Severity: **Critical** — Query diretta su tabella `sentiment_scores` + colonna `combined_score`: tool “query_sentiment” è vertical-specific ma è incluso nel core MCP server.
- `services/api_mcp/tools/sentiment.py:52` — Severity: **High** — Output testuale “Market sentiment favors …”: framing finance/market hardcoded.
- `services/api_mcp/tools/semantic.py:39` — Severity: **Medium** — Output include `sectors` e `risk_profile` come campi “canonici”.
- `vitruvyan_core/core/orchestration/langgraph/node/llm_mcp_node.py:214` — Severity: **Critical** — System prompt: “financial analysis assistant” → leakage di dominio nel nodo MCP di LangGraph.

**2) Abstraction Violations**
- `services/api_mcp/middleware.py:8` — Severity: **Critical** — Usa `redis.Redis` + Pub/Sub direttamente; nessun uso del trasporto `StreamBus` (Streams) come astrazione standard.
- `services/api_mcp/tools/screen.py:35` — Severity: **Medium** — Coupling a endpoint e semantica LangGraph (`POST {LANGGRAPH}/run`) come dipendenza implicita del tool.
- `services/api_mcp/tools/screen.py:41` — Severity: **Medium** — Coupling a shape specifico della risposta (`numerical_panel`) → il tool non è “executor” generico, ma adapter fragile verso un servizio specifico.
- `services/api_mcp/tools/semantic.py:28` — Severity: **Medium** — Coupling a Pattern Weavers HTTP (`POST /weave`) invece di interazione via bus/contract.
- `services/api_mcp/middleware.py:103` — Severity: **Medium** — Archiviazione via SQL diretto (schema/table hardcoded) invece di “Vault Keepers” come boundary esplicito.
- `services/api_mcp/requirements.txt:14` — Severity: **Low** — `sentence-transformers` incluso nelle deps del gateway MCP, creando lock-in/inerzia verso embedding provider pur non essendo usato dai tool attuali.
- `infrastructure/docker/dockerfiles/Dockerfile.api_mcp:17` — Severity: **Critical** — Dockerfile copia solo `vitruvyan_core/core/foundation/persistence` ma il servizio importa `PostgresAgent` (es. `services/api_mcp/middleware.py:12`): build “minimal copy” strutturalmente incoerente (rischio import error a runtime).

**3) Boundary Violations (Epistemic + Micelial)**
- `services/api_mcp/middleware.py:59` — Severity: **Critical** — Pubblica su `conclave.mcp.request`, ma:
  - Orthodoxy Wardens dichiara consumo da `conclave.mcp.actions` (`vitruvyan_core/core/governance/orthodoxy_wardens/events/orthodoxy_events.py:73`).
  - MCP Listener in core ascolta `conclave.mcp.actions` (`vitruvyan_core/core/synaptic_conclave/listeners/mcp.py:87`).  
  Risultato: integrazione Conclave/Orthodoxy *di fatto disallineata* (eventi MCP non arrivano ai consumer previsti).
- `docs/services/mcp.md:43` — Severity: **Critical** — La doc canonica parla di `cognitive_bus:mcp_request`, ma l’implementazione usa `conclave.mcp.request` (`services/api_mcp/middleware.py:59`): drift di canale.
- `services/api_mcp/middleware.py:67` — Severity: **Critical** — Il middleware dichiara stati “blessed/purified/heretical”, ma implementa solo transizioni verso `purified` (mai `heretical`) → non esiste blocking reale.
- `services/api_mcp/api/routes.py:81` — Severity: **High** — Il path 422 “heretical” scatta su `ValueError`, ma il middleware non genera “heretical” (quindi enforcement Orthodoxy è nominale, non effettivo).
- `services/api_mcp/middleware.py:100` — Severity: **Medium** — Il gateway scrive audit trail direttamente in Postgres (“Vault Keepers archiving”), invece di richiedere archiviazione al relativo Ordine (boundary sfocato).
- `services/api_mcp/tools/screen.py:32` — Severity: **Medium** — Executor fa chiamate cross-service HTTP dirette; se la regola interna è “inter-order via Redis Streams”, qui è bypassata.
- `vitruvyan_core/core/synaptic_conclave/listeners/mcp.py:271` — Severity: **Critical** — Listener MCP in core usa Redis Pub/Sub (`pubsub.subscribe`) invece di Streams (micelial integration non completata).

**4) Configuration Audit**
- `services/api_mcp/main.py:11` — Severity: **Medium** — Logging level hardcoded DEBUG; non usa `config.service.log_level` (`services/api_mcp/config.py:12`).
- `services/api_mcp/middleware.py:74` — Severity: **Medium** — Soglie Orthodoxy hardcoded (z-score ±3).
- `services/api_mcp/middleware.py:80` — Severity: **Medium** — Soglie composite hardcoded (±5).
- `services/api_mcp/middleware.py:87` — Severity: **Low** — Range word_count hardcoded (100–200).
- `services/api_mcp/config.py:16` — Severity: **Medium** — Config centralizza endpoint/redis ma non include Postgres; eppure il servizio richiede Postgres per audit (`services/api_mcp/middleware.py:100`).
- `vitruvyan_core/core/orchestration/langgraph/node/llm_mcp_node.py:50` — Severity: **Medium** — Default `MCP_SERVER_URL` punta a `:8021`, mentre il servizio espone `8020` (`services/api_mcp/config.py:11`) → rischio integrazione fragile se env non settata.
- `vitruvyan_core/core/orchestration/langgraph/node/llm_mcp_node.py:260` — Severity: **Critical** — Lettura `orthodoxy_status` dal posto sbagliato (`result.data.*`); nello schema MCP è top-level (`services/api_mcp/schemas/models.py:19`) e viene popolato in risposta (`services/api_mcp/api/routes.py:76`).
- `docs/services/mcp.md:66` — Severity: **Low** — Doc indica `services/mcp/main.py` per `TOOL_SCHEMAS`, ma l’implementazione reale è `services/api_mcp/schemas/tools.py` (doc drift).
- `services/api_mcp/README.md:91` — Severity: **Low** — README elenca endpoint `POST /tools/list` e `POST /tools/execute`, ma il server espone `GET /tools` e `POST /execute` (`services/api_mcp/api/routes.py:43`).
- `services/api_mcp/README.md:72` — Severity: **Medium** — README cita migration `001_mcp_tool_calls.sql`, ma nel repo non risulta presente (deployment prerequisite non tracciato come artefatto).

**5) Legacy Residue Analysis**
- `.github/Vitruvyan_Appendix_K_MCP_Integration.md:56` — Finanza come dominio implicito nei tool (screen + z-score) è parte dell’eredità; gli stessi costrutti sono ancora nel contratto/tooling attuale (`services/api_mcp/schemas/tools.py:9`).
- `.github/MCP_SACRED_ORDERS_INTEGRATION.md:161` — Legacy/plan usa `cognitive_bus:mcp_request`, ma l’implementazione corrente non pubblica su quel canale (`services/api_mcp/middleware.py:59`) → residuo di naming non chiuso.
- `services/api_mcp/README.md:109` — Persistono naming “ticker” (`screen_ticker`) incoerenti col refactor verso “entity” → rename incompleto/ibrido.
- `.github/Vitruvyan_Appendix_K_MCP_Integration.md:260` — Severity: **Critical (Security)** — Credenziale in chiaro (POSTGRES_PASSWORD) in appendix.
- `infrastructure/docker/archive/docker-compose.omni.yml.OBSOLETE_DEC29:139` — Severity: **Critical (Security)** — Credenziale in chiaro anche in compose archiviato.

**6) Agnosticization Score (0–100)**
- **Score: 16 / 100**
  - Domain Purity: **2/20** (contratto tool + executors espongono tassonomia finance: `services/api_mcp/schemas/tools.py:9`)
  - Abstraction Purity: **5/20** (coupling a LangGraph/Pattern Weavers + raw Redis + packaging incoerente: `infrastructure/docker/dockerfiles/Dockerfile.api_mcp:17`)
  - Epistemic Boundary: **3/20** (Orthodoxy/Vault “simulate” nel middleware e non come ordini separati: `services/api_mcp/middleware.py:67`)
  - Config Injection: **3/20** (soglie hardcoded + mismatch schema/port: `vitruvyan_core/core/orchestration/langgraph/node/llm_mcp_node.py:260`)
  - Micelial Integration: **3/20** (Pub/Sub e canali disallineati rispetto a Streams e consumer: `services/api_mcp/middleware.py:59`)
- 3 miglioramenti prioritari (correttivi, non redesign):
  1. Allineare canali/eventing MCP a `conclave.mcp.actions` e adottare Streams/`StreamBus` end-to-end (oggi `conclave.mcp.request` è “orfano”).
  2. Correggere i contratti di integrazione MCP↔LangGraph (porta default + parsing `orthodoxy_status` top-level) per evitare failure silenziose.
  3. Spostare/isolarel il catalogo tool finance (momentum/z-score/VARE/sentiment_scores) fuori dal “default MCP server” o renderlo veramente vertical-injected come dichiarato in doc (`docs/services/mcp.md:17`).

Se vuoi, nel prossimo passaggio posso produrre una checklist di “refactor done/remaining” specifica (Streams + canali + schema risposta + dockerfile) da usare come gate di release, senza toccare il codice.