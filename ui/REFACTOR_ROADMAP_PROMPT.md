# VITRUVYAN UI REFACTOR — PROMPT OPERATIVO PER AI ASSISTANT

**Data**: 30 Dicembre 2025  
**Progetto**: Vitruvyan UI (Next.js 14, Tailwind CSS)  
**Obiettivo**: Consolidamento architetturale post-refactor VitruvyanResponse

---

## 🎯 CONTESTO

Vitruvyan è un AI trading advisor con frontend Next.js. È stato recentemente introdotto un modello canonico `VitruvyanResponse` con:
- Schema: `narrative` → `followUps` → `context` → `evidence`
- Adapter layer per normalizzazione
- Renderer unificato

**Problema attuale**: L'UI ha accumulato debito tecnico:
- Dead code (~1,100 linee)
- Duplicazione token (2 file)
- VEE non integrata correttamente (trattata come evidence invece che come layer semantico)
- Placeholder invece di chart reali
- Tooltip in due sistemi separati

---

## 🚫 DECISIONI NON-NEGOTIABLE

Queste decisioni sono **IRREVERSIBILI**. Non discuterle, implementale.

### 1. VEE È IL CENTRO SEMANTICO
```
VEE Summary = È LA NARRATIVE (non aggiunta ad essa)
VEE Technical + Detailed = Accordion SOTTO la narrative, PRIMA dell'evidence
```

**Schema UI definitivo**:
```
┌─────────────────────────────────────────────────┐
│  NARRATIVE (= VEE Summary)                      │
├─────────────────────────────────────────────────┤
│  ADVISOR BADGE (optional)                       │
├─────────────────────────────────────────────────┤
│  VEE ACCORDION                                  │
│  ├─ Technical (Level 2)                         │
│  └─ Detailed + Contextualized (Level 3-4)      │
├─────────────────────────────────────────────────┤
│  EVIDENCE ACCORDION                             │
│  └─ Charts, Tables                              │
└─────────────────────────────────────────────────┘
```

### 2. TOOLTIP = UN SOLO SISTEMA
- `TooltipLibrary.jsx` è l'UNICA fonte di tooltip
- `vee/VeeTooltip.jsx` va assorbito o eliminato
- I tooltip sono linguaggio, non decorazione

### 3. TOKEN = UNA SOLA FONTE
- `theme/tokens.js` è l'UNICA fonte di design tokens
- `cards/cardTokens.js` va deprecato e migrato
- Nessun colore hardcoded

### 4. NESSUN DEAD CODE
- Se non ha import, non esiste
- Il backup vive in git, non nel tree

---

## 📁 FILE DA ELIMINARE (DEAD CODE)

Questi file NON hanno import attivi. Eliminare senza discussione:

```
# Cartella explainability/ (quasi tutto)
components/explainability/VEEMultiLevelAccordion.jsx    # ~200 loc
components/explainability/PlainLanguageCards.jsx        # ~150 loc
components/explainability/SimplifiedNeuralEngineCard.jsx # ~100 loc
components/explainability/ExecutiveSummary.jsx          # ~80 loc
components/explainability/NeuralEngineTabs.jsx          # ~120 loc

# Cartella strategic-card/ (tutto)
components/strategic-card/index.js
components/strategic-card/StrategicCard.jsx
components/strategic-card/[altri file]

# Altri
components/CognitiveCLI.jsx                             # ~150 loc

# Backup file
components/chat.jsx.backup
```

**TENERE** (ha import attivo):
- `components/explainability/FundamentalsTooltip.jsx`

---

## 🎨 PALETTE COLORI — GRAMMATICA SEMANTICA

Da consolidare in `theme/tokens.js`:

```javascript
export const tokens = {
  colors: {
    // Semantica
    positive: {
      light: 'bg-green-50',
      base: 'bg-green-100', 
      dark: 'bg-green-600',
      text: 'text-green-800'
    },
    negative: {
      light: 'bg-red-50',
      base: 'bg-red-100',
      dark: 'bg-red-600', 
      text: 'text-red-800'
    },
    neutral: {
      light: 'bg-gray-50',
      base: 'bg-gray-100',
      dark: 'bg-gray-600',
      text: 'text-gray-800'
    },
    attention: {
      light: 'bg-yellow-50',
      base: 'bg-yellow-100',
      dark: 'bg-yellow-600',
      text: 'text-yellow-800'
    },
    vitruvyan: {
      light: 'bg-emerald-50',
      base: 'bg-emerald-100',
      dark: 'bg-emerald-600',
      text: 'text-emerald-800'
    },
    info: {
      light: 'bg-blue-50',
      base: 'bg-blue-100',
      dark: 'bg-blue-600',
      text: 'text-blue-800'
    },
    
    // Z-Score (già esistenti, da consolidare)
    zScore: {
      exceptional: 'green-600',  // z > 1.5
      strong: 'green-500',       // z > 1.0
      average: 'yellow-500',     // z > 0.5
      weak: 'blue-500',          // z > -0.5
      poor: 'red-500'            // z < -0.5
    }
  }
}
```

---

## 📋 ROADMAP DETTAGLIATA

### FASE P0: FONDAZIONI (Priorità massima)

#### P0.1 — Token Consolidation
**Obiettivo**: Una sola fonte di truth per i design tokens

**TODO**:
1. Leggere `cards/cardTokens.js` e `theme/tokens.js`
2. Unificare tutto in `theme/tokens.js` con la grammatica semantica sopra
3. Aggiornare tutti gli import da `cardTokens` a `tokens`
4. Eliminare `cards/cardTokens.js`
5. Verificare build

**Commit**: `refactor(tokens): unify design tokens into single source of truth`

---

#### P0.2 — Dead Code Removal
**Obiettivo**: Tree pulito, nessuna ambiguità

**TODO**:
1. Eliminare file in `explainability/` (eccetto FundamentalsTooltip.jsx)
2. Eliminare intera cartella `strategic-card/`
3. Eliminare `CognitiveCLI.jsx`
4. Eliminare `chat.jsx.backup`
5. Verificare build
6. Se cartella `explainability/` rimane con solo FundamentalsTooltip, valutare spostamento in `tooltips/`

**Commit**: `chore(cleanup): remove ~1100 lines of dead code`

---

### FASE P1: CUORE SEMANTICO (VEE Integration)

#### P1.1 — VEE Adapter
**Obiettivo**: Bridge tra VitruvyanResponse e VEEAccordions esistente

**TODO**:
1. Creare `adapters/veeAdapter.js`:
   ```javascript
   export function adaptVEEForAccordion(vitruvyanResponse) {
     // Mappa evidence.vee o vee_explanations → props VEEAccordions
   }
   ```
2. VEEAccordions.jsx NON va modificato (è maturo, 268 loc)
3. L'adapter estrae: summary, technical, detailed, contextualized

**Commit**: `feat(vee): add VEE adapter for VitruvyanResponse integration`

---

#### P1.2 — VEE come Narrative
**Obiettivo**: VEE Summary diventa la narrative principale

**TODO**:
1. In `UnifiedRenderer.jsx` o equivalente:
   - Se `vee.summary` esiste, usarlo come contenuto di NarrativeSection
   - NON concatenare, SOSTITUIRE
2. Creare `VEEAccordionWrapper.jsx` che:
   - Si posiziona DOPO narrative, PRIMA di evidence
   - Usa VEEAccordions.jsx via adapter
   - Mostra solo technical + detailed (summary è già in narrative)

**Commit**: `feat(vee): integrate VEE as semantic narrative layer`

---

### FASE P2: EVIDENZA (Charts Wiring)

#### P2.1 — Radar Chart Integration
**Obiettivo**: Sostituire placeholder con chart reale

**TODO**:
1. In `EvidenceSectionRenderer.jsx`:
   - Importare `FactorRadarChart` da `charts/`
   - Nel case `type === 'radar'`: renderizzare FactorRadarChart
   - Passare props da `section.data`
2. Verificare che FactorRadarChart accetti i props corretti

**Commit**: `feat(charts): wire FactorRadarChart to EvidenceSectionRenderer`

---

#### P2.2 — Candlestick Chart Integration
**Obiettivo**: Chart prezzi funzionante

**TODO**:
1. In `EvidenceSectionRenderer.jsx`:
   - Importare `CandlestickChart` da `charts/`
   - Nel case `type === 'candlestick'` o `type === 'price'`: renderizzare
2. Verificare props: `ticker`, `days`, `explainability`

**Commit**: `feat(charts): wire CandlestickChart to EvidenceSectionRenderer`

---

### FASE P3: RAFFINAMENTI

#### P3.1 — Tooltip Consolidation
**Obiettivo**: Un solo sistema tooltip

**TODO**:
1. Leggere `vee/VeeTooltip.jsx`
2. Verificare se logica è già in `TooltipLibrary.jsx`
   - Se sì: eliminare VeeTooltip.jsx
   - Se no: migrare logica in TooltipLibrary, poi eliminare
3. Aggiornare eventuali import
4. Verificare build

**Commit**: `refactor(tooltips): consolidate VeeTooltip into TooltipLibrary`

---

#### P3.2 — Advisor Badge Integration
**Obiettivo**: Badge azioni visibile nel flusso

**TODO**:
1. Verificare che `AdvisorNodeUI.jsx` o equivalente esista
2. Integrare nel flusso UnifiedRenderer DOPO narrative, PRIMA di VEE accordion
3. Deve mostrare: action type (buy/sell/hold/rebalance) con colore semantico

**Commit**: `feat(advisor): integrate AdvisorBadge in unified render flow`

---

## ✅ CHECKLIST FINALE

Dopo ogni fase, verificare:

```bash
# Build check
cd /home/caravaggio/vitruvyan/vitruvyan-ui && npm run build

# Se errori, fixare prima di procedere
```

### Stato atteso post-refactor:

- [ ] Un solo file token (`theme/tokens.js`)
- [ ] Zero dead code (no file senza import)
- [ ] VEE Summary = narrative principale
- [ ] VEE Accordion sotto narrative, prima di evidence
- [ ] Charts reali (no placeholder)
- [ ] Un solo sistema tooltip (TooltipLibrary)
- [ ] Build passa senza errori

---

## 🔍 FILE CHIAVE DA CONOSCERE

Prima di iniziare, leggi questi file per contesto:

```
# Schema e adapter
components/models/VitruvyanResponse.js
adapters/vitruvyanResponseAdapter.js

# Renderer principale
components/UnifiedRenderer.jsx (o equivalente orchestratore)

# VEE esistente (NON modificare, solo integrare)
components/vee/VEEAccordions.jsx

# Tooltip (fonte unica)
components/tooltips/TooltipLibrary.jsx

# Token (fonte unica dopo consolidamento)
theme/tokens.js

# Evidence renderer
components/evidence/EvidenceSectionRenderer.jsx

# Charts da integrare
components/charts/FactorRadarChart.jsx
components/charts/CandlestickChart.jsx
components/charts/ComparativeRadarChart.jsx
```

---

## ⚠️ REGOLE OPERATIVE

1. **MAI modificare VEEAccordions.jsx** — è maturo, crea adapter
2. **MAI creare nuovi file token** — usa solo tokens.js
3. **MAI creare nuovi sistemi tooltip** — usa solo TooltipLibrary
4. **SEMPRE verificare build** dopo ogni fase
5. **SEMPRE commit atomici** — un commit per task

---

## 📊 METRICHE DI SUCCESSO

| Metrica | Prima | Dopo |
|---------|-------|------|
| File token | 2 | 1 |
| Dead code (loc) | ~1,100 | 0 |
| Sistemi tooltip | 2 | 1 |
| Chart placeholder | Sì | No |
| VEE = evidence | Sì | No (è narrative) |

---

**INIZIA DA P0.1 (Token Consolidation)**
