# AICOMSEC — Flusso di Ingestione: Esempio Concreto (Excel Assessment)

> **Last updated**: Feb 27, 2026 14:00 UTC
> **Tipo**: Walkthrough tecnico — esempio reale per onboarding
> **File sorgente**: `assessment_contursi_feb25.xlsx` — Impianto di Linea Contursi, Snam S.p.A.
> **Documento correlato**: [AICOMSEC_BRAINSTORM_REPORT.md](./AICOMSEC_BRAINSTORM_REPORT.md)

---

## Il file sorgente

Un workbook Excel di assessment di sicurezza fisica/cyber con **7 fogli interdipendenti**:

| Foglio | Contenuto |
|--------|-----------|
| **Informazioni generali Asset** | Anagrafica: denominazione, tipologia, società, settore, comune, provincia, regione, data assessment |
| **Data Validation** | Lookup list: livelli implementazione, tipologie asset, società del gruppo (Snam, Snam Rete Gas, GNL Italia…) |
| **Checklist 1 - Rischio inerente** | Criteri (a) geografici/territoriali, (b) vulnerabilità strutturale, (c) criticità business → calcola RISCHIO INERENTE |
| **Checklist 2 - Misure di sicurezza** | ~50 misure distribuite su 8 ambiti → livello AS-IS vs baseline → GAP |
| **SCOPERTURA MISURE** | % copertura per categoria (AS-IS e TO-BE), visualizzata come radar chart |
| **CALCOLO RI_RR** | Formula finale: Rischio Residuo AS-IS e TO-BE (matrice probabilità × impatto) |
| **FINDIGS** | Raccomandazioni con stima economica per ogni gap aperto |

**Asset di riferimento in questo esempio**:

```
DENOMINAZIONE:  IMPIANTO DI LINEA CONTURSI
TIPOLOGIA:      Impianto di linea
SOCIETÀ:        Snam S.p.A.
SETTORE:        Idrogeno
COMUNE:         Contursi Terme (SA) — Campania
DATA ASSESSMENT: feb-2025
```

---

## Stadio 1 — Oculus Prime riceve il file

Oculus Prime (port 8050) è il **pre-epistemic intake**: non fa NER, non fa embedding, non interpreta il significato. Smonta il workbook foglio per foglio ed emette un **Evidence Envelope** sul bus Redis.

```python
# Redis Stream: oculus_prime.evidence.created

{
    "evidence_id": "ev_contursi_20260227",
    "tenant_id":   "snam_infrastrutture",
    "source_uri":  "upload://assessment_contursi_feb25.xlsx",
    "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",

    "sheets": {
        "Informazioni generali Asset": {
            "DENOMINAZIONE ASSET": "IMPIANTO DI LINEA CONTURSI",
            "TIPOLOGIA ASSET":     "Impianto di linea",
            "SOCIETA'":            "Snam S.p.A.",
            "SETTORE":             "Idrogeno",
            "COMUNE":              "Contursi Terme",
            "PROVINCIA":           "Salerno",
            "DATA ASSESSMENT":     "feb-25"
        },
        "Checklist 1 - Rischio inerente": {
            "rows": [
                {"id":"c1",  "criterio":"Furti/Rapine",                   "fonte":"MisCrime DB",  "valutazione":"BASSO"},
                {"id":"c2",  "criterio":"Atti vandalici/eventi estremi",   "fonte":"MisCrime DB",  "valutazione":"BASSO"},
                {"id":"c3",  "criterio":"Manifestazioni/Proteste",         "fonte":"MisCrime DB",  "valutazione":"BASSO"},
                {"id":"b3",  "criterio":"Utilizzo dispositivi IT/OT critici","valutazione":"ALTO"},
                {"id":"c_biz","criterio":"Criticità per il business",      "valutazione":"SI"}
            ]
        },
        "Checklist 2 - Misure di sicurezza": {
            "rows": [
                {"id":"SFP1",  "ambito":"SICUREZZA FISICA PASSIVA",
                 "misura":"Il perimetro del sito deve essere interamente segregato...",
                 "livello_asis":"Completamente Implementata e in funzione", "gap": 0},

                {"id":"IARD1", "ambito":"INFRASTRUTTURA ALIMENTAZIONE RETE DATI",
                 "misura":"L'infrastruttura di alimentazione deve essere dedicata e segregata...",
                 "livello_asis":"Non Implementata", "gap": 1},

                {"id":"AI2",   "ambito":"SISTEMA ANTINTRUSIONE",
                 "misura":"Il sistema di antintrusione deve garantire la protezione del perimetro sito...",
                 "livello_asis":"Non Implementata", "gap": 1},

                {"id":"CA1",   "ambito":"SISTEMA CONTROLLO ACCESSI",
                 "misura":"I varchi pedonali di accesso al sito devono essere dotati di...",
                 "livello_asis":"Non Implementata", "gap": 1},

                {"id":"VS2",   "ambito":"SISTEMA VIDEOSORVEGLIANZA",
                 "misura":"Il sistema di videosorveglianza deve garantire il monitoraggio perimetro sito...",
                 "livello_asis":"Non Implementata", "gap": 1}
                # ... ~50 righe totali
            ]
        },
        "FINDIGS": {
            "rows": [
                {"id":"IARD1", "raccomandazione":"Si richiede di predisporre Infrastruttura di alimentazione del SIS dedicata e segregata rispetto a tutti gli altri impianti elettrici di sito come da standard di Gruppo (SECUR)"},
                {"id":"AI2",   "raccomandazione":"Si richiede di prevedere contatti magnetici sul perimetro del sito"},
                {"id":"VS2",   "raccomandazione":"Si richiede di prevedere che il sistema di videosorveglianza garantisca il monitoraggio del perimetro"}
            ]
        }
    },
    "metadata": {
        "filename":    "assessment_contursi_feb25.xlsx",
        "sheet_count": 7,
        "asset_type":  "critical_infrastructure",
        "ingested_at": "2026-02-27T09:00:00Z"
    }
}
```

> **Nota**: le celle `#NOME?` visibili nel file originale sono errori di formula Excel (baseline non ancora compilata). Oculus Prime li cattura come stringa `"#NOME?"`. Codex Hunters li marcherà `data_quality: incomplete` — la pipeline non si blocca.

---

## Stadio 2 — Codex Hunters → PostgreSQL

Codex Hunters consuma `codex.entity.bound` e produce **due tipi di entità** da questo file: l'asset principale + una entità per ogni gap aperto.

### Tabella `codex_entities`

```sql
-- 1. Asset principale
INSERT INTO codex_entities VALUES (
  'ent_contursi_asset',
  'ev_contursi_20260227',
  'snam_infrastrutture',
  'IMPIANTO DI LINEA CONTURSI',
  'critical_infrastructure',        -- tipo classificato da Codex Hunters
  'security',                       -- domain_family
  '{
    "tipologia": "Impianto di linea",
    "societa": "Snam S.p.A.",
    "settore": "Idrogeno",
    "comune": "Contursi Terme",
    "provincia": "Salerno",
    "regione": "Campania",
    "data_assessment": "2025-02",
    "asset_type_normalized": "pipeline_facility",
    "data_quality": "partial"       -- celle #NOME? rilevate
  }',
  '2026-02-27T09:01:00Z'
);

-- 2. Un record per ogni misura NON IMPLEMENTATA
INSERT INTO codex_entities VALUES (
  'ent_contursi_gap_IARD1',
  'ev_contursi_20260227',
  'snam_infrastrutture',
  'GAP: Infrastruttura alimentazione rete dati non dedicata/segregata',
  'security_gap',
  'security',
  '{
    "measure_id": "IARD1",
    "ambito": "INFRASTRUTTURA ALIMENTAZIONE RETE DATI",
    "livello_asis": "Non Implementata",
    "baseline_required": "Richiesto",
    "gap_open": true,
    "raccomandazione": "Predisporre Infrastruttura SIS dedicata e segregata — standard SECUR Gruppo"
  }',
  '2026-02-27T09:01:02Z'
),
(
  'ent_contursi_gap_AI2',
  'ev_contursi_20260227',
  'snam_infrastrutture',
  'GAP: Sistema antintrusione perimetro sito non implementato',
  'security_gap',
  'security',
  '{
    "measure_id": "AI2",
    "ambito": "SISTEMA ANTINTRUSIONE",
    "livello_asis": "Non Implementata",
    "baseline_required": "Richiesto",
    "gap_open": true,
    "raccomandazione": "Prevedere contatti magnetici sul perimetro del sito"
  }',
  '2026-02-27T09:01:03Z'
);
-- Stesso pattern per: AI3, AI4, AI5-AI8, CA1, CA3, VS1, VS2, VS4, IARD2, IARD3, IARD4 ...
```

### Tabella `codex_lineage`

```sql
INSERT INTO codex_lineage VALUES
  ('ent_contursi_asset',     'ev_contursi_20260227', 'Informazioni generali Asset',  'codex_hunters_v1'),
  ('ent_contursi_gap_IARD1', 'ev_contursi_20260227', 'Checklist 2 + FINDIGS',        'codex_hunters_v1'),
  ('ent_contursi_gap_AI2',   'ev_contursi_20260227', 'Checklist 2 + FINDIGS',        'codex_hunters_v1');
```

---

## Stadio 3 — Babel Gardens + Pattern Weavers → Qdrant

Collection: `aicomsec.snam_infrastrutture.chunks`

Vengono creati vettori **distinti per cluster tematico** — non uno per riga Excel, ma uno per gruppo di misure affini (più efficiente per la retrieval semantica).

```python
# Vettore 1 — Contesto asset
{
    "id": "chunk_contursi_asset_info",
    "vector": [...],    # 768-dim SecBERT
    "payload": {
        "entity_id":    "ent_contursi_asset",
        "tenant_id":    "snam_infrastrutture",
        "text":         "IMPIANTO DI LINEA CONTURSI — Tipologia: Impianto di linea — Snam S.p.A. — Settore: Idrogeno — Contursi Terme (SA), Campania — Assessment: feb-2025",
        "domain_class": "operational",
        "security_category": "critical_infrastructure",
        "asset_type":   "pipeline_facility",
        "company":      "Snam S.p.A.",
        "sector":       "Idrogeno",
        "location_geo": {"comune": "Contursi Terme", "provincia": "Salerno", "regione": "Campania"},
        "ontology_class": "asset/critical",
        "intent_hint":  "risk_assessment"
    }
}

# Vettore 2 — Cluster gap SISTEMA ANTINTRUSIONE (AI1–AI8, tutti Non Implementata)
{
    "id": "chunk_contursi_gap_antintrusione",
    "vector": [...],
    "payload": {
        "text":         "SISTEMA ANTINTRUSIONE: AI1-AI8 tutti Non Implementata. Perimetro sito, edifici, aree locali sensibili, impianti tecnologici, integrazione altri sistemi. Baseline: Richiesto per Impianto di linea. Raccomandazioni: contatti magnetici perimetro, volumetrici interni a trappola, contatti magnetici cancelli.",
        "domain_class": "cyber",
        "security_category": "sistema_antintrusione",
        "ambito_id":    "AI",
        "gap_count":    8,
        "coverage_pct": 0.0,
        "severity":     "high",
        "ontology_class": "compliance/control_gap",
        "intent_hint":  "gap_analysis",
        "norm_refs":    ["NIS2 Art.21", "SECUR Gruppo"]
    }
}

# Vettore 3 — Gap IARD (infrastruttura rete dati Security)
{
    "id": "chunk_contursi_gap_IARD",
    "vector": [...],
    "payload": {
        "text":         "INFRASTRUTTURA ALIMENTAZIONE RETE DATI: IARD1 alimentazione SIS non dedicata Non Implementata. IARD2 rete dati non conforme DTBIN Non Implementata. IARD3 continuità assoluta UPS/gruppo elettrogeno Non Implementata. IARD4 impianti tecnologici locali sensibili Non Implementata.",
        "domain_class": "cyber",
        "security_category": "infrastruttura_rete_dati",
        "ambito_id":    "IARD",
        "gap_count":    4,
        "coverage_pct": 0.0,
        "norm_refs":    ["SECUR Gruppo", "DTBIN", "IEC 62443"],
        "ontology_class": "compliance/control_gap",
        "intent_hint":  "gap_analysis"
    }
}

# Vettore 4 — Rischio inerente (da Checklist 1)
{
    "id": "chunk_contursi_rischio_inerente",
    "vector": [...],
    "payload": {
        "text":         "Rischio inerente Impianto Linea Contursi Terme: contesto geografico BASSO — furti, atti vandalici, manifestazioni storicamente bassi (MisCrime DB). Utilizzo dispositivi IT/OT critici: ALTO. Criticità per il business: SÌ. Asset infrastruttura critica settore idrogeno.",
        "domain_class": "operational",
        "security_category": "risk_assessment",
        "risk_context": {
            "geo_risk":          "BASSO",
            "iot_criticality":   "ALTO",
            "business_critical": True,
            "asset_sector":      "Idrogeno"
        },
        "ontology_class": "risk/inherent",
        "intent_hint":    "risk_assessment"
    }
}

# Vettore 5 — Misure SFP implementate (benchmark positivo)
{
    "id": "chunk_contursi_sfp_implemented",
    "vector": [...],
    "payload": {
        "text":         "SICUREZZA FISICA PASSIVA: SFP1 perimetro segregato Completamente Implementata. SFP5 resistenza perimetro edifici Completamente Implementata. SFP6 locali tecnici aree sensibili Completamente Implementata. SFP7 locali altamente sensibili Completamente Implementata. SFP8 sicurezza aree tecniche Completamente Implementata.",
        "domain_class": "physical",
        "security_category": "sicurezza_fisica_passiva",
        "coverage_pct": 0.80,
        "gap_open":     False,
        "ontology_class": "compliance/control_met",
        "intent_hint":  "technical_report"
    }
}
```

---

## Stadio 4 — Query via Graph: tre esempi

### Query 1 — Gap analysis completa

**Input del consulente** (chat H2M):
> *"Quali sistemi di sicurezza mancano completamente all'impianto di Contursi?"*

**LangGraph flow**:
```
parse → intent_detection: gap_analysis
→ entity_resolver: asset=CONTURSI, tenant=snam_infrastrutture
→ RAG su Qdrant con filtro: gap_open=True
→ SecurityAggregationProvider (VWRE): raggruppa per ambito
→ VEE SecurityExplainabilityProvider: narrativa livello "Technical"
→ compose → output
```

**Query Qdrant**:
```python
qdrant.search(
    collection="aicomsec.snam_infrastrutture.chunks",
    query_vector=embed("sistemi sicurezza non implementati mancanti"),
    query_filter={"must": [{"key": "gap_open", "match": {"value": True}}]},
    limit=10
)
# → restituisce cluster AI, IARD, CA, VS
```

**Risposta generata**:
```
L'Impianto di Linea Contursi presenta grave scopertura su 4 ambiti:

• SISTEMA ANTINTRUSIONE (AI) — 0% implementato (8/8 misure mancanti)
  Nessun rilevatore perimetrale, nessun sistema volumetrico interno.
  Raccomandazione: contatti magnetici perimetro + volumetrici a trappola.

• SISTEMA CONTROLLO ACCESSI (CA) — 0% implementato
  Nessun varco pedonale controllato, nessun videocitofonico.

• SISTEMA VIDEOSORVEGLIANZA (VS) — circa 15% implementato
  Nessuna copertura perimetrale. Copertura parziale interno.

• INFRASTRUTTURA RETE DATI SECURITY (IARD) — 0% implementato (4/4 mancanti)
  Alimentazione SIS non segregata (IARD1), rete non conforme DTBIN (IARD2).

Totale: ~35 gap aperti su ~50 misure obbligatorie per infrastruttura critica.

Fonte: assessment_contursi_feb25.xlsx [feb-2025]
```

---

### Query 2 — Compliance check NIS2

**Input** (API M2M):
```json
POST /v1/compliance/gap-analysis
{
    "asset_id": "ent_contursi_asset",
    "framework": "NIS2",
    "article": "Art. 21"
}
```

**LangGraph flow**:
```
intent: compliance_check
→ RAG con filtro: norm_refs contains "NIS2"
→ VARE SecurityRiskProvider: calcola compliance_gap
→ VEE: livello "Detailed" (per auditor)
```

**Risposta**:
```
IMPIANTO DI LINEA CONTURSI — Conformità NIS2 Art. 21: NON CONFORME

Misure NIS2 Art. 21 obbligatorie per infrastruttura critica (Idrogeno):

✗  Sicurezza fisica — controllo accessi (CA): Non Implementata
✗  Sicurezza fisica — antintrusione (AI): Non Implementata
✗  Sicurezza reti e sistemi informativi (IARD): Non Implementata
✓  Sicurezza fisica passiva perimetrale (SFP1, SFP5–SFP8): Implementata

Compliance gap: 78% delle misure NIS2 Art. 21 non soddisfatte.

Azioni prioritarie (baseline "Richiesto" per Impianto di linea — rischio ALTO):
  1. IARD1: segregare alimentazione SIS — standard SECUR Gruppo
  2. AI1–AI8: installare sistema antintrusione completo
  3. CA1–CA8: installare controllo accessi varchi

Fonte: Checklist 2 + FINDIGS, assessment feb-2025.
```

---

### Query 3 — Evidence Chain Constructor

**Input**:
```json
POST /v1/evidence/chain
{
    "norm": "NIS2",
    "article": "Art. 21",
    "tenant_id": "snam_infrastrutture"
}
```

**Risposta** (pacchetto prove per auditor):
```json
{
    "norm": "NIS2",
    "article": "Art. 21",
    "tenant_id": "snam_infrastrutture",
    "entity_fqn": "aicomsec.snam_infrastrutture.normative.nis2_art_21",
    "evidence_chain": [
        {
            "step": 1,
            "type": "normative_reference",
            "entity_fqn": "aicomsec.snam_infrastrutture.normative.nis2_art_21",
            "description": "NIS2 Art. 21 — Misure di sicurezza per la gestione dei rischi"
        },
        {
            "step": 2,
            "type": "source_document",
            "entity_fqn": "aicomsec.snam_infrastrutture.ingested.assessment_contursi_feb25",
            "description": "Assessment Sicurezza — Impianto Linea Contursi, Snam S.p.A., feb-2025"
        },
        {
            "step": 3,
            "type": "chunk",
            "entity_fqn": "aicomsec.snam_infrastrutture.processed.gap_antintrusione",
            "description": "GAP: SISTEMA ANTINTRUSIONE — 0% implementato — 8 misure mancanti",
            "metadata": {"direction": "downstream", "pipeline": "babel_gardens"}
        },
        {
            "step": 4,
            "type": "chunk",
            "entity_fqn": "aicomsec.snam_infrastrutture.processed.gap_IARD",
            "description": "GAP: IARD1–IARD4 — Infrastruttura SIS non segregata, rete non conforme DTBIN",
            "metadata": {"direction": "downstream", "pipeline": "babel_gardens"}
        },
        {
            "step": 5,
            "type": "chunk",
            "entity_fqn": "aicomsec.snam_infrastrutture.processed.sfp_implemented",
            "description": "CONFORME: SFP1, SFP5–SFP8 — Sicurezza fisica passiva completamente implementata",
            "metadata": {"direction": "downstream", "pipeline": "babel_gardens"}
        }
    ],
    "chain_hash": "sha256:a3f9c1d8b4e2f701",
    "lineage_available": true,
    "retrieved_at": "2026-02-27T14:00:00Z"
}
```

---

## Riepilogo per il collega

```
Excel (7 fogli)
│
├─ "Informazioni generali Asset"
│   └─► PostgreSQL codex_entities  (tipo=critical_infrastructure)
│        └─► Qdrant: vettore contesto asset (settore, geo, tipologia)
│
├─ "Checklist 1 - Rischio inerente"
│   └─► PostgreSQL codex_entities  (tipo=risk_assessment)
│        └─► Qdrant: vettore rischio inerente (geo BASSO, IT/OT ALTO, business critico)
│
├─ "Checklist 2 - Misure di sicurezza"  [~50 righe → ~35 gap aperti]
│   ├─► PostgreSQL: 1 entità per ogni misura "Non Implementata"
│   └─► Qdrant: 5 vettori cluster (SFP ✓, IARD ✗, AI ✗, CA ✗, VS ✗, PSM, RVCR)
│
├─ "FINDIGS"
│   └─► arricchisce payload Qdrant con testo raccomandazione
│        e norm_refs (NIS2, SECUR Gruppo, DTBIN, IEC 62443)
│
└─ "CALCOLO RI_RR"
    └─► alimenta signal_mapper Pattern Weavers
         → VPAR SecurityRiskProvider (score finale rischio residuo)
```

| Componente | Cosa contiene dopo l'ingestione |
|-----------|--------------------------------|
| **PostgreSQL** `codex_entities` | 1 record asset + ~35 record gap, ciascuno con metadata strutturato (ambito, misura, livello AS-IS, raccomandazione) |
| **PostgreSQL** `codex_lineage` | Traccia: da quale foglio Excel viene ogni entità, quale pipeline l'ha processata |
| **Qdrant** `aicomsec.snam_infrastrutture.chunks` | 5–7 vettori 768-dim per cluster tematico, ricercabili semanticamente con filtri (gap_open, coverage_pct, norm_refs, ambito_id) |
| **OpenMetadata** | DAG di lineage: file Excel → entity → chunk → embedding — usato dall'Evidence Chain Constructor per costruire il pacchetto prove NIS2 |

**Punto chiave**: il file Excel entra come documento opaco. Dopo ~30 secondi è interrogabile semanticamente — "*quali sistemi mancano?*", "*siamo conformi NIS2?*", "*costruisci il pacchetto prove per l'auditor*" — senza riaprire il file.
