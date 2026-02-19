# 🐙 Vitruvyan: Architettura Cognitiva Bio-Ispirata

**Documento per Stakeholder Tecnici e Istituzionali**

*Versione 1.0 — 27 Gennaio 2026*

---

## 📖 Sommario Esecutivo

Vitruvyan è un **sistema operativo cognitivo** (Epistemic Operating System) progettato per prendere decisioni complesse in modo trasparente, auditabile e resiliente.

La sua architettura è ispirata a due organismi biologici:
- 🐙 **Il Polipo**: Intelligenza distribuita (2/3 dei neuroni nelle braccia)
- 🍄 **I Funghi**: Rete miceliare decentralizzata (nessun nodo centrale)

**Risultato**: Un sistema che non ha single point of failure, dove ogni componente può operare autonomamente e la comunicazione è auto-riparante.

---

## 🧬 Parte 1: Il Sistema Generale (Vitruvyan come OS)

### 1.1 I Tre Componenti Fondamentali

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  🧠 CERVELLO (LangGraph)                                            │
│  ─────────────────────                                              │
│  • Riceve la richiesta                                              │
│  • Capisce cosa bisogna fare                                        │
│  • Decide QUALI tentacoli attivare e in che ORDINE                  │
│  • NON esegue il lavoro, solo coordina                              │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  🦑 TENTACOLI (Consumers/Servizi)                                   │
│  ────────────────────────────────                                   │
│  • Ogni tentacolo è SPECIALIZZATO in un compito                     │
│  • Lavorano AUTONOMAMENTE quando attivati                           │
│  • Possono comunicare TRA LORO senza passare dal cervello           │
│  • Se un tentacolo muore, gli altri continuano                      │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  🍄 RETE NERVOSA (Cognitive Bus / Redis Streams)                    │
│  ──────────────────────────────────────────────                     │
│  • Connette i tentacoli tra loro                                    │
│  • Trasporta messaggi/eventi                                        │
│  • NON ha un nodo centrale (come i miceli di un fungo)              │
│  • Se un canale muore, la rete si auto-ripara                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Schema Visivo Semplificato

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#2d3436', 'primaryTextColor': '#fff', 'lineColor': '#6c5ce7'}}}%%

graph TB
    subgraph BRAIN["🧠 CERVELLO<br/>(LangGraph)"]
        B["Decisioni di alto livello<br/><i>'Devo valutare questo input'</i>"]
    end

    subgraph BUS["🍄 RETE NERVOSA<br/>(Cognitive Bus)"]
        N["Connessioni tra tentacoli<br/><i>I tentacoli parlano tra loro</i>"]
    end

    subgraph TENTACLES["🦑 TENTACOLI<br/>(Servizi Autonomi)"]
        T1["Intake<br/><i>Acquisisce dati</i>"]
        T2["Pattern Weavers<br/><i>Estrae significato</i>"]
        T3["Neural Engine<br/><i>Calcola ranking</i>"]
        T4["VEE<br/><i>Spiega risultati</i>"]
        T5["Vault<br/><i>Archivia tutto</i>"]
    end

    B -->|"attiva"| T1
    B -->|"attiva"| T2
    B -->|"attiva"| T3
    B -->|"attiva"| T4
    
    T1 <-->|"comunica"| N
    T2 <-->|"comunica"| N
    T3 <-->|"comunica"| N
    T4 <-->|"comunica"| N
    T5 <-->|"comunica"| N

    classDef brain fill:#6c5ce7,stroke:#a29bfe,stroke-width:3px,color:#fff
    classDef bus fill:#fdcb6e,stroke:#f39c12,stroke-width:3px,color:#2d3436
    classDef tentacle fill:#00b894,stroke:#00cec9,stroke-width:2px,color:#fff

    class B brain
    class N bus
    class T1,T2,T3,T4,T5 tentacle
```

### 1.3 Perché Questa Architettura?

#### Il Vantaggio del Polipo

| Sistema Tradizionale | Sistema Polipo (Vitruvyan) |
|---------------------|---------------------------|
| Tutto passa dal cervello | I tentacoli pensano da soli |
| Se il cervello muore, tutto muore | Se un tentacolo muore, gli altri continuano |
| Collo di bottiglia centrale | Elaborazione parallela |
| Difficile da scalare | Scala aggiungendo tentacoli |

#### I 4 Benefici Chiave

1. **🛡️ Resilienza**: Nessun single point of failure
2. **📈 Scalabilità**: Aggiungi tentacoli senza modificare il cervello
3. **🔍 Auditabilità**: Ogni evento è tracciato
4. **🧠 Autonomia**: Ogni tentacolo può decidere localmente

---

## 🏛️ Parte 2: Vitruvyan — Un Esempio di Sistema di Dominio

### 2.1 Cos'è Vitruvyan?

**Vitruvyan** (Advanced Exploration of Generative Infrastructure Solutions) è un **vertical** di Vitruvyan specializzato in **Design Space Exploration** — la valutazione di configurazioni architetturali complesse.

Mentre Vitruvyan è il "sistema operativo", Vitruvyan è un'"applicazione" che gira su di esso.

### 2.2 Il Percorso Cognitivo Completo in Vitruvyan

Quando un **frammento di informazione** entra nel sistema Vitruvyan, attraversa un percorso preciso. Ecco il flusso reale, basato sul codice sorgente:

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  FASE 1: ACQUISIZIONE (Intake Layer)                                │
│  ═══════════════════════════════════                                │
│                                                                     │
│  📥 Un documento/immagine/audio/video entra nel sistema             │
│       ↓                                                             │
│  📦 Intake Agent (Document/Image/Audio/Video) lo processa           │
│       ↓                                                             │
│  📋 Crea un "Evidence Pack" (pacchetto di evidenza immutabile)      │
│       ↓                                                             │
│  💾 Salva in PostgreSQL (append-only, mai modificato)               │
│       ↓                                                             │
│  📡 Emette evento: "intake.evidence.created"                        │
│                                                                     │
│  ⚠️  IMPORTANTE: L'Intake NON interpreta il contenuto.              │
│      Acquisisce e normalizza. Basta.                                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              │ 🍄 (via Cognitive Bus)
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  FASE 2: ARRICCHIMENTO (Codex Hunters)                              │
│  ═════════════════════════════════════                              │
│                                                                     │
│  🎧 EventHunter ascolta "intake.evidence.created"                   │
│       ↓                                                             │
│  🔍 Recupera Evidence Pack da PostgreSQL                            │
│       ↓                                                             │
│  🧮 Genera embeddings vettoriali (per ricerca semantica)            │
│       ↓                                                             │
│  💾 Salva embeddings in Qdrant (memoria vettoriale)                 │
│       ↓                                                             │
│  📡 Emette evento: "codex.evidence.indexed"                         │
│                                                                     │
│  ⚠️  IMPORTANTE: Codex Hunters arricchisce ma NON decide.           │
│      Prepara i dati per l'elaborazione successiva.                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              │ 🍄 (via Cognitive Bus)
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  FASE 3: PONTE (Intake-DSE Bridge)                                  │
│  ═════════════════════════════════                                  │
│                                                                     │
│  🌉 IntakeDSEBridge ascolta "codex.evidence.indexed"                │
│       ↓                                                             │
│  📋 Crea record in dse_intake_evidence (tracciabile)                │
│       ↓                                                             │
│  📡 Emette evento: "langgraph.intake.ready"                         │
│                                                                     │
│  ⚠️  IMPORTANTE: Il Bridge collega il mondo pre-epistemico          │
│      (Intake/Codex) al mondo epistemico (LangGraph/DSE).            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              │ 🍄 (via Cognitive Bus)
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  FASE 4: ELABORAZIONE COGNITIVA (LangGraph - Il Cervello)           │
│  ════════════════════════════════════════════════════════           │
│                                                                     │
│  🧠 LangGraph riceve "langgraph.intake.ready" e ATTIVA i nodi:      │
│                                                                     │
│     ┌─────────────────────────────────────────────────────────┐     │
│     │  Nodo 1: parse_node                                     │     │
│     │  → Estrae entità base (design_point_ids, parametri)     │     │
│     └─────────────────────────────────────────────────────────┘     │
│                              ↓                                      │
│     ┌─────────────────────────────────────────────────────────┐     │
│     │  Nodo 2: intent_detection_node                          │     │
│     │  → Classifica l'intento (evaluate, optimize, compare)   │     │
│     └─────────────────────────────────────────────────────────┘     │
│                              ↓                                      │
│     ┌─────────────────────────────────────────────────────────┐     │
│     │  Nodo 3: pattern_weavers_node  🦑 TENTACOLO             │     │
│     │  → Estrae ipotesi semantiche (concetti, vincoli)        │     │
│     │  → Output: SemanticHypothesis (NON VINCOLANTE)          │     │
│     └─────────────────────────────────────────────────────────┘     │
│                              ↓                                      │
│     ┌─────────────────────────────────────────────────────────┐     │
│     │  Nodo 4: orthodoxy_gate_node  🛡️ VALIDAZIONE            │     │
│     │  → Valida ipotesi contro contratti sacri (dogma)        │     │
│     │  → Se valido: ApprovedKernelInput (VINCOLANTE)          │     │
│     │  → Se invalido: RejectionReport (richiede correzione)   │     │
│     └─────────────────────────────────────────────────────────┘     │
│                              ↓                                      │
│     ┌─────────────────────────────────────────────────────────┐     │
│     │  Nodo 5: dse_node  🦑 TENTACOLO (Neural Engine)         │     │
│     │  → Esegue Design Space Exploration                      │     │
│     │  → Calcola Pareto frontier + ranking                    │     │
│     │  → Output: DSE Artifact (risultati computazionali)      │     │
│     └─────────────────────────────────────────────────────────┘     │
│                              ↓                                      │
│     ┌─────────────────────────────────────────────────────────┐     │
│     │  Nodo 6: compose_node  🦑 TENTACOLO (VEE Engine)        │     │
│     │  → Genera narrativa esplicativa (3 livelli)             │     │
│     │  → Summary (semplice) → Detailed → Technical            │     │
│     └─────────────────────────────────────────────────────────┘     │
│                              ↓                                      │
│     ┌─────────────────────────────────────────────────────────┐     │
│     │  Nodo 7: vault_node  🦑 TENTACOLO (Archiviazione)       │     │
│     │  → Archivia tutto per audit trail                       │     │
│     │  → Immutabile, con hash crittografico                   │     │
│     └─────────────────────────────────────────────────────────┘     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  FASE 5: OUTPUT                                                     │
│  ══════════════                                                     │
│                                                                     │
│  📊 Risposta strutturata:                                           │
│     • Ranking dei design points                                     │
│     • Pareto frontier (trade-offs ottimali)                         │
│     • Narrativa esplicativa (perché questa decisione)               │
│     • Audit trail completo (per compliance)                         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.3 Schema Mermaid del Flusso Vitruvyan

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#1a1a2e', 'primaryTextColor': '#fff'}}}%%

flowchart TB
    subgraph EXTERNAL["🌍 MONDO ESTERNO"]
        DOC["📄 Documento"]
        IMG["🖼️ Immagine"]
        AUD["🎵 Audio"]
        VID["🎬 Video"]
    end

    subgraph INTAKE["📥 FASE 1: INTAKE<br/>(Pre-Epistemico)"]
        IA["Intake Agents<br/><i>Acquisizione + Normalizzazione</i>"]
        EP["Evidence Pack<br/><i>Pacchetto Immutabile</i>"]
    end

    subgraph CODEX["🔍 FASE 2: CODEX HUNTERS<br/>(Arricchimento)"]
        EH["EventHunter<br/><i>Listener Eventi</i>"]
        EMB["Embeddings<br/><i>Vettori Semantici</i>"]
    end

    subgraph BRIDGE["🌉 FASE 3: BRIDGE"]
        BR["IntakeDSEBridge<br/><i>Collega Intake → LangGraph</i>"]
    end

    subgraph LANGGRAPH["🧠 FASE 4: LANGGRAPH<br/>(Cervello)"]
        PARSE["parse_node"]
        INTENT["intent_detection"]
        PW["pattern_weavers 🦑"]
        ORTHO["orthodoxy_gate 🛡️"]
        DSE["dse_node 🦑"]
        COMPOSE["compose_node 🦑"]
        VAULT["vault_node 🦑"]
    end

    subgraph OUTPUT["📤 FASE 5: OUTPUT"]
        RESULT["Ranking + Narrativa + Audit"]
    end

    subgraph BUS["🍄 COGNITIVE BUS<br/>(Rete Miceliare)"]
        E1[/"intake.evidence.created"/]
        E2[/"codex.evidence.indexed"/]
        E3[/"langgraph.intake.ready"/]
        E4[/"dse.completed"/]
    end

    DOC --> IA
    IMG --> IA
    AUD --> IA
    VID --> IA
    
    IA --> EP
    EP --> E1
    E1 --> EH
    EH --> EMB
    EMB --> E2
    E2 --> BR
    BR --> E3
    E3 --> PARSE
    
    PARSE --> INTENT --> PW --> ORTHO --> DSE --> COMPOSE --> VAULT
    
    VAULT --> RESULT
    DSE --> E4

    classDef external fill:#74b9ff,color:#2d3436
    classDef intake fill:#a29bfe,color:#fff
    classDef codex fill:#fd79a8,color:#fff
    classDef bridge fill:#fdcb6e,color:#2d3436
    classDef brain fill:#6c5ce7,color:#fff
    classDef output fill:#00b894,color:#fff
    classDef bus fill:#636e72,color:#fff

    class DOC,IMG,AUD,VID external
    class IA,EP intake
    class EH,EMB codex
    class BR bridge
    class PARSE,INTENT,PW,ORTHO,DSE,COMPOSE,VAULT brain
    class RESULT output
    class E1,E2,E3,E4 bus
```

### 2.4 La Catena Epistemica di Vitruvyan

Vitruvyan implementa una **catena epistemica** rigida che trasforma informazioni grezze in decisioni vincolanti:

```
INTAKE → CODEX → PATTERN_WEAVERS → CONTRACT → KERNEL → EXPLAINABILITY
  │        │           │              │          │            │
  │        │           │              │          │            │
  ▼        ▼           ▼              ▼          ▼            ▼
Grezzo → Arricchito → Ipotesi → Validato → Calcolato → Spiegato
         (embeddings)  (non      (binding)  (ranking)  (narrativa)
                      binding)
```

| Fase | Componente | Input | Output | Vincolante? |
|------|------------|-------|--------|-------------|
| 1 | Intake | File raw | Evidence Pack | ❌ No |
| 2 | Codex Hunters | Evidence Pack | Embeddings | ❌ No |
| 3 | Pattern Weavers | Evidence | SemanticHypothesis | ❌ No |
| 4 | Orthodoxy Gate | Hypothesis | ApprovedKernelInput | ✅ SÌ |
| 5 | DSE Kernel | Approved Input | Ranking + Pareto | ✅ SÌ |
| 6 | VEE | Ranking | Narrativa | ✅ SÌ |

**Principio chiave**: Solo dopo la validazione Orthodoxy Gate le decisioni diventano vincolanti.

---

## 🔄 Parte 3: Come i Componenti Comunicano

### 3.1 La Rete Miceliare (Cognitive Bus)

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  Nei funghi, i miceli sono filamenti che:                           │
│  • Connettono alberi diversi nella foresta                          │
│  • Trasportano nutrienti e segnali chimici                          │
│  • Non hanno un nodo centrale                                       │
│  • Se un filamento muore, la rete si auto-ripara                   │
│                                                                     │
│  Il Cognitive Bus funziona esattamente così:                       │
│  • Connette i tentacoli (servizi)                                  │
│  • Trasporta eventi (messaggi strutturati)                         │
│  • Non ha un nodo centrale                                         │
│  • Se un canale muore, gli altri continuano                        │
│                                                                     │
│  🦑────🍄────🦑────🍄────🦑                                         │
│   │         │         │                                            │
│   🍄────────🍄────────🍄                                            │
│   │         │         │                                            │
│  🦑────🍄────🦑────🍄────🦑                                         │
│                                                                     │
│  (Ogni 🍄 è un canale Redis Stream, ogni 🦑 è un tentacolo)        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Gli Eventi Principali in Vitruvyan

| Evento | Emesso da | Consumato da | Significato |
|--------|-----------|--------------|-------------|
| `intake.evidence.created` | Intake Agent | Codex Hunters | "Ho acquisito un nuovo frammento" |
| `codex.evidence.indexed` | Codex Hunters | IntakeDSEBridge | "Ho arricchito l'evidenza con embeddings" |
| `langgraph.intake.ready` | IntakeDSEBridge | LangGraph | "L'evidenza è pronta per elaborazione" |
| `dse.completed` | DSE Node | Vault, Monitoring | "Ho completato l'esplorazione" |
| `vault.archived` | Vault Keepers | Audit System | "Ho archiviato l'evento per compliance" |

### 3.3 Perché Event-Driven?

**Domanda**: Perché usare eventi invece di chiamate dirette?

**Risposta**:

```
CHIAMATA DIRETTA (accoppiamento stretto):
─────────────────────────────────────────
Intake --chiama--> Codex --chiama--> Bridge --chiama--> LangGraph

❌ Se Codex è giù, Intake si blocca
❌ Se Bridge è lento, tutto rallenta
❌ Difficile aggiungere nuovi consumatori

───────────────────────────────────────────────────────────────────

EVENT-DRIVEN (accoppiamento lasco):
───────────────────────────────────
Intake --emette evento--> [Bus] <--ascolta-- Codex
                               <--ascolta-- Monitoring
                               <--ascolta-- Backup System

✅ Se Codex è giù, gli eventi restano in coda
✅ Posso aggiungere consumatori senza modificare Intake
✅ Ogni componente lavora al suo ritmo
```

---

## 🎯 Parte 4: Riepilogo per Stakeholder

### 4.1 Per il CTO/CIO

> *"Vitruvyan è un sistema senza single point of failure. Ogni componente opera autonomamente, comunicando attraverso una rete distribuita auto-riparante. Se un servizio cade, gli altri continuano a funzionare."*

### 4.2 Per il Compliance Officer

> *"Ogni decisione è tracciata con catena causale completa. L'Orthodoxy Gate valida ogni input prima che diventi vincolante. Il Vault Keepers archivia tutto in modo immutabile con hash crittografico."*

### 4.3 Per il Board

> *"Il sistema scala linearmente: aggiungiamo capacità senza riscrivere l'architettura. L'ispirazione biologica (polipo + funghi) non è marketing — è un principio ingegneristico che garantisce resilienza."*

### 4.4 Script per Presentazione (2 minuti)

> *"Vitruvyan funziona come un polipo.*
>
> *Il **cervello** (LangGraph) riceve la richiesta e decide cosa fare — ma non fa il lavoro.*
>
> *I **tentacoli** (Intake, Codex, Neural Engine, VEE) sono specializzati: uno acquisisce dati, uno li arricchisce, uno calcola, uno spiega. Ognuno sa fare bene una cosa sola.*
>
> *La **rete nervosa** (Cognitive Bus) permette ai tentacoli di parlare tra loro direttamente, senza passare dal cervello.*
>
> *In Vitruvyan, un documento entra come 'frammento grezzo', viene arricchito, interpretato, validato contro contratti sacri, elaborato matematicamente, e infine spiegato in linguaggio naturale.*
>
> *Ogni passaggio è tracciato. Ogni decisione è auditabile. Se un componente fallisce, gli altri continuano."*

---

## 📊 Appendice A: Schema Architetturale Completo

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#1a1a2e', 'primaryTextColor': '#eee', 'primaryBorderColor': '#7B68EE', 'lineColor': '#7B68EE', 'secondaryColor': '#16213e', 'tertiaryColor': '#0f3460'}}}%%

graph TB
    subgraph BRAIN["🧠 CERVELLO (1/3 neuroni)<br/>Governance Minima"]
        CONCLAVE["⚖️ Synaptic Conclave<br/><i>Event ID + Causal Chain</i>"]
        ORTHODOXY["🛡️ Orthodoxy Wardens<br/><i>Validation Only</i>"]
        VAULT["📦 Vault Keepers<br/><i>Immutable Archive</i>"]
    end

    subgraph STREAMS["🌊 REDIS STREAMS<br/>Mycelial Network"]
        direction LR
        S1[/"stream:intake.evidence.created"/]
        S2[/"stream:codex.evidence.indexed"/]
        S3[/"stream:langgraph.intake.ready"/]
        S4[/"stream:dse.completed"/]
        S5[/"stream:vault.archived"/]
    end

    subgraph ARM1["🦑 BRACCIO 1: Perception<br/>(Intake Modules)"]
        INTAKE["📥 Intake Agents<br/><i>Doc/Image/Audio/Video</i>"]
        CODEX["🔍 Codex Hunters<br/><i>EventHunter + Embeddings</i>"]
    end

    subgraph ARM2["🦑 BRACCIO 2: Reason<br/>(DSE Engine)"]
        DSE["🧮 DSE Neural Engine<br/><i>Pareto + Ranking</i>"]
        PW["🕸️ Pattern Weavers<br/><i>Semantic Hypotheses</i>"]
    end

    subgraph ARM3["🦑 BRACCIO 3: Discourse<br/>(Explainability)"]
        VEE["💬 VEE Engine<br/><i>3-Level Narrative</i>"]
        LANGGRAPH["🔀 LangGraph<br/><i>16-Node Orchestration</i>"]
    end

    subgraph ARM4["🦑 BRACCIO 4: Memory<br/>(Dual Storage)"]
        POSTGRES[("🗄️ PostgreSQL<br/><i>Evidence + Audit</i>")]
        QDRANT[("🔮 Qdrant<br/><i>Embeddings</i>")]
    end

    %% Connections
    INTAKE -->|"emit"| S1
    S1 -->|"consume"| CODEX
    CODEX -->|"emit"| S2
    S2 -->|"consume"| LANGGRAPH
    LANGGRAPH -->|"call"| PW
    LANGGRAPH -->|"call"| DSE
    LANGGRAPH -->|"call"| VEE
    DSE -->|"emit"| S4
    VAULT -->|"emit"| S5
    
    CODEX -->|"write"| QDRANT
    VAULT -->|"write"| POSTGRES
    DSE -->|"read"| POSTGRES

    classDef brain fill:#4a0080,stroke:#9d4edd,stroke-width:3px,color:#fff
    classDef stream fill:#1a5f7a,stroke:#57c5b6,stroke-width:2px,color:#fff
    classDef consumer fill:#16213e,stroke:#e94560,stroke-width:1px,color:#fff
    classDef storage fill:#0f3460,stroke:#00d9ff,stroke-width:2px,color:#fff

    class CONCLAVE,ORTHODOXY,VAULT brain
    class S1,S2,S3,S4,S5 stream
    class INTAKE,CODEX,DSE,PW,VEE,LANGGRAPH consumer
    class POSTGRES,QDRANT storage
```

