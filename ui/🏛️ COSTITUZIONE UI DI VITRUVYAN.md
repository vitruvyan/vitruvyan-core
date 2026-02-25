 # 🏛️ COSTITUZIONE UI DI VITRUVYAN

**Principi Fondativi per un'Interfaccia Cognitiva Scalabile**

---

## PREAMBOLO

> Vitruvyan non è una dashboard.  
> Vitruvyan non è una collezione di componenti.  
> **Vitruvyan è un sistema cognitivo che dialoga con l'essere umano.**

Questa Costituzione definisce i principi immutabili che regolano la costruzione dell'interfaccia utente di Vitruvyan e di ogni suo verticale, presente o futuro.

- Ogni riga di codice UI deve essere compatibile con quanto segue.
- Ogni eccezione deve essere giustificata architettonicamente, non pragmaticamente.

---

## ARTICOLO I — SEPARAZIONE TRA PENSIERO E VISUALIZZAZIONE

La UI di Vitruvyan è divisa in due domini distinti:

1. **Dominio Cognitivo** (ragionamento, spiegazione, intenzione)
2. **Dominio Analitico** (dati, metriche, grafici)

**L'utente parla prima con il consulente, non con i dati.**

Nessun dato quantitativo può:
- interrompere la narrativa
- anticipare la spiegazione
- competere visivamente con il testo conversazionale

---

## ARTICOLO II — L'ADAPTER È L'UNITÀ DI UX

Ogni adapter rappresenta una **UX completa e autonoma**.

Un adapter:
- conosce il contesto
- decide cosa mostrare
- decide in che ordine
- decide con quale profondità

> I componenti non conoscono il contesto.  
> Gli adapter sì.

La scalabilità della UI non avviene aggiungendo componenti, ma **aggiungendo nuovi adapter**.

- La UI è un **framework**.
- Gli adapter sono le **applicazioni**.

---

## ARTICOLO III — IL RENDERER È STABILE

Il renderer finale (`VitruvyanResponseRenderer`) è **infrastruttura**, non feature.

Il renderer:
- non contiene logica di business
- non conosce il dominio
- non evolve per supportare nuove UX

> Se una nuova esigenza richiede di modificare il renderer,  
> **l'architettura è sbagliata a monte**.

---

## ARTICOLO IV — I COMPONENTI SONO STRUMENTI, NON DECISIONI

Un componente:
- visualizza
- non interpreta
- non decide
- non orchestra

I componenti:
- non devono contenere logica di dominio
- non devono duplicare formattazioni
- non devono "sapere" perché vengono usati

Ogni componente vive in un **dominio semantico chiaro**, espresso dal tree.

---

## ARTICOLO V — STRUTTURA SEMANTICA DEL TREE

Ogni cartella rappresenta un **verbo**, non un contenitore arbitrario.

| Cartella | Verbo |
|----------|-------|
| `adapters/` | trasforma |
| `response/` | renderizza |
| `composites/` | compone |
| `cards/` | mostra |
| `analytics/` | visualizza numeri |
| `explainability/` | spiega |
| `theme/` | definisce |
| `utils/` | supporta |
| `deprecated/` | conserva memoria tecnica |

> ❌ **Nessun file JSX può vivere nel root di `components/`.**

---

## ARTICOLO VI — EXPLAINABILITY È UN DOMINIO, NON UN ACCESSORIO

Tutto ciò che spiega:
- VEE
- tooltip
- badge semantici
- annotazioni

...vive in `explainability/`.

L'explainability:
- non è un dettaglio visivo
- non è opzionale
- non è delegata al singolo componente

> **La spiegazione è un layer cognitivo, non una nota a piè di pagina.**

---

## ARTICOLO VII — STRATIFICAZIONE DELL'INFORMAZIONE

Le informazioni **non vengono mostrate tutte insieme**.

Ogni risposta è stratificata:
1. Narrativa primaria
2. Explainability (VEE)
3. Dati strutturati
4. Approfondimenti opzionali

Ogni livello può essere:
- collassato
- espanso
- ignorato

> **La UI non presume competenza, la accompagna.**

---

## ARTICOLO VIII — COERENZA VISIVA COME LEGGE

Colori, font, spacing e gerarchie:
- derivano **solo dai token**
- non sono mai hardcoded

Se due risposte sembrano diverse graficamente:
- l'utente perde fiducia
- il sistema perde autorevolezza

> **La UI di Vitruvyan deve essere riconoscibile come una voce unica, come una persona coerente.**

---

## ARTICOLO IX — DEPRECAZIONE CONSAPEVOLE

Il codice **non viene cancellato**: viene deprecato.

Ogni file deprecato:
- è spostato in `deprecated/`
- è marcato chiaramente
- ha una destinazione futura (rimozione o sostituzione)

> **La memoria architetturale è un valore, non un peso.**

---

## ARTICOLO X — INVARIANZA TRA VERTICALI

Ogni verticale di Vitruvyan:
- Mercator
- Vector
- Ignis
- Caelestis
- futuri domini

...deve rispettare questa Costituzione.

**Cambiano:**
- gli adapter
- i dati
- le priorità

**Non cambia:**
- la struttura
- il flusso cognitivo
- la separazione dei ruoli

---

## ARTICOLO XI — SILENZIO PREFERIBILE ALL'AMBIGUITÀ

Vitruvyan **non mostra dati incompleti**.

Se una sezione non ha abbastanza informazioni per essere significativa:
- non viene renderizzata
- non mostra placeholder "N/A"
- non suggerisce incompletezza

> **Meglio non dire nulla che dire qualcosa di fuorviante.**

Soglie minime per sezione:
- Fundamentals: min 3 metriche
- Risk: min 2 dimensioni
- Comparison: min 2 ticker validi

---

## ARTICOLO XII — ORDINE EPISTEMICO DELLE EVIDENZE

L'ordine delle sezioni evidence **non è arbitrario**.

Riflette il modo in cui un sistema razionale valuta:

1. **Solidità** — prerequisito di sopravvivenza
2. **Redditività** — efficienza attuale
3. **Crescita** — traiettoria futura
4. **Risk** — limiti e vincoli
5. **Momentum/Trend** — segnali di mercato
6. **Sentiment** — percezione esterna

> **Senza solidità, il resto è rumore.**

Questo ordine:
- è epistemico, non grafico
- è blindato per ogni verticale
- non può essere sovrascritto da preferenze UX

---

## ARTICOLO XIII — TENSIONE EPISTEMICA

Se i dati contraddicono il verdetto, **Vitruvyan lo dichiara esplicitamente**.

La tensione epistemica:
- è rilevata dal **backend** (compose_node / decision engine)
- è comunicata alla UI come flag (`tension_detected: true`)
- è resa visibile nella narrativa e nei badge

> **La UI non inferisce, non deduce, non scopre.**
> **La UI rende visibile una decisione già presa a monte.**

Questo distingue un sistema narrativo da un sistema cognitivo.
Vitruvyan è entrambi, ma non li confonde.

---

## ARTICOLO XIV — ACCOMPAGNAMENTO, NON IMPOSIZIONE

L'utente **non decide se fidarsi** del verdetto.

Viene **accompagnato a capire** perché è ragionevole.

La struttura UI:
- non chiede fiducia cieca
- non nasconde il ragionamento
- non delega all'utente la sintesi

> **Vitruvyan spiega, non convince.**

Questo è il cuore del valore Vitruvyan.

---

## ARTICOLO XV — MICRO-SEGNALI PERCETTIVI

I badge e micro-indicatori:
- sono **segnali di stato**, non call-to-action
- usano **testo + colore**, non emoji
- sono visibili anche da sezioni collapsed

Formato standard:
- `Solidi` (verde)
- `Neutrali` (grigio)
- `In tensione` (arancio/rosso)

> **Un micro-badge è come una spia sul cruscotto: informa, non allerta.**

Questo distingue Vitruvyan dalle dashboard ansiogene.

---

## ARTICOLO XVI — LE PROVE NON SONO UN PLAYGROUND

Le sezioni evidence (Fundamentals, Risk, ecc.):
- **provano** il verdetto, non lo esplorano
- non insegnano finanza
- non invitano a confronti manuali
- non sono espandibili all'infinito

> **La sezione Fundamentals non serve a "capire i fundamentals".**
> **Serve a capire se la risposta di Vitruvyan ha fondamenta.**

---

## ARTICOLO XVII — INDICATORI AGGREGATI

Gli indicatori aggregati (es. `fundamentals_z`) sono **indicatori di coerenza**, non medie matematiche.

Un `fundamentals_z` neutro può derivare da:
- metriche tutte neutre
- metriche discordanti che si bilanciano

In entrambi i casi, il significato è: **nessuna direzione netta**.

> **L'aggregato misura la coerenza del pattern, non la somma dei valori.**

---

## CLAUSOLA FINALE

Questa Costituzione:
- precede il codice
- governa le scelte
- limita l'entropia
- abilita la scalabilità

> **Ogni violazione non giustificata è debito architetturale consapevole.**

---

---

# 📜 DECISION SHEETS

Le Decision Sheet sono documenti operativi che traducono la Costituzione in specifiche UX per ogni verticale.

---

## DECISION SHEET #1 — Single Ticker → Fundamentals

**Data**: 1 Gennaio 2026  
**Status**: 🔒 BLINDATA

### Ruolo nella UX

I Fundamentals sono la **prima prova razionale** del verdetto.

Non guidano l'azione → **giustificano la coerenza**.

### Posizione nel Flusso

```
1. Narrativa (VEE Summary)
2. Verdetto / Orientamento
3. ▶ FUNDAMENTALS ◀ (prima evidenza)
4. Risk
5. Trend / Momentum
6. Sentiment
```

### Container

| Proprietà | Valore |
|-----------|--------|
| Componente | `EvidenceAccordion` |
| Stato default | `collapsed` |
| Titolo | "Fondamentali" |
| Sottotitolo | **Dinamico** (vedi sotto) |

### Sottotitolo Dinamico

Basato su `fundamentals_z` aggregato:

| Condizione | Sottotitolo | Colore |
|------------|-------------|--------|
| `> 0.5` | "Base razionale solida" | Verde |
| `-0.5 ~ 0.5` | "Segnali misti, nessuna evidenza forte" | Grigio |
| `< -0.5` | "Attenzione: fondamentali in tensione" | Arancio |

### Micro-Badge (da collapsed)

Visibile anche quando la sezione è chiusa:

| Stato | Badge | Colore |
|-------|-------|--------|
| Positivo | `Solidi` | Verde |
| Neutro | `Neutrali` | Grigio |
| Negativo | `In tensione` | Arancio |

**Formato**: Testo + colore. NO emoji.

### Metriche — Set Definitivo (max 7)

**Ordine epistemico blindato:**

#### Cluster 1 — SOLIDITÀ (prerequisito)
| Metrica | Chiave Backend |
|---------|----------------|
| Debt / Equity | `debt_to_equity_z` |
| Free Cash Flow Consistency | `free_cash_flow_z` |

#### Cluster 2 — REDDITIVITÀ (performance)
| Metrica | Chiave Backend |
|---------|----------------|
| ROIC | `roic_z` |
| Operating Margin | `operating_margin_z` |
| Net Margin | `net_margin_z` |

#### Cluster 3 — CRESCITA (traiettoria)
| Metrica | Chiave Backend |
|---------|----------------|
| Revenue Growth | `revenue_growth_yoy_z` |
| Earnings Growth | `eps_growth_yoy_z` |

### Visualizzazione Metriche

Ogni metrica → `ZScoreCard`

| Elemento | Visibilità |
|----------|------------|
| Badge semantico (Strong/Neutral/Weak) | **Primario** |
| Z-score numerico | Solo in tooltip |
| VEE tooltip ("Perché conta") | Hover |
| VEE accordion (spiegazione estesa) | Opzionale |

### Regole di Omissione

| Regola | Comportamento |
|--------|---------------|
| Metrica null | Omessa silenziosamente |
| < 3 metriche disponibili | Sezione NON renderizzata |
| Nessun placeholder "N/A" | Mai |

### Tensione Epistemica

| Proprietà | Valore |
|-----------|--------|
| Rilevata da | Backend (`compose_node`) |
| Flag | `tension_detected: true` |
| Effetto UI | Sottotitolo rosso + icona warning |
| Requisito | Narrativa deve già contenere spiegazione |

### Responsabilità Adapter

L'adapter `singleTickerAdapter` **DEVE**:
- Selezionare le metriche rilevanti
- Normalizzarle secondo lo schema
- Fornire payload VEE per ogni metrica
- Calcolare `fundamentals_z` aggregato
- Fornire sintesi 1 riga per sottotitolo

L'adapter **NON DEVE**:
- Decidere layout
- Decidere colori
- Scrivere JSX
- Fare rendering

### Checklist di Validazione

- [ ] Ordine cluster rispettato (Solidità → Redditività → Crescita)
- [ ] Min 3 metriche presenti per renderizzare
- [ ] Sottotitolo dinamico basato su fundamentals_z
- [ ] Micro-badge testuale visibile da collapsed
- [ ] Tensione epistemica gestita se flag presente
- [ ] Nessun N/A o placeholder visibile
- [ ] Badge semantico prioritario su valore numerico

---

## 📁 Tree Base

```
components/
├── adapters/                    # 🔄 UX MAPPING (trasformazione cognitiva)
│   ├── index.js
│   ├── singleTickerAdapter.js
│   ├── comparisonAdapter.js
│   ├── conversationalAdapter.js
│   ├── portfolioAdapter.js
│   ├── allocationAdapter.js
│   └── screeningAdapter.js
│
├── response/                    # 🎯 RENDERING FINALE
│   ├── VitruvyanResponseRenderer.jsx
│   └── EvidenceSectionRenderer.jsx
│
├── composites/                  # 🧱 BLOCCHI NARRATIVI RIUTILIZZABILI
│   ├── NarrativeBlock.jsx
│   ├── FollowUpChips.jsx
│   ├── EvidenceAccordion.jsx
│   ├── IntentBadge.jsx
│   └── FallbackMessage.jsx
│
├── analytics/                   # 📊 DOMINIO QUANTITATIVO
│   ├── charts/                  # Grafici puri
│   │   ├── FactorRadarChart.jsx
│   │   ├── ComparativeRadarChart.jsx
│   │   ├── CompositeScoreGauge.jsx
│   │   ├── MetricsHeatmap.jsx
│   │   ├── RiskRewardScatter.jsx
│   │   ├── CandlestickChart.jsx
│   │   ├── CompositeBarChart.jsx
│   │   ├── MiniRadarGrid.jsx
│   │   └── NormalizedPerformanceChart.jsx
│   │
│   └── panels/                  # Orchestratori metrici
│       ├── FundamentalsPanel.jsx
│       └── RiskPanel.jsx
│
├── explainability/              # 💡 SPIEGAZIONE E CONTESTO
│   ├── vee/                     # Explainability Engine
│   │   ├── VEEAccordions.jsx
│   │   ├── VeeBadge.jsx
│   │   ├── VeeAnnotation.jsx
│   │   ├── VeeLayer.jsx
│   │   ├── VeeReport.jsx
│   │   └── fundamentalsVEE.js
│   │
│   ├── tooltips/                # Tooltip unificati
│   │   ├── TooltipLibrary.jsx
│   │   └── TooltipToggle.jsx
│   │
│   └── badges/                  # Badge semantici
│       └── VerdictGaugeBadge.jsx
│
├── cards/                       # 🃏 COMPONENTI ATOMICI
│   ├── CardLibrary.jsx
│   ├── BaseCard.jsx
│   ├── MetricCard.jsx
│   ├── ZScoreCard.jsx
│   ├── ZScoreCardMulti.jsx
│   ├── ChartCard.jsx
│   └── AccordionCard.jsx
│
├── layouts/                     # 📐 STRUTTURE DI PAGINA
│   ├── AnalysisHeader.jsx
│   └── UnifiedLayout.jsx
│
├── controls/                    # 🎛️ CONTROLLI INTERATTIVI
│   └── ...
│
├── theme/                       # 🎨 DESIGN TOKENS
│   └── tokens.js
│
├── utils/                       # 🧰 UTILITIES PURE
│   └── veeUtils.js
│
├── deprecated/                  # 🗑️ MEMORIA ARCHITETTURALE
│   ├── composites/
│   └── comparison/
│
└── nodes/                       # 🚫 LEGACY (da eliminare progressivamente)
```
