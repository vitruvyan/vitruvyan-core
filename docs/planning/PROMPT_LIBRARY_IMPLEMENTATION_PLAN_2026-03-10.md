# Prompt Library Core - Report e Piano d'Azione

> **Last updated**: Mar 10, 2026 11:35 UTC
> **Status**: READ-ONLY ANALYSIS / IMPLEMENTATION PLAN
> **Scope**: sviluppo in `vitruvyan-core`, poi import nei verticali come `aicomsec`
> **Origine**: analisi architetturale + peer verification esterna

---

## 0. Executive Summary

Il problema e' reale: il codebase ha gia' un `PromptRegistry` valido come base infrastrutturale, ma l'adozione runtime e' minima e gran parte dei prompt resta hardcoded nei nodi e nei servizi.

La decisione raccomandata e' questa:

- **non riscrivere da zero il sistema prompt**
- **estendere il `PromptRegistry` esistente**
- **introdurre un `PromptAgent` leggero come gateway canonico**
- **contrattualizzare la feature con un set minimo di DTO**
- **migrare progressivamente i prompt hardcoded verso il registry**

La priorita' numero uno non e' costruire una nuova architettura astratta, ma **portare adoption** sul codice reale.

Formula sintetica:

`PromptRegistry` + `PromptAgent` + `Prompt contracts` + `Prompt policy` + `gradual adoption`

---

## 1. Contesto e problema

In Vitruvyan OS il prompting oggi e' trattato in pratica come:

- stringhe sparse
- registry poco usato
- versioning per lo piu' decorativo
- log privi di metadati di audit sul prompt effettivamente usato

Questo e' insufficiente in generale, e particolarmente debole in un verticale security/compliance come `aicomsec`, dove il prompt definisce:

- perimetro epistemico
- limiti di comportamento
- regole di astensione
- priorita' tra tool, evidenza e generazione
- policy di comunicazione verso l'utente

In questo contesto il prompting non e' copywriting: e' un **layer operativo di governance**.

---

## 2. Stato attuale del codebase

### 2.1 Cosa esiste gia'

Il repository ha gia' una base utile:

- `core/llm/prompts/registry.py`
  - registrazione per dominio
  - risoluzione per dominio/scenario/lingua
  - fallback a dominio generico
  - combinazione `identity + scenario`
  - supporto base per version field
- `core/llm/prompts/version.py`
  - metadati di versione
- `domains/<domain>/prompts/`
  - pattern di prompt bundle di dominio
- almeno un call site reale nel runtime
  - uso dell'identity prompt via registry

### 2.2 Cosa manca davvero

Secondo peer audit e verifica architetturale, i gap reali sono:

| Gap | Stato attuale | Azione necessaria |
|-----|---------------|-------------------|
| Adoption | Registry poco usato | Migrare i call site hardcoded |
| Trace/Audit | Nessuna traccia forte | Aggiungere `prompt_id`, `version`, `hash`, `domain`, `scenario` |
| Policy layer | Assente | Aggiungere un layer di vincoli non negoziabili |
| Contratto formale | Assente | Creare DTO e documento di contract |
| Versioning runtime | Debole | Meccanismo di selezione della versione attiva |
| Plugin integration | Disallineata | Chiarire relazione tra registry e prompt dei plugin |
| Domain bundles | Presenti ma non governati | Standardizzare pattern bundle per dominio |

### 2.3 Cosa NON serve fare adesso

Non serve:

- buttare via il `PromptRegistry`
- spezzare subito il sistema in molti moduli separati
- rifondare tutto sotto un nuovo package solo teorico
- migrare in un colpo solo tutti i prompt del repository

---

## 3. Decisione architetturale

### 3.1 Decisione secca

La feature deve essere sviluppata in `vitruvyan-core` e poi importata dai verticali.

La forma architetturale corretta e':

- `PromptRegistry` come base di registrazione e composizione
- `PromptAgent` come gateway canonico verso il runtime
- `Prompt contracts` minimi per stabilizzare input/output
- `Prompt policy` come layer leggero di enforcement

### 3.2 Perche' contrattualizzare

Si', la feature va contrattualizzata.

Motivi:

- impedire che ogni nodo costruisca prompt arbitrari
- rendere il comportamento testabile senza chiamare l'LLM
- rendere il prompting osservabile e auditabile
- uniformare i verticali futuri oltre `security`

### 3.3 Pattern raccomandato

Non c'e' un falso dilemma tra `PromptRegistry` e `PromptAgent`.

Il pattern giusto e':

- `PromptRegistry` = storage strutturato + composizione base + fallback
- `PromptAgent` = wrapper sottile che orchestra il registry e restituisce una risoluzione completa

---

## 4. Architettura target pragmatica

```text
vitruvyan_core/
├── contracts/
│   └── prompting.py              # NEW
├── core/
│   ├── agents/
│   │   └── prompt_agent.py       # NEW
│   └── llm/prompts/
│       ├── registry.py           # EXISTING -> extend
│       ├── version.py            # EXISTING -> extend
│       └── policy.py             # NEW
└── domains/
    ├── security/prompts/         # EXISTING pattern
    └── <domain>/prompts/         # future domains
```

### Nota di architettura

Per i prossimi giorni **non e' necessario** creare un nuovo package ampio tipo `core/prompting/`.

Quella scelta potra' essere rivalutata piu' avanti, ma oggi il percorso corretto e':

- massimizzare compatibilita'
- ridurre diff inutili
- innestare la nuova capability sul codice gia' esistente

---

## 5. Contratti minimi richiesti

## 5.1 `PromptRequest`

Responsabilita':

- descrivere la richiesta di costruzione prompt

Campi minimi concettuali:

- `domain`
- `scenario`
- `language`
- `assistant_name`
- `template_vars`
- `policy_flags`
- `version_override` opzionale

## 5.2 `PromptResolution`

Responsabilita':

- descrivere il risultato della risoluzione

Campi minimi concettuali:

- `system_prompt`
- `domain`
- `scenario`
- `language`
- `version`
- `prompt_id`
- `prompt_hash`
- `policy_applied`
- `fallback_used`

## 5.3 `PromptPolicy`

Responsabilita':

- dichiarare vincoli non negoziabili

Esempi:

- no fabricated facts
- evidence first
- no legal advice
- declare confidence and limits
- stay in domain

### Nota importante

Questi sono i contratti minimi. Non serve partire con una tassonomia piu' grande.

---

## 6. Ruolo del PromptAgent

Il `PromptAgent` deve essere un **thin orchestrator**, non un god object.

Responsabilita':

- ricevere una `PromptRequest`
- interrogare il `PromptRegistry`
- applicare policy e versione
- comporre il risultato finale
- restituire una `PromptResolution`
- esporre metadati utilizzabili nei log runtime

Non deve:

- chiamare il modello
- duplicare la logica del `LLMAgent`
- sostituire il registry
- diventare un motore di business logic

---

## 7. Policy layer

Va aggiunto un file leggero, ad esempio:

- `core/llm/prompts/policy.py`

Scopo:

- applicare vincoli trasversali prima della composizione finale o durante la risoluzione

Esempi di utilizzo:

- aggiungere frammenti obbligatori
- bloccare combinazioni invalide
- iniettare avvertenze globali
- marcare policy applicate nei metadati di audit

Questo layer deve restare semplice e leggibile. Niente DSL complesse in Fase 1.

---

## 8. Priorita' reale: adoption

La priorita' numero uno e' spostare il runtime verso il sistema esistente esteso.

Il rischio maggiore oggi non e' l'assenza di teoria architetturale.
Il rischio maggiore e' il **numero di call site che continuano a costruire prompt hardcoded**.

La roadmap deve quindi partire dai nodi con impatto piu' alto.

---

## 9. Piano operativo per i prossimi giorni

## Fase 1 - Foundation minima e primi call site

**Obiettivo**: creare la capability minima senza rompere il runtime.

### Deliverable

1. `vitruvyan_core/contracts/prompting.py`
   - `PromptRequest`
   - `PromptResolution`
   - `PromptPolicy`

2. `vitruvyan_core/core/agents/prompt_agent.py`
   - wrapper leggero attorno al registry
   - output con metadati minimi di audit

3. Estensione di `vitruvyan_core/core/llm/prompts/registry.py`
   - supporto a `prompt_id`
   - supporto a trace metadata base
   - compatibilita' backward-safe con le API attuali

4. Estensione di `vitruvyan_core/core/llm/prompts/version.py`
   - meccanismo di selezione versione attiva
   - override runtime opzionale

5. Migrazione di 3-4 punti chiave del runtime
   - `compose_node`
   - `cached_llm_node`
   - `llm_mcp_node`
   - eventuale rifinitura di `can_node`

### Obiettivo di Fase 1

Portare il prompting da:

- registry presente ma marginale

a:

- registry usato in piu' punti critici
- gateway canonico disponibile
- metadati di audit disponibili

---

## Fase 2 - Governance e contract enforcement

**Obiettivo**: stabilizzare la feature come capability core.

### Deliverable

6. `vitruvyan_core/core/llm/prompts/policy.py`
7. trace metadata nei log runtime
8. documento `PROMPT_CONTRACT_V1.md`
9. test unitari sul nuovo contratto e sul `PromptAgent`

### Obiettivo di Fase 2

- policy centrale minima
- audit leggibile
- contratto esplicito per i contributor

---

## Fase 3 - Evoluzione e convergenza

**Obiettivo**: unificare nel tempo i diversi sistemi prompt del kernel.

### Deliverable

10. chiarire l'integrazione con prompt di plugin tipo:
    - `ISemanticPlugin.get_system_prompt()`
    - comprehension plugins

11. supporto per:
    - A/B testing
    - versioning runtime reale
    - rollback chiaro

12. standard bundle per verticali futuri
    - security
    - finance
    - altri domini

### Obiettivo di Fase 3

Passare da adozione locale a infrastruttura cross-domain.

---

## 10. Definition of Done

La feature puo' essere considerata correttamente avviata quando:

- esiste un `PromptAgent` importabile dal core
- esistono contratti minimi per request e resolution
- almeno 3 nodi runtime usano il nuovo percorso
- i log espongono `prompt_id`, `version`, `hash`
- il `PromptRegistry` resta compatibile e piu' capace di prima
- la policy minima e' documentata
- il percorso di sviluppo resta nel repo `vitruvyan-core`, non nei verticali

---

## 11. Non-goals espliciti

Non fanno parte della prima iterazione:

- migrazione completa di tutti i prompt del repo
- redesign completo del package layout
- nuovo framework di templating
- policy engine complesso
- supporto multi-provider avanzato lato prompt
- refactor totale dei plugin semantic/comprehension

---

## 12. Rischi e attenzioni

### Rischio 1 - Over-engineering

Se si aprono troppi file e troppi concetti subito, la feature si blocca in analisi.

**Mitigazione**:
- mantenere Fase 1 piccola
- riusare `PromptRegistry`
- introdurre solo il minimo indispensabile

### Rischio 2 - Refactor astratto senza adoption

Si puo' produrre una bella architettura senza cambiare il comportamento reale del runtime.

**Mitigazione**:
- migrare subito i call site chiave

### Rischio 3 - Contratti troppo larghi

Troppi DTO all'inizio aumentano attrito e non danno valore immediato.

**Mitigazione**:
- partire solo con `PromptRequest`, `PromptResolution`, `PromptPolicy`

---

## 13. Decisione finale raccomandata

Decisione da assumere come base di sviluppo:

- **si'** a una Prompt Library core in `vitruvyan-core`
- **si'** a una architettura coerente con gli agent esistenti
- **si'** alla contrattualizzazione della feature
- **si'** a un `PromptAgent` sottile
- **si'** all'estensione del `PromptRegistry`
- **no** a una riscrittura totale del sistema
- **no** a una proliferazione iniziale di moduli astratti
- **si'** a un piano incrementale guidato da adoption

---

## 14. Prompt operativo per la prossima sessione

```text
Sto aprendo la feature Prompt Library core in vitruvyan-core.

Assumi questa decisione architetturale:
- non riscrivere il PromptRegistry
- estenderlo
- introdurre PromptAgent come thin wrapper
- aggiungere contratti minimi:
  - PromptRequest
  - PromptResolution
  - PromptPolicy
- aggiungere policy.py leggero
- iniziare dai call site a maggior impatto:
  - compose_node
  - cached_llm_node
  - llm_mcp_node

Obiettivo della sessione:
1. implementare Fase 1 minima
2. mantenere backward compatibility
3. preparare la feature per essere importata poi nei verticali

Non fare redesign totale.
Non creare un nuovo framework astratto.
Massimizza adoption e tracciabilita' runtime.
```

---

## 15. Chiusura

Questo documento deve essere letto come guida pragmatica di sviluppo.

La direzione strategica resta corretta: il prompting deve diventare infrastruttura core.
La correzione tattica e' altrettanto chiara: bisogna partire dal `PromptRegistry` che gia' esiste, aggiungere il minimo indispensabile e portare il runtime a usarlo davvero.
