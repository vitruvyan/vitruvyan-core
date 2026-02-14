🔥 EXECUTIVE PROMPT — VITRUVYAN CORE PURIFICATION P0
Missione

Stiamo trasformando Vitruvyan in un Cognitive Orchestration Substrate domain-agnostic.
Il core deve essere completamente indipendente dal dominio finance.

Obiettivo: completare i 9 task P0 del Piano Remediation Prioritizzato e portare la conformance:

Domain-agnostic ≥ 95%

Security ≥ 95%

No hardcoded = 100%

Governance pluggable

Questo è un intervento chirurgico strutturale, non cosmetico.

📌 CONSTRAINTS ARCHITETTURALI NON NEGOZIABILI

Il core non conosce il dominio.

Niente ticker

Niente stock

Niente market

Niente buy|sell|invest

Niente riferimenti a modelli finance-specific

Il core espone solo concetti generici:

entity_id

entity_ids

domain

context

ruleset

analysis_output

Ogni dominio deve essere plug-in, mai hardcoded nel core.

LIVELLO 1 = Pure Domain Layer

Zero I/O

Zero subprocess

Zero Docker access

Zero Redis direct

Zero filesystem hardcoded

Security by default.

Nessun shell=True

Nessun CORS wildcard con credentials

Nessun endpoint hardcoded

🎯 TASK P0 — IMPLEMENTAZIONE OBBLIGATORIA
1️⃣ Event Schema Purification

File: event_schema.py

Azione:

Sostituire ogni:

ticker

tickers
con:

entity_id

entity_ids

Rimuovere fusion_method = "gemma_finbert"
→ sostituire con "default" o config-driven.

Aggiornare validation logic:

payload.get('ticker') → payload.get('entity_id')

Parametrizzare sources=["yfinance","reddit","google_news"]
→ caricare da config/env/domain plugin.

Non introdurre alias temporanei.
Il core non deve più conoscere la parola ticker.

2️⃣ Pipeline Parsing Cleanup
parse_node.py

Rimuovere completamente:

"portafoglio" in txt

params_extraction_node.py

Rimuovere pattern:

titoli|acciones|etfs


Sostituire con:

pattern neutri

oppure pattern caricati da domain registry

Il core non contiene lessico finance.

3️⃣ GovernanceRuleRegistry (CRITICO)

Creare:

core/governance/orthodoxy_wardens/governance/rule_registry.py

Obiettivo:

Rendere le compliance rules completamente pluggabili.

Architettura richiesta:
class GovernanceRuleRegistry:

    def register_domain(self, domain: str):
        """
        Load domain-specific rules from:
        domains/<domain>/governance_rules.py
        """
    
    def get_rules(self) -> List[Rule]:
        ...

Refactor necessario:

Spostare tutte le regex finance-specific fuori da rule.py

rule.py diventa generico

Regole finance vengono caricate solo se domain="finance"

Il core non deve più contenere:

buy

sell

invest

stock

market

portfolio

4️⃣ Inquisitor Prompt Purification

File: inquisitor_agent.py

Rimuovere:

"Analyze the following financial analysis output..."


Sostituire con:

"Analyze the following domain-specific analysis output..."


Oppure caricare il prompt da:

domain plugin

oppure config-driven template

5️⃣ Security Hardening (NON NEGOZIABILE)
Rimuovere shell=True

File: penitent_agent.py

Eliminare completamente uso pipe in subprocess.
Se richiede privilegi root → rimuovere feature.

Fix CORS

In tutti i servizi:

Sostituire:

allow_origins=["*"]


Con:

ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")


Non lasciare wildcard con credentials attive.

6️⃣ Config Hardening

Sostituire tutti i seguenti:

localhost

URL embedding API

Redis default

log paths /app/logs/*

Con:

os.getenv("VAR_NAME", "default")


Il core non deve mai assumere ambiente locale.

7️⃣ Wire EntityResolverRegistry

In graph_flow.py:

Caricare ENTITY_DOMAIN

Registrare registry

Configurare entity_resolver_node

Nessun registry deve esistere senza wiring.

8️⃣ Boundary Enforcement LIVELLO 1

Audit su penitent_agent.py:

Rimuovere I/O diretto

Spostare subprocess/docker/redis in adapter LIVELLO 2

Se non critico → archiviare in _legacy/

LIVELLO 1 deve diventare matematicamente puro.

9️⃣ Zero Finance in Core Verification

Al termine:

Eseguire search globale su:

ticker
stock
market
invest
buy
sell
portfolio
finbert
yfinance


Se uno di questi compare in core/ → FAIL.

📊 OUTPUT RICHIESTO

Al termine dell’implementazione, fornire:

Lista file modificati

Diff summary

Conferma:

0 occorrenze finance in core

Governance completamente pluggabile

Nessun shell=True

Nessun CORS wildcard

Tutti endpoint configurabili via env

Nuovo punteggio conformance stimato

⚠️ NON FARE

Non introdurre workaround temporanei

Non mantenere alias tipo ticker/entity_id

Non lasciare commenti TODO

Non spostare finance in altro punto del core

Finance deve vivere solo in:

domains/finance/

🎯 OBIETTIVO FINALE

Portare Vitruvyan da:

Opinionated finance-biased orchestration framework

a:

Domain-agnostic cognitive orchestration substrate con governance pluggabile.

Quando questi 9 punti sono completati, possiamo difendere seriamente il termine:

Cognitive OS Runtime Layer