# Vitruvyan Frontier — Odoo Connector Roadmap

> **Last updated**: Mar 15, 2026 14:00 UTC

## Cos'è Vitruvyan Frontier

**Vitruvyan Frontier** è la linea di connettori premium che collega sistemi enterprise (ERP, CRM, ECM) al kernel epistemico Vitruvyan. Ogni connettore è un **plugin di Oculus Prime** — non un servizio separato — che si registra sull'`APIRegistry` esistente tramite auto-discovery via Python entry points.

**Modello commerciale**:
| Tier | Contenuto | Prezzo |
|------|-----------|--------|
| **Core** | Vitruvyan OS + Oculus Prime (7 media agents + GDrive + APIRegistry) | Open / gratuito |
| **Frontier (per connettore)** | `vitruvyan-frontier-odoo`, `vitruvyan-frontier-sap`, etc. | Premium (licenza) |
| **Enterprise Bundle** | Tutti i connettori Frontier + supporto prioritario | Enterprise |

**Website**: Pagina dedicata `/frontier` — spec in `omni-ui/FRONTIER_PAGE_ABSTRACT.md`

---

## Obiettivo

Collegare una sandbox Odoo a Vitruvyan tramite il primo connettore **Vitruvyan Frontier** per dimostrare il sistema come **cognitive layer aziendale**: l'utente fa domande in linguaggio naturale e ottiene risposte narrative con dati ERP reali, passando per l'intero pipeline epistemico (Perception → Memory → Reason → Discourse → Truth).

## Architettura

```
Oculus Prime (servizio unico, porta 9050)           ← ships con Vitruvyan Core (gratuito)
├── Core agents (7 media types + GDrive)
├── APIRegistry ← i connettori Frontier si registrano qui via entry points
└── Evidence Pack pipeline (universale)

vitruvyan-frontier-odoo (pacchetto premium)          ← pip install / vit install
├── fetchers/                                        ← OdooInvoiceFetcher, OdooSaleOrderFetcher, OdooPartnerFetcher
├── domains/enterprise/                              ← intent_config.py, vertical_manifest.yaml (dominio singolo, condiviso da tutti i connettori ERP)
└── pyproject.toml                                   ← entry-points: vitruvyan.oculus_connect
```

**Decisioni architetturali chiave**:
1. **Plugin inside Oculus Prime** — zero container aggiuntivi, stessa pipeline evidence, stesso bus
2. **Dominio "enterprise" unico** — non un dominio per ogni ERP; il fetcher normalizza i dati ERP-specifici, la cognizione è universale
3. **Auto-discovery** — `pip install vitruvyan-frontier-odoo` → Oculus Prime lo scopre automaticamente al boot via entry points

## Prerequisiti

- Stack Vitruvyan attivo (redis, postgres, qdrant, graph, babel, codex, memory, pattern, vault, orthodoxy, conclave, mcp, embedding, oculus_prime)
- Accesso a sandbox Odoo (es. `demo.odoo.com` o istanza self-hosted)
- Credenziali Odoo (database, username, API key)

---

## Fase 0 — Env vars e config

**Dove**: `infrastructure/docker/.env`

```env
# Odoo ERP connection (Vitruvyan Frontier)
ODOO_URL=https://demo.odoo.com
ODOO_DB=demo
ODOO_USER=admin
ODOO_API_KEY=<api_key_or_password>

# Enterprise domain (attivare per intent ERP-specifici)
INTENT_DOMAIN=enterprise
```

**Contratti rispettati**: Nessun secret hardcoded nel codice (Golden Rule).

---

## Fase 1 — Fetcher Odoo (Perception / Oculus Prime)

### 1.0 — Struttura pacchetto Frontier

**Sviluppo iniziale**: dentro `vitruvyan-core` come reference implementation (sotto `infrastructure/edge/oculus_prime/plugins/frontier_odoo/`). Quando validato, viene estratto in un repo separato `vitruvyan-frontier-odoo` per distribuzione premium.

```
infrastructure/edge/oculus_prime/plugins/frontier_odoo/
├── __init__.py
├── fetchers.py          ← OdooInvoiceFetcher, OdooSaleOrderFetcher, OdooPartnerFetcher
├── auth.py              ← OdooAuthenticator (XML-RPC uid caching)
└── pyproject.toml       ← template per il pacchetto standalone

vitruvyan_core/domains/enterprise/
├── __init__.py
├── intent_config.py     ← IntentRegistry "enterprise" (condiviso da tutti i connettori Frontier)
└── vertical_manifest.yaml
```

**`pyproject.toml`** (template per il pacchetto standalone futuro):
```toml
[project]
name = "vitruvyan-frontier-odoo"
version = "0.1.0"
description = "Vitruvyan Frontier connector for Odoo ERP"
requires-python = ">=3.11"

[project.entry-points."vitruvyan.oculus_connect"]
odoo_invoices = "vitruvyan_frontier_odoo.fetchers:OdooInvoiceFetcher"
odoo_orders = "vitruvyan_frontier_odoo.fetchers:OdooSaleOrderFetcher"
odoo_partners = "vitruvyan_frontier_odoo.fetchers:OdooPartnerFetcher"
```

**Auto-discovery in Oculus Prime** (da aggiungere a `APIRegistry`):
```python
from importlib.metadata import entry_points

def discover_frontier_plugins(self):
    """Auto-discover Frontier connectors installed via pip/vit."""
    eps = entry_points(group="vitruvyan.oculus_connect")
    for ep in eps:
        fetcher_cls = ep.load()
        self.register(ep.name, fetcher_cls())
```

**CLI**: `vit install frontier-odoo` → wrappa `pip install vitruvyan-frontier-odoo` + riavvia Oculus Prime.

### 1.1 — Creare i fetcher

**Dove**: `infrastructure/edge/oculus_prime/plugins/frontier_odoo/fetchers.py`

**Contratto**: `AbstractAPIFetcher` da `api_intake.py`

**Modelli Odoo da coprire** (3 fetcher, un file):

| Fetcher class | Odoo model | Dati estratti |
|---|---|---|
| `OdooInvoiceFetcher` | `account.move` | Fatture emesse/ricevute, importi, scadenze, stato pagamento |
| `OdooSaleOrderFetcher` | `sale.order` | Ordini di vendita, righe prodotto, quantità, totali |
| `OdooPartnerFetcher` | `res.partner` | Clienti/fornitori, anagrafica, categorie |

**4 metodi astratti per ciascun fetcher**:

```python
class OdooInvoiceFetcher(AbstractAPIFetcher):

    def get_config(self) -> APIConfig:
        # base_url da ODOO_URL, endpoint="/xmlrpc/2/object"
        # auth_type="basic" (Odoo XML-RPC usa uid+api_key)
        # response_format="json"

    def build_params(self, **kwargs) -> Dict[str, Any]:
        # model="account.move", method="search_read"
        # domain filtri: move_type, date range, payment_state
        # fields: name, partner_id, amount_total, invoice_date,
        #         invoice_date_due, payment_state, invoice_line_ids

    def parse_response(self, response: APIResponse) -> Dict[str, Any]:
        # Estrae records, li normalizza in formato standard
        # Calcola aggregati (totale, count, media)
        # NO semantica — solo dati letterali

    def create_evidence_metadata(self, parsed_data, params) -> Dict[str, Any]:
        # source_type: "erp_record"
        # source_ref JSONB con: source_system="odoo", source_model,
        #   structured_fields (importi, date, stati)
        # technical_metadata: extraction_method="odoo_xmlrpc",
        #   erp_version, fetch_timestamp, record_count
```

**Attenzione**: Odoo usa XML-RPC (non REST puro). Il fetcher wrappa `xmlrpc.client.ServerProxy` dentro il pattern `AbstractAPIFetcher`, delegando l'auth a un modulo `auth.py` con classe `OdooAuthenticator` che restituisce lo `uid` e lo cachea.

### 1.2 — Normalized text (contratto IntakeGuardrails)

Il `normalized_text` dell'Evidence Pack DEVE essere **letterale-descrittivo**, validato da `IntakeGuardrails.validate_no_semantics()`:

```
✅ "Fattura INV/2026/0847 emessa il 2026-01-15 verso Rossi SpA (ID partner: 42).
    Importo totale EUR 12.500,00. Stato pagamento: non pagato.
    Scadenza: 2026-02-28. Righe: 50x Widget Pro a EUR 250,00/unità."

❌ "La fattura di Rossi è in ritardo e potrebbe indicare problemi di liquidità."
   (violazione: "potrebbe indicare" = inferential, "problemi" = evaluative)
```

### 1.3 — Evidence Pack (contratto schema.sql)

```python
source_ref = {
    "source_type": "erp_record",
    "source_system": "odoo",
    "source_model": "account.move",
    "source_id": "INV/2026/0847",
    "source_uri": "odoo://demo.odoo.com/account.move/847",
    "source_hash": "sha256:<hash del record JSON>",
    "mime_type": "application/json",
    "byte_size": 1024,
    "structured_fields": {
        "partner_id": 42,
        "partner_name": "Rossi SpA",
        "amount_total": 12500.00,
        "currency": "EUR",
        "payment_state": "not_paid",
        "invoice_date": "2026-01-15",
        "invoice_date_due": "2026-02-28",
        "line_items": [
            {"product": "Widget Pro", "qty": 50, "unit_price": 250.00}
        ]
    }
}

technical_metadata = {
    "extraction_method": "odoo_xmlrpc",
    "erp_version": "17.0",
    "record_type": "out_invoice",
    "fetch_timestamp": "2026-03-14T10:30:00Z",
    "record_count": 1,
    "chunk_position": 0,
    "language_detected": "it"
}

integrity = {
    "evidence_hash": "sha256:<hash dell'intero evidence pack>",
    "immutable": True,
    "signature": None
}
```

### 1.4 — Registrazione su APIRegistry (auto-discovery)

**Due modalità** (coesistono):

**A) Auto-discovery via entry points** (produzione — pacchetti installati con `pip`/`vit`):
```python
# In APIRegistry.discover_frontier_plugins() — boot di Oculus Prime
from importlib.metadata import entry_points

eps = entry_points(group="vitruvyan.oculus_connect")
for ep in eps:
    fetcher_cls = ep.load()
    registry.register(ep.name, fetcher_cls())
# → registra automaticamente: odoo_invoices, odoo_orders, odoo_partners
```

**B) Registrazione esplicita** (sviluppo locale — plugin nel repo):
```python
# In services/api_edge_oculus_prime/main.py al lifespan
from infrastructure.edge.oculus_prime.plugins.frontier_odoo.fetchers import (
    OdooInvoiceFetcher, OdooSaleOrderFetcher, OdooPartnerFetcher
)

registry.register("odoo_invoices", OdooInvoiceFetcher())
registry.register("odoo_orders", OdooSaleOrderFetcher())
registry.register("odoo_partners", OdooPartnerFetcher())
```

In entrambi i casi, zero nuovi container — i fetcher vivono dentro Oculus Prime.

### 1.5 — Evento StreamBus

Il fetcher NON emette eventi direttamente. Il flusso è:

```
Fetcher.parse_response() → normalized_text + metadata
  → OculusPrimeAdapter persiste Evidence Pack in PostgreSQL
  → OculusPrimeEventEmitter.emit_evidence_created()
  → Channel: "oculus_prime.evidence.created" (v2 canonical)
```

Payload evento (contratto `EvidenceCreatedEvent`):

```python
{
    "event_id": "EVT-<uuid>",
    "evidence_id": "EVD-<uuid>",
    "chunk_id": "CHK-0",
    "source_type": "erp_record",
    "source_uri": "odoo://demo.odoo.com/account.move/847",
    "source_hash": "sha256:...",
    "byte_size": 1024,
    "language_detected": "it",
    "sampling_policy_ref": "SAMPPOL-ERP-DEFAULT-V1"
}
```

### 1.6 — Endpoint API (opzionale, per trigger manuale)

**Dove**: `services/api_edge_oculus_prime/api/routes.py` — nuovo endpoint

```
POST /api/oculus-prime/erp
Body: { "source": "odoo", "model": "account.move", "domain": [...], "limit": 100 }
Response: { "status": "success", "evidence_ids": [...], "records_ingested": 47 }
```

### 1.7 — Ingestione schedulata (opzionale)

**Dove**: `services/api_edge_oculus_prime/streams_listener.py` (attualmente placeholder)

Cron o scheduled task che ogni N ore fa fetch incrementale:
- Filtro: `write_date > last_fetch_timestamp`
- Persiste il timestamp in PostgreSQL per idempotenza
- Usa `idempotency_key` = SHA-256 di `(source_system, source_model, source_id, write_date)` per evitare duplicati

---

## Fase 2 — Pipeline epistemico (zero codice, già cablato)

Una volta che gli Evidence Pack sono sul bus, il pipeline esistente li processa automaticamente:

```
oculus_prime.evidence.created
  ↓
Codex Hunters (listener)
  → Entity discovery: "Rossi SpA" → tipo:cliente
  → Entity binding: Rossi SpA → nodo ontologico (se esiste, lo lega; se nuovo, lo crea)
  → Emette: codex.entity.discovered, codex.entity.bound
  ↓
Babel Gardens (listener)
  → Language detection: "it"
  → Sentiment: neutral (è un dato contabile, non un'opinione)
  → Embedding: vettore 768-dim del normalized_text
  ↓
Memory Orders (listener)
  → Persiste embedding in Qdrant con metadati ontologici
  → Il vettore è arricchito: non solo il testo, ma le relazioni (partner, importo, stato)
  → Abilita RAG: "fatture di Rossi" → semantic search → trova tutti gli evidence pack correlati
  ↓
Pattern Weavers
  → Ontologia semantica: Rossi COMPRA Widget, Rossi HA fattura_scaduta
  → Anomaly detection: quantità fuori media, inattività seguita da ordine grande
  → Trend: variazione importi nel tempo
  ↓
Vault Keepers
  → Archiviazione immutabile degli evidence pack processati
  → Snapshot per audit trail
```

**Nessun codice da scrivere in questa fase.** Il pipeline è event-driven via StreamBus.

---

## Fase 3 — Query in linguaggio naturale (Graph / CAN)

### 3.1 — Intent config enterprise (dominio unico condiviso)

Il dominio **"enterprise"** è **unico per tutti i connettori Frontier** — non esiste un dominio "odoo", "sap", "salesforce". Il fetcher normalizza i dati ERP-specifici; la cognizione opera su entità universali (clienti, fatture, ordini).

**Dove**: `vitruvyan_core/domains/enterprise/intent_config.py`

**Contratto**: `IntentRegistry`, `IntentDefinition`, `ScreeningFilter`

```python
ENTERPRISE_INTENTS = [
    IntentDefinition(
        name="erp_query",
        description="Query ERP data: fatture, ordini, clienti",
        examples=[
            "Quanto abbiamo fatturato questo mese?",
            "Quali clienti hanno fatture scadute?",
            "Mostrami gli ordini aperti",
            "How much did we invoice in Q4?",
        ],
        synonyms=["fatturato", "invoices", "ordini", "orders", "scaduto", "overdue"],
        requires_entities=False,
        route_type="direct",
    ),
    IntentDefinition(
        name="erp_comparison",
        description="Confronto temporale di metriche ERP",
        examples=[
            "Confronta vendite Q3 vs Q4",
            "Come sono andate le vendite rispetto al mese scorso?",
            "Year over year revenue comparison",
        ],
        synonyms=["confronta", "compare", "vs", "trend", "variazione"],
        requires_entities=False,
        route_type="direct",
    ),
    IntentDefinition(
        name="erp_anomaly",
        description="Rilevamento anomalie nei dati ERP",
        examples=[
            "C'è qualcosa di strano negli ordini recenti?",
            "Anomalie nelle fatture di questo mese",
            "Any unusual patterns in recent orders?",
        ],
        synonyms=["anomalia", "strano", "unusual", "anomaly", "outlier"],
        requires_entities=False,
        route_type="direct",
    ),
]

ENTERPRISE_FILTERS = [
    ScreeningFilter(
        name="erp_model",
        description="Tipo di dato ERP",
        value_type="enum",
        enum_values=["invoices", "orders", "partners", "products"],
        keywords=["fatture", "ordini", "clienti", "prodotti", "invoices", "orders"],
    ),
    ScreeningFilter(
        name="time_range",
        description="Periodo temporale",
        value_type="enum",
        enum_values=["today", "this_week", "this_month", "this_quarter", "this_year", "custom"],
        keywords=["oggi", "settimana", "mese", "trimestre", "anno", "today", "week", "month"],
    ),
]

def create_enterprise_registry() -> IntentRegistry:
    registry = IntentRegistry(domain_name="enterprise")
    for intent in ENTERPRISE_INTENTS:
        registry.register_intent(intent)
    for f in ENTERPRISE_FILTERS:
        registry.register_filter(f)
    return registry
```

**Attivazione**: `INTENT_DOMAIN=enterprise` nel `.env`

### 3.2 — Vertical manifest

**Dove**: `vitruvyan_core/domains/enterprise/vertical_manifest.yaml`

```yaml
domain_name: "enterprise"
domain_version: "0.1.0"
status: "draft"

compatibility:
  min_core_version: "1.0.0"
  max_core_version: "1.x.x"
  contracts_major: 1
  update_channel: "stable"
  breaking_changes_allowlist: []
  smoke_tests_timeout: 300

ownership:
  team: "vitruvyan-core"
  tech_lead: "dbaldoni"
  contact: "info@vitruvyan.com"

required_components:
  intent_config: true
  readme: true
  manifest: true

optional_components:
  graph_plugin: false
  graph_nodes: false
  governance_rules: false
  slot_filler: false
  response_formatter: false

adapters:
  langgraph_plugin: false
  sacred_orders_rules: false
  neural_engine_contracts: false

contracts_used:
  - contracts.IIngestionPlugin
```

---

## Fase 4 — Demo script e ingestione iniziale

### 4.1 — Script di ingestione bulk

**Dove**: `scripts/odoo_initial_ingest.py`

```
Flusso:
1. Autenticazione Odoo (XML-RPC)
2. Fetch partners (res.partner) → Evidence Pack per ciascun cliente/fornitore
3. Fetch fatture (account.move) ultimi 12 mesi → Evidence Pack per fattura
4. Fetch ordini (sale.order) ultimi 12 mesi → Evidence Pack per ordine
5. Emissione eventi → pipeline epistemico li processa
6. Report: N partners, N fatture, N ordini ingeriti
```

### 4.2 — Scenari demo (5 domande precaricate)

| # | Domanda | Pipeline path | Output atteso |
|---|---|---|---|
| 1 | "Quanto abbiamo fatturato questo mese?" | Graph → RAG (Memory Orders) → CAN | Importo totale, numero fatture, ticket medio, variazione vs mese precedente |
| 2 | "Quali clienti hanno fatture scadute?" | Graph → RAG → CAN | Lista clienti con importi scaduti, giorni di ritardo, priorità |
| 3 | "Confronta vendite Q4 vs Q3" | Graph → Pattern Weavers + RAG → CAN | Delta %, driver principali, variazione margine |
| 4 | "C'è qualcosa di anomalo negli ordini?" | Graph → Pattern Weavers (anomaly) → CAN | Ordini fuori pattern (quantità, inattività, frequenza) con spiegazione |
| 5 | "Dimmi tutto su Rossi SpA" | Graph → Codex (entity) + RAG → CAN | Grafo relazionale: fatturato, ordini, scaduto, trend, anomalie — tutto narrativo |

---

## Fase 5 — Test e validazione

### 5.1 — Unit test fetcher (LIVELLO 1, nessun I/O)

**Dove**: `infrastructure/edge/oculus_prime/plugins/frontier_odoo/tests/test_fetchers.py`

- Test `build_params()` con diversi filtri
- Test `parse_response()` con mock response Odoo
- Test `create_evidence_metadata()` — verifica struttura source_ref
- Test `validate_no_semantics()` sul normalized_text generato

### 5.2 — Integration test (con sandbox Odoo)

**Dove**: `scripts/test_odoo_integration.py`

- Connessione a sandbox Odoo
- Fetch reale di 10 fatture
- Verifica Evidence Pack in PostgreSQL
- Verifica evento su StreamBus
- Verifica embedding in Qdrant (post-pipeline)

### 5.3 — E2E test (domanda → risposta)

- Ingestione dati Odoo
- Query via graph API: "Quanto abbiamo fatturato?"
- Verifica che la risposta contenga dati reali dalla sandbox

---

## File deliverables (riepilogo)

| Fase | File | Tipo | Note |
|---|---|---|---|
| 0 | `.env` (variabili Odoo + `INTENT_DOMAIN=enterprise`) | Config | 5 min |
| 1.0 | `infrastructure/edge/oculus_prime/plugins/frontier_odoo/__init__.py` | **Nuovo** | Package Frontier |
| 1.0 | `infrastructure/edge/oculus_prime/plugins/frontier_odoo/pyproject.toml` | **Nuovo** | Template pacchetto standalone |
| 1.1 | `infrastructure/edge/oculus_prime/plugins/frontier_odoo/fetchers.py` | **Nuovo** | Core fetcher (3 classi) |
| 1.1 | `infrastructure/edge/oculus_prime/plugins/frontier_odoo/auth.py` | **Nuovo** | OdooAuthenticator |
| 1.6 | `services/api_edge_oculus_prime/api/routes.py` | Edit | Endpoint ERP |
| 3.1 | `vitruvyan_core/domains/enterprise/__init__.py` | **Nuovo** | Dominio enterprise (condiviso) |
| 3.1 | `vitruvyan_core/domains/enterprise/intent_config.py` | **Nuovo** | Intent registry |
| 3.2 | `vitruvyan_core/domains/enterprise/vertical_manifest.yaml` | **Nuovo** | Manifest |
| 4.1 | `scripts/odoo_initial_ingest.py` | **Nuovo** | Script ingestione bulk |
| 5.1 | `infrastructure/edge/oculus_prime/plugins/frontier_odoo/tests/test_fetchers.py` | **Nuovo** | Unit test |

**Codice Vitruvyan core toccato**: 1 edit (routes.py — endpoint opzionale). Tutto il resto è estensione plugin.

---

## Ordine di esecuzione

```
Fase 0 (env vars)               ← 5 min
  ↓
Fase 1.0 (struttura pacchetto)  ← scaffold plugin
  ↓
Fase 1.1-1.5 (fetcher + EP)     ← lavoro principale
  ↓
Fase 4.1 (ingestione bulk)      ← verifica pipeline
  ↓
Fase 2 (pipeline — zero codice) ← verifica automatica
  ↓
Fase 3 (intent config)          ← dominio enterprise condiviso
  ↓
Fase 5 (test)                   ← validazione
  ↓
Fase 4.2 (scenari demo)         ← demo pronta
```

---

## Strategia distribuzione

### Fase sviluppo (ora)
Plugin sviluppato dentro `vitruvyan-core` come reference implementation:
```
infrastructure/edge/oculus_prime/plugins/frontier_odoo/
```
Registrazione esplicita in `main.py` di Oculus Prime.

### Fase produzione (post-validazione)
Estrazione in repo separato `vitruvyan-frontier-odoo`:
```
vitruvyan-frontier-odoo/
├── src/vitruvyan_frontier_odoo/
│   ├── __init__.py
│   ├── fetchers.py
│   └── auth.py
├── tests/
├── pyproject.toml        ← entry-points: vitruvyan.oculus_connect
├── LICENSE               ← licenza premium
└── README.md
```
Installazione: `pip install vitruvyan-frontier-odoo` o `vit install frontier-odoo`
Auto-discovery: Oculus Prime scopre i fetcher via `importlib.metadata.entry_points(group="vitruvyan.oculus_connect")` al boot.

### Connettori futuri (stesso pattern)
| Pacchetto | ERP/CRM | Status |
|-----------|---------|--------|
| `vitruvyan-frontier-odoo` | Odoo | 🔵 In sviluppo |
| `vitruvyan-frontier-sap` | SAP S/4HANA | ⚪ Planned |
| `vitruvyan-frontier-salesforce` | Salesforce | ⚪ Planned |
| `vitruvyan-frontier-sharepoint` | SharePoint / M365 | ⚪ Planned |

Tutti i connettori condividono lo stesso dominio `enterprise` e la stessa pipeline evidence.

---

## Dipendenze esterne

| Dipendenza | Necessaria? | Note |
|---|---|---|
| `xmlrpc.client` | Sì | Stdlib Python — zero pip install |
| Odoo sandbox | Sì | `demo.odoo.com` (gratuito, reset giornaliero) o istanza self-hosted |
| Nuove librerie pip | No | Tutto stdlib + librerie già nel requirements |
