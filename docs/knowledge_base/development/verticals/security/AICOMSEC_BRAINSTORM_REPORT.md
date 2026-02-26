# AICOMSEC — Brainstorming & Architecture Report

> **Last updated**: Feb 26, 2026 12:00 UTC
> **Status**: Draft — in fase di brainstorming pre-Sprint 1
> **Autore**: Vitruvyan AI + Team AICOMSEC
> **Branch**: `feature/aicomsec-domain`

---

## Indice

1. [Cos'è AICOMSEC](#1-cosè-aicomsec)
2. [Tre Modalità Operative](#2-tre-modalità-operative)
3. [Pipeline di Ingestione](#3-pipeline-di-ingestione)
4. [Superfici UX](#4-superfici-ux)
5. [Integrazione DSE — Design Space Exploration](#5-integrazione-dse)
6. [Integrazione VPAR — Algoritmi Proprietari](#6-integrazione-vpar)
7. [Funzionalità Avanzate (7 proposte)](#7-funzionalità-avanzate)
8. [Architettura Complessiva](#8-architettura-complessiva)
9. [Sprint Plan](#9-sprint-plan)
10. [Domande Aperte](#10-domande-aperte)

---

## 1. Cos'è AICOMSEC

AICOMSEC è il **vertical di sicurezza fisica e cyber** costruito sopra il framework Vitruvyan OS. Non è un SIEM, non è un semplice RAG, non è un motore di compliance statico.

È un **sistema epistemico di sicurezza** che:
- Ingesta documenti tecnici (planimetrie, policy, audit, certificazioni)
- Acquisisce flussi normativi (NIS2, ISO 27001, GDPR, ACN, EUR-Lex)
- Integra intelligence trasversale (CVE/NVD, threat feeds)
- Produce analisi strutturate, piani di gap analysis, report di compliance
- Ottimizza la strategia di mitigazione tramite motori di ottimizzazione multi-obiettivo

**Il problema che risolve**: la conoscenza di sicurezza è frammentata — il consulente che va in sito porta esperienza personale non strutturata, il cliente ha documentazione dispersa, la normativa cambia continuamente. AICOMSEC costruisce la **memoria epistemica del sito** e la mantiene aggiornata nel tempo.

### Cosa NON è AICOMSEC

| NON è | Perché |
|-------|--------|
| Un sistema di controllo accessi | Non gestisce operazioni real-time sui dispositivi |
| Un SIEM | Non processa log in streaming per detection |
| Un sistema di sorveglianza | Non elabora feed video live |
| Un tool di pentesting | Nessun output offensivo (invariante `security.offensive.*`) |
| Un sostituito del consulente | Amplifica il consulente, non lo rimpiazza |

---

## 2. Tre Modalità Operative

### H2M — Human to Machine (Conversazionale)
Il consulente o l'operatore interagisce via chat con la knowledge base del sito. Esempi:
- *"Quali zone del piano B non hanno copertura CCTV entro 3 metri da un punto di accesso?"*
- *"Mostrami le non conformità NIS2 ancora aperte per il cliente XYZ"*
- *"Genera un report tecnico per l'audit ISO 27001 del 15 marzo"*

**LangGraph node**: `cached_llm_node` con RAG su `aicomsec.{tenant_id}.chunks`

### M2M — Machine to Machine (API Strutturata)
Integrazione con sistemi terzi: ERP, BMS (Building Management System), CMMS (manutenzione). Output strutturato JSON, nessun testo narrativo a meno che non richiesto.

**Endpoint**: `POST /v1/assess/risk`, `POST /v1/compliance/gap`, `GET /v1/site/{site_id}/status`

### Document Generation (Output Epistemico)
Generazione automatica di documentazione formale: piano di trattamento del rischio, DPIA, relazione tecnica per certificazione, evidence package per audit NIS2.

**LangGraph node**: `compose_node` + VEE `SecurityExplainabilityProvider`

---

## 3. Pipeline di Ingestione

La pipeline è a **due canali convergenti** che alimentano la stessa knowledge base multi-tenant.

### Canale A — Documenti Cliente

```
Cliente (GDrive / SharePoint / Upload)
    │
    ▼
Oculus Prime (api_edge_oculus_prime, port 8050)
    │  Pre-epistemic intake: NO NER, NO embedding, NO semantica
    │  Agents: Document (PDF/DOCX), Image (OCR), CAD/BIM, Audio (Whisper)
    │
    ▼  Redis Stream: oculus_prime.evidence.created
    │
    ▼
Babel Gardens AICOMSEC Consumer
    │  Filtra: domain_family=security
    │  Classifica: physical | cyber | normative | operational
    │  Sanitizza PII (gate pre-embedding)
    │  Embedding con fusione SecBERT (0.35) + LLM (0.50) + multilingual (0.15)
    │
    ▼
Qdrant: aicomsec.{tenant_id}.chunks
```

### Canale B — Flussi Normativi (Automatico)

```
Sorgenti pubbliche:
    ├── EUR-Lex REST API  (attivo, JSON nativo)
    ├── ACN (Agenzia Cyber Nazionale)  (scraping programmato)
    ├── CVE/NVD NIST API  (patch notes, severity scores)
    └── ENISA Publications Feed

    ▼  Crawler schedulato (cron / Codex Hunters)
    ▼
Normalizzazione + versioning temporale
    │  Ogni normativa ha: valid_from, valid_to, superseded_by
    │

    ▼
Qdrant: aicomsec.normative.{framework}
    │  (collection separata — condivisa tra tenant, read-only per tenant)
```

### 5 Stadi della Pipeline

| Stadio | Input | Output | Ordine Sacred |
|--------|-------|--------|---------------|
| **Intake** | Raw file / API response | Evidence envelope | Perception (Oculus Prime) |
| **Classification** | Evidence envelope | Tipo + metadata | Perception (Babel Gardens) |
| **Chunking** | Testo classificato | Chunk con overlap | Perception (Babel Gardens) |
| **Embedding** | Chunk | Vettore 768-dim | Memory Orders |
| **Retrieval** | Query vettore | Top-k chunk rilev. | Memory Orders + VSGS |

---

## 4. Superfici UX

### Superficie 1 — Chat Epistémico
Interfaccia conversazionale per consulenti / operatori sicurezza. Accesso alla KB del sito tramite linguaggio naturale. Il sistema cita sempre la fonte (invariante `security.trace.*`).

**Stack**: LangGraph → `document_query` / `normative_lookup` intent → RAG → VEE summary → risposta con citazione

### Superficie 2 — Dashboard Compliance
Vista strutturata per compliance officer. Mostra:
- Punteggio complessivo per framework (NIS2, ISO27001, GDPR)
- Trend nel tempo (Compliance Entropy — vedi §7)
- Non conformità aperte, scadenze, responsabili
- Heatmap rischio per zona / sistema

**Stack**: M2M API → VARE risk profiling → dati aggregati → rendering frontend

### Superficie 3 — API M2M
Per integrazioni sistemi terzi. Documentata con OpenAPI. Output JSON deterministico. Autenticazione JWT con scope per tenant.

**Endpoints chiave**:
```
POST /v1/site/{site_id}/risk-assessment
POST /v1/compliance/gap-analysis
GET  /v1/compliance/{framework}/status
POST /v1/report/generate
GET  /v1/normative/horizon-scan
```

---

## 5. Integrazione DSE

**DSE** = Design Space Exploration (`infrastructure/edge/dse/`, port 8021). Motore di ottimizzazione multi-obiettivo Pareto, aggiunto in v1.6.1.

### Perché DSE in AICOMSEC?

La gap analysis individua i problemi. DSE risponde a: **"Quale azione intraprendere per prima, dato il budget, il tempo e la tolleranza al rischio?"**

### Flusso di Integrazione

```
VARE SecurityRiskProvider
    → RiskResult (dimension_scores per sito)
        ↓
Gap Analysis (Pattern Weavers security)
    → Lista non conformità con severity, cost_to_fix, deadline
        ↓
DSE Parameter Space
    ├── decision_vars: [action_1, action_2, ..., action_n]  (binarie: fai/non fare)
    ├── objectives:
    │       minimize: residual_risk_after_action
    │       minimize: implementation_cost
    │       minimize: time_to_compliance
    └── constraints:
            budget_total ≤ budget_cliente
            deadline_nis2 ≤ 2025-10-17
        ↓
Pareto Frontier
    → Insieme di piani ottimali non dominati
        ↓
Doctrine Ranking (configurable per cliente)
    ├── critical_infra: peso maggiore su residual_risk
    ├── budget_constrained: peso maggiore su cost
    └── deadline_driven: peso maggiore su time
        ↓
Piano di Mitigazione Ottimale con spiegazione VWRE
    "L'azione prioritaria è X perché riduce il cyber_risk del 42%
     a costo contenuto (€8.000) entro la scadenza NIS2."
```

### Dottrine per Tipo Cliente

| Dottrina | Peso Risk | Peso Cost | Peso Time | Caso d'uso |
|----------|-----------|-----------|-----------|------------|
| `critical_infra` | 0.60 | 0.15 | 0.25 | Infrastruttura critica, PA |
| `nis2_compliance` | 0.30 | 0.20 | 0.50 | Scadenza NIS2 imminente |
| `iso27001_compliance` | 0.40 | 0.25 | 0.35 | Certificazione ISO |
| `budget_constrained` | 0.25 | 0.60 | 0.15 | PMI con budget limitato |

---

## 6. Integrazione VPAR

VPAR = Vitruvyan Proprietary Algorithms Repository (`vitruvyan_core/core/vpar/`). Tutti i motori sono LIVELLO 1 — pura computazione, zero I/O, iniettati via contract.

### Mappa Contratti → Provider Security

Il pattern è identico a quello Finance (reference implementation in `vitruvyan_core/domains/finance/vpar/`):

```
domains/risk_contract.py           → SecurityRiskProvider   → VARE engine
domains/aggregation_contract.py    → SecurityAggregationProvider → VWRE engine
domains/explainability_contract.py → SecurityExplainabilityProvider → VEE engine
```

Directory da creare: `vitruvyan_core/domains/security/vpar/`

### SecurityRiskProvider → VARE

**Dimensioni di rischio per sito/sistema:**

| Dimensione | Descrizione |
|------------|-------------|
| `cyber_risk` | f(CVE count, patch_age, exposure_level) |
| `compliance_risk` | f(gap_count, deadline_distance, severity_distribution) |
| `physical_risk` | f(cctv_coverage_pct, access_control_score, perimeter_gaps) |
| `incident_risk` | f(incident_frequency_12m, mean_severity, mean_recovery_time) |
| `normative_risk` | f(regulatory_update_age, unmet_obligation_count) |

**Profili disponibili:**

| Profilo | Uso | Peso dominante |
|---------|-----|---------------|
| `critical_infrastructure` | PA, utilities, ospedali | `cyber_risk` 0.35 |
| `standard_facility` | Uffici, retail | bilanciato |
| `nis2_compliance` | Focus scadenza NIS2 | `compliance_risk` 0.40 |
| `iso27001_compliance` | Percorso certificazione | `compliance_risk` 0.40 |

### SecurityAggregationProvider → VWRE

Risponde a: *"Perché il sito ha score 78? Quale fattore pesa di più?"*

Fattori: `cve_critical`, `patch_lag`, `access_control`, `cctv_coverage`, `normative_gaps`, `incident_history`, `policy_completeness`

Output: *"Il sito Via Roma 15 ha score 78 principalmente a causa di CVE critici non patchati (contributo +0.42, 38% del totale)."*

### SecurityExplainabilityProvider → VEE

Genera narrative con 3 livelli rispettando `governance_rules.py`:

| Livello | Audience | Invariante |
|---------|----------|------------|
| Summary | Manager / executive | Nessun claim assoluto (rule `security.safety.*`) |
| Technical | Analista sicurezza | CVE citati esplicitamente (rule `security.trace.*`) |
| Detailed | Auditor / certificatore | Norma + articolo citati (rule `security.norm.*`) |

### VSGS — Semantic Grounding System

VSGS è già funzionante — nessuna customizzazione richiesta. Si attiva con:
```bash
VSGS_ENABLED=1
VSGS_COLLECTION=aicomsec.{tenant_id}.semantic_states
```
Cerca contesto semantico nello storico conversazioni prima di ogni risposta LLM.

---

## 7. Funzionalità Avanzate

Le seguenti 7 funzionalità sono state identificate in sessione di brainstorming come possibili sviluppi post-MVP, ordinate per priorità suggerita.

### P1 — Evidence Chain Constructor 🚀

**Problema**: preparare la documentazione per un audit NIS2 richiede 2-3 settimane per raccogliere prove da sistemi disparati.

**Soluzione**: AICOMSEC costruisce automaticamente il **pacchetto di prove** per ogni requisito normativo:
- Hash del documento (immodificabilità)
- Catena: requisito normativo → controllo tecnico → evidenza documentale → data di verifica
- Export PDF firmato pronto per auditor

**Impatto stimato**: da 3 settimane a 2 ore per preparazione audit NIS2.

**Integration point**: Vault Keepers (archivio) + Orthodoxy Wardens (validazione) + VEE (narrative)

---

### P2 — Compliance Entropy Monitor

**Problema**: la compliance non è uno stato binario ma una traiettoria. Senza monitoraggio, i clienti si trovano "sorprendentemente" fuori compliance.

**Soluzione**: tracking giornaliero del punteggio di compliance per framework. Il sistema:
- Riconosce la traiettoria di degradazione
- Predice *"a questo ritmo, sarete sotto soglia critica in 47 giorni"*
- Lancia alert proattivi prima della scadenza

**Metrica chiave**: `compliance_entropy_rate` = variazione punteggio / tempo

**Integration point**: Pattern Weavers (analisi trend) + VARE compliance_risk dimension

---

### P3 — Regulatory Horizon Scanner

**Problema**: le normative cambiano, ma i clienti lo scoprono spesso troppo tardi.

**Soluzione**: monitoraggio continuo dei processi normativi europei e nazionali:
- Trilogues EU (stati di avanzamento iter legislativo)
- Consultazioni pubbliche ENISA
- Cicli di revisione NIST
- Bozze ACN ancora non ufficiali

**Output**: alert 12-18 mesi prima dell'entrata in vigore + piano di adattamento preventivo via DSE.

**Integration point**: Canale B pipeline (crawler) + DSE (piano preventivo) + Ortodoxi Wardens (validazione normativa)

---

### P4 — Semantic Spatial Layer

**Problema**: le planimetrie CAD/BIM sono file statici. Non è possibile fare query semantiche su di esse: *"mostrami le zone senza copertura CCTV entro 3m da un punto di accesso"*.

**Soluzione**: conversione CAD/BIM → grafo spaziale (NetworkX / Neo4j-compatibile):
- Nodi: stanze, zone, punti di accesso, dispositivi di sicurezza
- Archi: distanze, connettività, visibilità
- Proprietà: tipo dispositivo, stato, ultima manutenzione

**Query esempio**:
```python
spatial_graph.query(
    "zones WHERE distance_to('access_point') < 3.0 AND cctv_coverage == False"
)
```

**Integration point**: Oculus Prime CAD/BIM agent (già esistente) + nuova pipeline graph → Qdrant payload enrichment

---

### P5 — Adversarial Reasoning Engine (Difensivo)

**Problema**: i consulenti pensano come difensori. Un attaccante ragiona diversamente.

**Soluzione**: motore di ragionamento adversariale **puramente difensivo** che:
- Usa la KB del sito per identificare scenari di attacco plausibili
- Per ogni scenario: probabilità, impatto, controllo mitigante assente
- Output: lista di "punti deboli sistemici" non ovvi

**Invariante assoluta**: `governance_rules.py` rule `security.offensive.*` — nessuna istruzione operativa per attacchi, solo identificazione e mitigazione difensiva.

**Integration point**: VARE (risk scoring degli scenari) + Pattern Weavers (analisi pattern) + LLM reasoning

---

### P6 — Federated Anonymous Intelligence

**Problema**: ogni cliente AICOMSEC lavora in un silo. L'intelligenza acquisita su un sito non beneficia gli altri.

**Soluzione**: contribuzione anonima di **pattern** (non dati) a uno spazio neutrale condiviso:
- Cosa contribuisce: statistiche aggregate anonimizzate (es. "il 60% degli impianti nel settore X ha gap su controllo accessi tipo Y")
- Cosa non contribuisce mai: dati del sito, tenant_id, documenti
- Meccanismo: differential privacy prima della contribuzione

**Valore**: più clienti = sistema più intelligente per tutti. Network effect.

**Integration point**: Vault Keepers (archivio federato) + infrastructure/edge/dse (aggregazione anonima)

---

### P7 — Incident Reconstruction Engine

**Problema**: dopo un incidente, ricostruire la timeline richiede settimane di analisi manuale di log eterogenei.

**Soluzione**: correlazione automatica multi-sorgente:
- Badge log (accessi fisici)
- Metadata CCTV (timestamps, zone, anomalie di movimento)
- Log sistema allarme
- Ticket manutenzione
- Syslog / audit trail IT

**Output**: timeline unificata dell'incidente con probabilità di causalità, aree di incertezza indicate.

**Note**: nessun accesso ai video CCTV — solo metadata (invariante privacy).

---

### Tabella Priorità

| # | Funzionalità | Impatto | Complessità | Priorità |
|---|-------------|---------|-------------|----------|
| 1 | Evidence Chain Constructor | ⭐⭐⭐⭐⭐ | Media | **P0** |
| 2 | Compliance Entropy Monitor | ⭐⭐⭐⭐ | Bassa | **P1** |
| 3 | Regulatory Horizon Scanner | ⭐⭐⭐⭐ | Media | **P1** |
| 4 | Semantic Spatial Layer | ⭐⭐⭐⭐ | Alta | **P2** |
| 5 | DSE + Gap Analysis | ⭐⭐⭐⭐⭐ | Media | **P2** |
| 6 | Adversarial Reasoning | ⭐⭐⭐ | Alta | **P3** |
| 7 | Federated Intelligence | ⭐⭐⭐ | Molto Alta | **P4** |
| 8 | Incident Reconstruction | ⭐⭐⭐ | Alta | **P4** |

---

## 8. Architettura Complessiva

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          AICOMSEC VERTICAL                              │
│                                                                         │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────────────┐   │
│  │  CANALE A   │    │  CANALE B    │    │     UX SURFACES         │   │
│  │  Documenti  │    │  Normative   │    │  Chat | Dashboard | API  │   │
│  │  Cliente    │    │  Pubbliche   │    └───────────┬─────────────┘   │
│  └──────┬──────┘    └──────┬───────┘                │                 │
│         │                  │                         │                 │
│         ▼                  ▼                         ▼                 │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │            OCULUS PRIME  (pre-epistemic intake)                 │   │
│  │     PDF │ DOCX │ Image │ Audio │ CAD/BIM │ Landscape │ Geo      │   │
│  └───────────────────────┬─────────────────────────────────────────┘   │
│                          │ oculus_prime.evidence.created                │
│                          ▼                                              │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │         BABEL GARDENS — AICOMSEC Consumer                        │  │
│  │   classify → sanitize PII → embed (SecBERT fusion) → upsert      │  │
│  └───────────────────────┬──────────────────────────────────────────┘  │
│                          │                                              │
│              ┌───────────▼──────────────┐                              │
│              │  QDRANT KNOWLEDGE BASE   │                              │
│              │  aicomsec.{tenant}.chunks│                              │
│              │  aicomsec.normative.*    │                              │
│              └───────────┬──────────────┘                              │
│                          │                                              │
│  ┌───────────────────────▼──────────────────────────────────────────┐  │
│  │              LANGGRAPH SECURITY PIPELINE                         │  │
│  │                                                                  │  │
│  │  parse → intent_detection → VSGS → entity_resolver              │  │
│  │     → decide → [                                                 │  │
│  │         document_query: RAG → VEE summary                       │  │
│  │         risk_assessment: VARE SecurityRiskProvider               │  │
│  │         gap_analysis:   VWRE SecurityAggregationProvider         │  │
│  │         technical_report: VEE SecurityExplainabilityProvider     │  │
│  │         compliance_check: VARE + Orthodoxy Wardens               │  │
│  │         mitigation_plan: Gap Analysis → DSE → Pareto ranking     │  │
│  │     ] → compose → orthodoxy → vault → output                    │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  VPAR — Algoritmi Proprietari                                  │    │
│  │  VARE (risk)  │  VWRE (attribution)  │  VEE (explainability)   │    │
│  │  + SecurityRiskProvider               + SecurityAggProvider    │    │
│  │  + SecurityExplainabilityProvider     (da implementare)        │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  DSE — Design Space Exploration (Pareto multi-obiettivo)       │    │
│  │  Input: gap_analysis output + budget + deadline + doctrine     │    │
│  │  Output: piano mitigazione ottimale con spiegazione VWRE       │    │
│  └────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

### Stack Tecnico

| Componente | Tecnologia | Port |
|-----------|-----------|------|
| Intake | Oculus Prime (FastAPI) | 8050 |
| LangGraph orchestration | api_graph (FastAPI) | 8010 |
| VPAR engines | Pura Python (LIVELLO 1) | — |
| Vector store | Qdrant | 6333 |
| Cognitive bus | Redis Streams | 6379 |
| Persistence | PostgreSQL | 5432 |
| LLM | LLMAgent → gpt-4o / configurabile | — |
| SecBERT | jackaduma/SecBERT (HuggingFace) | — |
| DSE optimizer | api_edge_dse | 8021 |
| AICOMSEC service | api_aicomsec (da creare) | 3001 |

**Naming tenant Qdrant**: `aicomsec.{tenant_id}.documents`, `aicomsec.{tenant_id}.chunks`, `aicomsec.{tenant_id}.semantic_states`

---

## 9. Sprint Plan

### Sprint 0 — COMPLETATO ✅ (Feb 2026)

| Task | Status | File |
|------|--------|------|
| Branch `feature/aicomsec-domain` | ✅ | — |
| `vertical_manifest.yaml` AICOMSEC | ✅ | `vertical_manifest.yaml` |
| `intent_config.py` (11 intents, 5 filter) | ✅ | `vitruvyan_core/domains/security/intent_config.py` |
| `governance_rules.py` (20 rules, 6 cat.) | ✅ | `vitruvyan_core/domains/security/governance_rules.py` |
| Fix: vit CLI 3 bug (repo, token, tag fetch) | ✅ | `core/platform/update_manager/engine/` |
| Upgrade core v1.5.0 → v1.6.1 | ✅ | — |

### Sprint 1 — PROSSIMO

| Task | Priorità | Dipendenze |
|------|----------|------------|
| Babel Gardens AICOMSEC consumer | P0 | Oculus Prime (ready) |
| Qdrant collections init script | P0 | RAG Governance Contract |
| `graph_plugin.py` security domain | P0 | `intent_config.py` ✅ |
| VPAR `SecurityRiskProvider` | P1 | VARE engine (ready) |
| VPAR `SecurityAggregationProvider` | P1 | VWRE engine (ready) |
| VPAR `SecurityExplainabilityProvider` | P1 | VEE engine (ready) |
| LangGraph security graph nodes | P1 | `graph_plugin.py` |

### Sprint 2 — BACKLOG

| Task | Funzionalità correlata |
|------|----------------------|
| Evidence Chain Constructor | §7 P1 |
| Compliance Entropy Monitor | §7 P2 |
| DSE integration (gap → Pareto plan) | §5 |
| Regulatory Horizon Scanner | §7 P3 |
| Semantic Spatial Layer | §7 P4 |

---

## 10. Domande Aperte

| # | Domanda | Impatto | Owner |
|---|---------|---------|-------|
| 1 | H2M vs M2M — quale modalità lanciare per prima al cliente? | Alto — condiziona UX e risorse Sprint 1 | Collega domain expert |
| 2 | Quanti tenant nel progetto pilota? | Alto — naming collections, auth JWT scope | PM |
| 3 | Il cliente vuole Evidence Chain Constructor nell'MVP o è post-MVP? | Alto — condiziona Sprint 1 | Collega domain expert |
| 4 | Quale dottrina DSE di default per il cliente pilota? | Medio | Collega domain expert |
| 5 | SecBERT: hosting locale o HuggingFace inference API? | Medio — latenza e costo | Tech lead |
| 6 | CAD/BIM: il cliente pilota ha planimetrie in formato standard (DXF/IFC)? | Alto per Semantic Spatial Layer | Collega domain expert |

---

## Riferimenti

| Documento | Path |
|-----------|------|
| Vertical Contract V1 | `docs/contracts/verticals/VERTICAL_CONTRACT_V1.md` |
| RAG Governance Contract | `docs/contracts/rag/` |
| Oculus Prime compliance | `services/api_edge_oculus_prime/` |
| DSE architecture | `infrastructure/edge/dse/` |
| VPAR engines | `vitruvyan_core/core/vpar/` |
| Finance VPAR providers (reference) | `vitruvyan_core/domains/finance/vpar/` |
| Security domain scaffold | `vitruvyan_core/domains/security/` |
| SACRED_ORDER_PATTERN | `vitruvyan_core/core/governance/SACRED_ORDER_PATTERN.md` |
| Appendix K — Babel Gardens | `.github/Vitruvyan_Appendix_K_Babel_Gardens.md` |
| Appendix I — Pattern Weavers | `.github/Vitruvyan_Appendix_I_Pattern_Weavers.md` |
