# 🔧 VITRUVYAN UI - CONSOLIDAMENTO FINALE
## Prompt per Agenti di Esecuzione

---

# 📋 CONTESTO STRATEGICO (TUTTI GLI AGENTI)

## Principio Architetturale Fondante (NON NEGOZIABILE)

```
Vitruvyan non cresce aggiungendo componenti, cresce aggiungendo adapter.
```

- Ogni **adapter** = una UX completa per un tipo di domanda/intento utente
- I **componenti** non sono feature, sono strumenti
- Il **renderer finale** (`VitruvyanResponseRenderer`) non deve cambiare nel tempo
- La **scalabilità** = aggiungere nuovi adapter senza toccare il core

**Metafora**: L'UI è un framework. Gli adapter sono le applicazioni.

## Vincoli Operativi

| ✅ FARE | ❌ NON FARE |
|---------|-------------|
| Spostare file | Aggiungere feature |
| Aggiornare import | Modificare logica |
| Creare index.js | Aggiungere if/else |
| Rimuovere duplicati | Anticipare feature future |
| Verificare build | Essere creativi |

**Mantra**: Pulizia, non creatività.

## Regole di Esecuzione

1. **Prima di ogni fase**: `git status` deve essere pulito
2. **Dopo ogni fase**: `npm run build` DEVE passare
3. **Se build fallisce**: FIX prima di procedere
4. **Commit atomici**: Ogni fase = 1 commit con prefisso `refactor:`

---

# 🅰️ AGENT-A: FILE SYSTEM + MOVES

## Missione
Creare la struttura directory definitiva e spostare i file nelle nuove posizioni semantiche.

## Fasi Assegnate
- **1.1** Creazione directory structure
- **1.2** Spostamento Charts → analytics/charts/
- **1.3** Spostamento componenti root → analytics/panels/
- **2.1** Creazione index centralizzato analytics/
- **2.2** Spostamento chart da comparison/

## Dipendenze
- **Nessuna dipendenza in ingresso** (puoi partire subito)
- **AGENT-B dipende da te** (deve aspettare 1.1)
- **AGENT-C dipende da te** (deve aspettare 1.2, 1.3)

---

## FASE 1.1: Creazione directory structure
**Tempo**: 5 min | **Rischio build**: ZERO

### Comandi
```bash
cd /home/caravaggio/vitruvyan/vitruvyan-ui

mkdir -p components/analytics/charts
mkdir -p components/analytics/panels
mkdir -p components/explainability/vee
mkdir -p components/explainability/tooltips
mkdir -p components/explainability/badges
mkdir -p components/deprecated/composites
mkdir -p components/deprecated/comparison
mkdir -p components/utils
```

### Verifica
```bash
ls -la components/ | grep -E "analytics|explainability|deprecated|utils"
# Deve mostrare le 4 nuove cartelle
```

### Commit
```bash
git add -A
git commit -m "refactor: [1.1] create semantic directory structure"
```

---

## FASE 1.2: Spostamento Charts → analytics/charts/
**Tempo**: 10 min | **Rischio build**: BASSO

### Azioni

1. **Spostare tutti i chart**:
```bash
mv components/charts/*.jsx components/analytics/charts/
mv components/charts/README.md components/analytics/charts/ 2>/dev/null || true
```

2. **Creare index.js**:
```bash
cat > components/analytics/charts/index.js << 'EOF'
// analytics/charts/index.js - Centralized chart exports
export { default as CandlestickChart } from './CandlestickChart'
export { default as ComparativeRadarChart } from './ComparativeRadarChart'
export { default as CompositeBarChart } from './CompositeBarChart'
export { default as CompositeScoreGauge } from './CompositeScoreGauge'
export { default as FactorRadarChart } from './FactorRadarChart'
export { default as MetricsHeatmap } from './MetricsHeatmap'
export { default as MiniRadarGrid } from './MiniRadarGrid'
export { default as RiskBreakdownChart } from './RiskBreakdownChart'
export { default as RiskRewardScatter } from './RiskRewardScatter'
EOF
```

3. **Trovare e aggiornare import**:
```bash
# Trova tutti i file che importano da charts/
grep -r "from.*['\"].*charts/" --include="*.jsx" --include="*.js" components/
```

4. **Aggiornare ogni import trovato**:
   - `from '../charts/...'` → `from '../analytics/charts/...'`
   - `from '@/components/charts/...'` → `from '@/components/analytics/charts/...'`

### Verifica
```bash
npm run build
# Deve passare senza errori
```

### Commit
```bash
git add -A
git commit -m "refactor: [1.2] move charts to analytics/charts"
```

---

## FASE 1.3: Spostamento componenti root → analytics/panels/
**Tempo**: 10 min | **Rischio build**: BASSO

### Azioni

1. **Spostare FundamentalsPanel**:
```bash
mv components/FundamentalsPanel.jsx components/analytics/panels/
```

2. **Spostare e rinominare VAREPanel**:
```bash
mv components/VAREPanel.jsx components/analytics/panels/RiskPanel.jsx
```

3. **Creare index.js**:
```bash
cat > components/analytics/panels/index.js << 'EOF'
// analytics/panels/index.js - Panel exports
export { default as FundamentalsPanel } from './FundamentalsPanel'
export { default as RiskPanel } from './RiskPanel'
EOF
```

4. **Trovare e aggiornare import**:
```bash
# FundamentalsPanel
grep -r "FundamentalsPanel" --include="*.jsx" --include="*.js" components/

# VAREPanel (ora RiskPanel)
grep -r "VAREPanel" --include="*.jsx" --include="*.js" components/
```

5. **Aggiornare import**:
   - `from './FundamentalsPanel'` → `from './analytics/panels/FundamentalsPanel'`
   - `from './VAREPanel'` → `from './analytics/panels/RiskPanel'`agent D
   - Aggiornare anche il nome del componente se importato come `VAREPanel`

### Verifica
```bash
npm run build
```

### Commit
```bash
git add -A
git commit -m "refactor: [1.3] move panels to analytics/panels"
```

---

## FASE 2.1: Creazione index centralizzato analytics/
**Tempo**: 5 min | **Rischio build**: ZERO

### Azioni

```bash
cat > components/analytics/index.js << 'EOF'
// analytics/index.js - Unified analytics exports
// Charts
export * from './charts'

// Panels
export * from './panels'
EOF
```

### Verifica
```bash
# Test import (in Node REPL o file temporaneo)
npm run build
```

### Commit
```bash
git add -A
git commit -m "refactor: [2.1] create analytics index"
```

---

## FASE 2.2: Spostamento chart da comparison/
**Tempo**: 5 min | **Rischio build**: BASSO

### Azioni

1. **Spostare NormalizedPerformanceChart**:
```bash
mv components/comparison/NormalizedPerformanceChart.jsx components/analytics/charts/
```

2. **Aggiornare index.js**:
```bash
# Aggiungere export a components/analytics/charts/index.js
echo "export { default as NormalizedPerformanceChart } from './NormalizedPerformanceChart'" >> components/analytics/charts/index.js
```

3. **Aggiornare import**:
```bash
grep -r "NormalizedPerformanceChart" --include="*.jsx" --include="*.js" components/
# Aggiornare tutti i path trovati
```

### Verifica
```bash
npm run build
```

### Commit
```bash
git add -A
git commit -m "refactor: [2.2] move NormalizedPerformanceChart to analytics"
```

---

## Segnale di Completamento

Quando hai finito tutte le fasi:
1. Verifica build finale: `npm run build`
2. Notifica: **"AGENT-A COMPLETATO - analytics/ pronto"**
3. AGENT-B e AGENT-C possono procedere

---

# 🅱️ AGENT-B: EXPLAINABILITY CONSOLIDATION

## Missione
Consolidare tutto ciò che riguarda "spiegazione" in un unico dominio semantico: `explainability/`.

## Fasi Assegnate
- **3.1** Spostamento vee/ → explainability/vee/
- **3.2** Spostamento tooltips/ → explainability/tooltips/
- **3.3** Spostamento badges → explainability/badges/
- **3.4** Eliminazione vecchia explainability/ e creazione index

## Dipendenze
- **Dipendi da AGENT-A fase 1.1** (directory deve esistere)
- **AGENT-C dipende da te** (fase 3.1 per VEE utils)

## Principio Guida
```
La spiegazione è un LAYER, non un dettaglio.
Tutto ciò che risponde a "perché Vitruvyan dice questo?" vive qui.
```

---

## FASE 3.1: Spostamento vee/ → explainability/vee/
**Tempo**: 10 min | **Rischio build**: MEDIO

### ⚠️ ATTENZIONE
Questa fase ha MOLTI import da aggiornare. Procedi con attenzione.

### Azioni

1. **Spostare tutti i file vee/**:
```bash
mv components/vee/*.jsx components/explainability/vee/
```

2. **Spostare vee-report.jsx dal root**:
```bash
mv components/vee-report.jsx components/explainability/vee/VeeReport.jsx
```

3. **Creare index.js**:
```bash
cat > components/explainability/vee/index.js << 'EOF'
// explainability/vee/index.js - VEE Engine UI Components
export { default as VEEAccordions } from './VEEAccordions'
export { default as VeeBadge } from './VeeBadge'
export { default as VeeAnnotation } from './VeeAnnotation'
export { default as VeeLayer } from './VeeLayer'
export { default as VeeReport } from './VeeReport'
EOF
```

4. **Trovare TUTTI gli import da aggiornare**:
```bash
grep -r "from.*vee/" --include="*.jsx" --include="*.js" components/
grep -r "from.*VEEAccordions" --include="*.jsx" --include="*.js" components/
grep -r "from.*VeeBadge" --include="*.jsx" --include="*.js" components/
grep -r "from.*vee-report" --include="*.jsx" --include="*.js" components/
```

5. **Aggiornare OGNI import trovato**:
   - `from '../vee/VEEAccordions'` → `from '../explainability/vee/VEEAccordions'`
   - `from '@/components/vee/VeeBadge'` → `from '@/components/explainability/vee/VeeBadge'`
   - `from './vee-report'` → `from './explainability/vee/VeeReport'`

### Verifica
```bash
npm run build
# DEVE passare prima di procedere
```

### Commit
```bash
git add -A
git commit -m "refactor: [3.1] consolidate vee into explainability/vee"
```

---

## FASE 3.2: Spostamento tooltips/ → explainability/tooltips/
**Tempo**: 10 min | **Rischio build**: MEDIO

### Azioni

1. **Spostare file**:
```bash
mv components/tooltips/TooltipLibrary.jsx components/explainability/tooltips/
mv components/tooltips/README.md components/explainability/tooltips/ 2>/dev/null || true
```

2. **Spostare TooltipToggle se esiste in controls/**:
```bash
mv components/controls/TooltipToggle.jsx components/explainability/tooltips/ 2>/dev/null || true
# Oppure da explainability/ vecchia
mv components/explainability/TooltipToggle.jsx components/explainability/tooltips/ 2>/dev/null || true
```

3. **Creare index.js**:
```bash
cat > components/explainability/tooltips/index.js << 'EOF'
// explainability/tooltips/index.js - Unified Tooltip System
export * from './TooltipLibrary'
// export { default as TooltipToggle } from './TooltipToggle'  // Uncomment if exists
EOF
```

4. **Trovare e aggiornare import**:
```bash
grep -r "from.*tooltips/" --include="*.jsx" --include="*.js" components/
grep -r "TooltipLibrary" --include="*.jsx" --include="*.js" components/
```

5. **Aggiornare import**:
   - `from '../tooltips/TooltipLibrary'` → `from '../explainability/tooltips/TooltipLibrary'`
   - `from '@/components/tooltips/TooltipLibrary'` → `from '@/components/explainability/tooltips/TooltipLibrary'`

### Verifica
```bash
npm run build
```

### Commit
```bash
git add -A
git commit -m "refactor: [3.2] consolidate tooltips into explainability/tooltips"
```

---

## FASE 3.3: Spostamento badges → explainability/badges/
**Tempo**: 5 min | **Rischio build**: BASSO

### Azioni

1. **Spostare VerdictGaugeBadge**:
```bash
# Potrebbe essere in explainability/ vecchia o altrove
mv components/explainability/VerdictGaugeBadge.jsx components/explainability/badges/ 2>/dev/null || true
```

2. **Creare index.js**:
```bash
cat > components/explainability/badges/index.js << 'EOF'
// explainability/badges/index.js - Semantic Badges
export { default as VerdictGaugeBadge } from './VerdictGaugeBadge'
EOF
```

3. **Aggiornare import se necessario**:
```bash
grep -r "VerdictGaugeBadge" --include="*.jsx" --include="*.js" components/
```

### Verifica
```bash
npm run build
```

### Commit
```bash
git add -A
git commit -m "refactor: [3.3] consolidate badges into explainability/badges"
```

---

## FASE 3.4: Pulizia e index finale explainability/
**Tempo**: 5 min | **Rischio build**: BASSO

### Azioni

1. **Verificare file rimasti nella vecchia explainability/**:
```bash
ls components/explainability/*.jsx 2>/dev/null
```

2. **Per ogni file trovato, decidere**:
   - `ZScoreTooltip.jsx` → Se duplicato di TooltipLibrary, spostare in `deprecated/`
   - Altri file → Spostare nella sottocartella appropriata

3. **Creare index.js principale**:
```bash
cat > components/explainability/index.js << 'EOF'
// explainability/index.js - Unified Explainability Layer
// "Everything that answers: WHY does Vitruvyan say this?"

export * from './vee'
export * from './tooltips'
export * from './badges'
EOF
```

4. **Rimuovere cartelle vuote originali**:
```bash
rmdir components/vee 2>/dev/null || true
rmdir components/tooltips 2>/dev/null || true
```

### Verifica
```bash
npm run build
```

### Commit
```bash
git add -A
git commit -m "refactor: [3.4] finalize explainability structure"
```

---

## Segnale di Completamento

Quando hai finito:
1. Verifica build: `npm run build`
2. Notifica: **"AGENT-B COMPLETATO - explainability/ consolidato"**
3. AGENT-C può procedere con fase 4.1

---

# 🅲 AGENT-C: REFACTORING PANELS

## Missione
Semplificare `FundamentalsPanel` e `RiskPanel` rimuovendo logica duplicata e estraendo VEE logic.

## Fasi Assegnate
- **4.1** Estrazione VEE logic da FundamentalsPanel
- **4.2** Rimozione funzioni duplicate da FundamentalsPanel
- **4.3** Stesso trattamento per RiskPanel

## Dipendenze
- **Dipendi da AGENT-A** (fasi 1.2, 1.3 - analytics/ deve esistere)
- **Dipendi da AGENT-B** (fase 3.1 - explainability/vee/ deve esistere)
- **AGENT-D dipende da te** (aspetta che tu finisca)

## Principio Guida
```
I Panel devono essere "orchestratori stupidi":
- Nessuna logica duplicata
- Nessuna explainability inline
- Solo composizione di cards, charts e VEE
```

---

## FASE 4.1: Estrazione VEE logic da FundamentalsPanel
**Tempo**: 20 min | **Rischio build**: MEDIO

### Obiettivo
Estrarre la funzione `getVeeExplanations()` (circa 70 righe) in un file dedicato.

### Azioni

1. **Leggere il file attuale**:
```bash
cat components/analytics/panels/FundamentalsPanel.jsx | head -150
```

2. **Creare il file VEE strategy**:
```bash
cat > components/explainability/vee/fundamentalsVEE.js << 'EOF'
/**
 * VEE Explanations for Fundamental Metrics
 * Extracted from FundamentalsPanel.jsx for separation of concerns
 * 
 * @module explainability/vee/fundamentalsVEE
 */

/**
 * Generate VEE explanations for fundamental metrics
 * @param {string} metricKey - Metric key (e.g., "revenue_growth_yoy_z")
 * @param {number|null} value - Z-score value
 * @param {Object} explainability - VEE explainability object from API
 * @returns {{simple: string, technical: string}} VEE explanations
 */
export function getVeeExplanations(metricKey, value, explainability) {
  // Metric display names
  const metricNames = {
    'revenue_growth_yoy_z': 'Revenue Growth',
    'eps_growth_yoy_z': 'EPS Growth',
    'net_margin_z': 'Net Margin',
    'debt_to_equity_z': 'Debt/Equity',
    'free_cash_flow_z': 'Free Cash Flow',
    'dividend_yield_z': 'Dividend Yield'
  }
  
  const metricName = metricNames[metricKey] || metricKey
  
  // Generate simple interpretation
  let simple = `${metricName}: `
  if (value === null || value === undefined) {
    simple += 'No data available'
  } else if (value > 1.5) {
    simple += 'Exceptional performance (top 7%)'
  } else if (value > 1.0) {
    simple += 'Strong performance (top quartile)'
  } else if (value > 0.5) {
    simple += 'Above average performance'
  } else if (value > -0.5) {
    simple += 'Average performance'
  } else if (value > -1.0) {
    simple += 'Below average performance'
  } else {
    simple += 'Weak performance (bottom quartile)'
  }
  
  // Generate technical explanation
  let technical = ''
  if (value !== null && value !== undefined) {
    const percentile = Math.round(50 + value * 15)
    const zScore = `${value >= 0 ? '+' : ''}${value.toFixed(2)}`
    
    // Metric-specific technical explanations
    const technicalTemplates = {
      'revenue_growth_yoy_z': `Revenue growth z-score ${zScore} (${percentile}th percentile). ${value > 1 ? 'Exceptional growth indicates strong demand and scaling.' : value < -1 ? 'Lower growth may signal market saturation.' : 'Growth in line with market expectations.'}`,
      'eps_growth_yoy_z': `EPS growth z-score ${zScore} (${percentile}th percentile). ${value > 1 ? 'Strong EPS growth signals operational leverage.' : value < -1 ? 'Declining EPS may result from margin compression.' : 'EPS growth stable relative to peers.'}`,
      'net_margin_z': `Net margin z-score ${zScore} (${percentile}th percentile). ${value > 1 ? 'High margins indicate pricing power.' : value < -1 ? 'Low margins may reflect competitive pressure.' : 'Margins stable relative to peers.'}`,
      'debt_to_equity_z': `Debt/Equity z-score ${zScore} (inverted: higher = less debt, ${percentile}th percentile). ${value > 1 ? 'Low leverage provides financial flexibility.' : value < -1 ? 'High leverage amplifies risk.' : 'Leverage in line with industry.'}`,
      'free_cash_flow_z': `FCF z-score ${zScore} (${percentile}th percentile). ${value > 1 ? 'Strong FCF enables dividends and buybacks.' : value < -1 ? 'Weak FCF may force external financing.' : 'FCF generation stable.'}`,
      'dividend_yield_z': `Dividend yield z-score ${zScore} (${percentile}th percentile). ${value > 1 ? 'High yield attracts income investors.' : value < -1 ? 'Low yield suggests growth reinvestment.' : 'Yield in line with sector.'}`
    }
    
    technical = technicalTemplates[metricKey] || `Z-score: ${zScore} (${percentile}th percentile)`
  }
  
  // Override with API explainability if available
  if (explainability?.detailed?.ranking?.stocks?.[0]?.explainability?.fundamentals?.[metricKey]) {
    const veeData = explainability.detailed.ranking.stocks[0].explainability.fundamentals[metricKey]
    if (veeData.simple) simple = veeData.simple
    if (veeData.technical) technical = veeData.technical
  }
  
  return { simple, technical }
}
EOF
```

3. **Aggiornare export in index.js**:
```bash
echo "export { getVeeExplanations } from './fundamentalsVEE'" >> components/explainability/vee/index.js
```

4. **Modificare FundamentalsPanel.jsx**:
   - Rimuovere la funzione `getVeeExplanations` inline (circa righe 75-145)
   - Aggiungere import in cima:
   ```javascript
   import { getVeeExplanations } from '@/components/explainability/vee/fundamentalsVEE'
   ```

### Verifica
```bash
npm run build
# Testare che FundamentalsPanel renderizzi correttamente
```

### Commit
```bash
git add -A
git commit -m "refactor: [4.1] extract VEE logic from FundamentalsPanel"
```

---

## FASE 4.2: Rimozione funzioni duplicate da FundamentalsPanel
**Tempo**: 15 min | **Rischio build**: BASSO

### Obiettivo
Eliminare `getZScoreColor`, `getZScoreEmoji`, `formatZScore` (già presenti in ZScoreCard).

### Azioni

1. **Verificare quali funzioni sono duplicate**:
```bash
grep -n "const getZScoreColor" components/analytics/panels/FundamentalsPanel.jsx
grep -n "const getZScoreEmoji" components/analytics/panels/FundamentalsPanel.jsx
grep -n "const formatZScore" components/analytics/panels/FundamentalsPanel.jsx
```

2. **Creare utility condivisa** (se non esiste):
```bash
cat > components/utils/zscoreUtils.js << 'EOF'
/**
 * Z-Score Utilities
 * Shared formatting and styling functions for z-score display
 */

export const getZScoreColor = (z) => {
  if (z === null || z === undefined) return 'text-gray-400 bg-gray-50 border-gray-200'
  if (z > 1.5) return 'text-green-700 bg-green-50 border-green-200'
  if (z > 1.0) return 'text-green-500 bg-green-50 border-green-200'
  if (z > 0.5) return 'text-yellow-500 bg-yellow-50 border-yellow-200'
  if (z > -0.5) return 'text-blue-500 bg-blue-50 border-blue-200'
  if (z > -1.0) return 'text-orange-500 bg-orange-50 border-orange-200'
  return 'text-red-500 bg-red-50 border-red-200'
}

export const getZScoreEmoji = (z) => {
  if (z === null || z === undefined) return '—'
  if (z > 1.5) return '🚀'
  if (z > 1.0) return '✅'
  if (z > 0.5) return '👍'
  if (z > -0.5) return '😐'
  if (z > -1.0) return '⚠️'
  return '❌'
}

export const formatZScore = (z) => {
  if (z === null || z === undefined) return 'N/A'
  return z >= 0 ? `+${z.toFixed(2)}` : z.toFixed(2)
}
EOF
```

3. **Modificare FundamentalsPanel.jsx**:
   - Rimuovere le 3 funzioni duplicate
   - Aggiungere import:
   ```javascript
   import { getZScoreColor, getZScoreEmoji, formatZScore } from '@/components/utils/zscoreUtils'
   ```

4. **Verificare che il composite card usi le funzioni importate**

### Verifica
```bash
npm run build
wc -l components/analytics/panels/FundamentalsPanel.jsx
# Dovrebbe essere < 200 righe (era 297)
```

### Commit
```bash
git add -A
git commit -m "refactor: [4.2] remove duplicate functions from FundamentalsPanel"
```

---

## FASE 4.3: Stesso trattamento per RiskPanel
**Tempo**: 15 min | **Rischio build**: BASSO

### Obiettivo
Semplificare RiskPanel (ex VAREPanel) con lo stesso pattern.

### Azioni

1. **Analizzare il file**:
```bash
wc -l components/analytics/panels/RiskPanel.jsx
grep -n "const get" components/analytics/panels/RiskPanel.jsx
```

2. **Verificare che usi componenti da cards/**:
```bash
grep "from.*cards" components/analytics/panels/RiskPanel.jsx
```

3. **Se ha funzioni duplicate**, estrarre in `utils/` o usare quelle esistenti

4. **Se ha logica di explainability inline**, valutare estrazione in `explainability/`

### Verifica
```bash
npm run build
wc -l components/analytics/panels/RiskPanel.jsx
# Target: < 150 righe
```

### Commit
```bash
git add -A
git commit -m "refactor: [4.3] simplify RiskPanel to orchestrator pattern"
```

---

## Segnale di Completamento

Quando hai finito:
1. Verifica build: `npm run build`
2. Verifica dimensioni:
   - `wc -l components/analytics/panels/FundamentalsPanel.jsx` → < 200
   - `wc -l components/analytics/panels/RiskPanel.jsx` → < 150
3. Notifica: **"AGENT-C COMPLETATO - Panels semplificati"**
4. AGENT-D può procedere

---

# 🅳 AGENT-D: DEPRECATION + CLEANUP

## Missione
Completare la pulizia spostando file ridondanti in `deprecated/` e verificando la struttura finale.

## Fasi Assegnate
- **5.1** Spostamento composites ridondanti → deprecated/
- **5.2** Aggiornamento import per deprecati
- **5.3** Spostamento comparison/ cards → deprecated/
- **6.1** Riclassificazione veeAdapter
- **6.2** Pulizia cartelle vuote
- **6.3** Verifica root vuoto

## Dipendenze
- **Dipendi da TUTTI gli altri agenti** (parti per ultimo)

## Principio Guida
```
Deprecated ≠ Deleted
I file vanno in deprecated/ con commento, non eliminati.
Questo permette rollback e tracciabilità.
```

---

## FASE 5.1: Spostamento composites ridondanti → deprecated/
**Tempo**: 10 min | **Rischio build**: ZERO (solo move)

### File da deprecare
Questi componenti sono ridondanti rispetto a:
- `FundamentalsDisplay.jsx` → usa `analytics/panels/FundamentalsPanel`
- `MetricDisplay.jsx` → usa `cards/MetricCard`
- `RiskDisplay.jsx` → usa `analytics/panels/RiskPanel`

### Azioni

1. **Spostare file**:
```bash
mv components/composites/FundamentalsDisplay.jsx components/deprecated/composites/
mv components/composites/MetricDisplay.jsx components/deprecated/composites/
mv components/composites/RiskDisplay.jsx components/deprecated/composites/
```

2. **Aggiungere header deprecation a ogni file**:
```bash
for file in components/deprecated/composites/*.jsx; do
  sed -i '1i/**\n * @deprecated This component is deprecated.\n * Use the replacement indicated below.\n * Will be removed in v2.0\n *\n * FundamentalsDisplay → analytics/panels/FundamentalsPanel\n * MetricDisplay → cards/MetricCard\n * RiskDisplay → analytics/panels/RiskPanel\n */\n' "$file"
done
```

3. **Creare README in deprecated/**:
```bash
cat > components/deprecated/README.md << 'EOF'
# Deprecated Components

These components are deprecated and will be removed in v2.0.

## composites/
- `FundamentalsDisplay.jsx` → Use `analytics/panels/FundamentalsPanel`
- `MetricDisplay.jsx` → Use `cards/MetricCard`
- `RiskDisplay.jsx` → Use `analytics/panels/RiskPanel`

## comparison/
- `ComparisonNeuralEngineCard.jsx` → Use `cards/ZScoreCardMulti`

## Migration Guide
1. Update imports to new locations
2. Verify component API compatibility
3. Remove deprecated imports
EOF
```

### Verifica
```bash
ls components/deprecated/composites/
# Deve mostrare 3 file
```

### Commit
```bash
git add -A
git commit -m "refactor: [5.1] move redundant composites to deprecated"
```

---

## FASE 5.2: Aggiornamento import per deprecati
**Tempo**: 15 min | **Rischio build**: ALTO

### Azioni

1. **Trovare tutti gli usi di FundamentalsDisplay**:
```bash
grep -r "FundamentalsDisplay" --include="*.jsx" --include="*.js" components/
```

2. **Per ogni uso trovato**:
   - Se in `VitruvyanResponseRenderer.jsx` o simili:
     - Sostituire con import da `analytics/panels/FundamentalsPanel`
     - Oppure rimuovere se ridondante

3. **Trovare tutti gli usi di MetricDisplay**:
```bash
grep -r "MetricDisplay" --include="*.jsx" --include="*.js" components/
```

4. **Sostituire con MetricCard**:
   - `import { MetricDisplay }` → `import { MetricCard } from '@/components/cards/CardLibrary'`

5. **Trovare tutti gli usi di RiskDisplay**:
```bash
grep -r "RiskDisplay" --include="*.jsx" --include="*.js" components/
```

6. **Sostituire con RiskPanel**:
   - `import { RiskDisplay }` → `import { RiskPanel } from '@/components/analytics/panels'`

### Verifica
```bash
npm run build
# DEVE passare
```

### Commit
```bash
git add -A
git commit -m "refactor: [5.2] update imports for deprecated components"
```

---

## FASE 5.3: Spostamento comparison/ cards → deprecated/
**Tempo**: 10 min | **Rischio build**: BASSO

### Azioni

1. **Identificare card ridondanti in comparison/**:
```bash
ls components/comparison/
```

2. **Spostare ComparisonNeuralEngineCard** (se esiste ed è sostituito da ZScoreCardMulti):
```bash
mv components/comparison/ComparisonNeuralEngineCard.jsx components/deprecated/comparison/ 2>/dev/null || true
```

3. **Verificare altri file in comparison/**:
   - Se sono chart → dovrebbero essere già in `analytics/charts/`
   - Se sono card specifici comparison → valutare se servono ancora

### Verifica
```bash
npm run build
```

### Commit
```bash
git add -A
git commit -m "refactor: [5.3] move deprecated comparison components"
```

---

## FASE 6.1: Riclassificazione veeAdapter
**Tempo**: 5 min | **Rischio build**: BASSO

### Motivazione
`veeAdapter.js` non è un adapter (non mappa UX), è un utility per trasformare dati VEE.

### Azioni

1. **Spostare file**:
```bash
mv components/adapters/veeAdapter.js components/utils/veeUtils.js
```

2. **Aggiornare import**:
```bash
grep -r "veeAdapter" --include="*.jsx" --include="*.js" components/
```

3. **Modificare ogni import trovato**:
   - `from '../adapters/veeAdapter'` → `from '../utils/veeUtils'`
   - `from '@/components/adapters/veeAdapter'` → `from '@/components/utils/veeUtils'`

### Verifica
```bash
npm run build
```

### Commit
```bash
git add -A
git commit -m "refactor: [6.1] reclassify veeAdapter as utility"
```

---

## FASE 6.2: Pulizia cartelle vuote
**Tempo**: 2 min | **Rischio build**: ZERO

### Azioni
```bash
# Rimuovere cartelle vuote originali
rmdir components/charts 2>/dev/null && echo "Removed empty charts/" || true
rmdir components/vee 2>/dev/null && echo "Removed empty vee/" || true
rmdir components/tooltips 2>/dev/null && echo "Removed empty tooltips/" || true

# Verificare che non ci siano altre cartelle vuote
find components -type d -empty
```

### Commit
```bash
git add -A
git commit -m "refactor: [6.2] remove empty directories"
```

---

## FASE 6.3: Verifica root vuoto
**Tempo**: 5 min | **Rischio build**: ZERO

### Obiettivo
Verificare che `/components/` root contenga SOLO cartelle (nessun file .jsx orfano).

### Azioni

1. **Listare file nel root**:
```bash
ls components/*.jsx 2>/dev/null
ls components/*.js 2>/dev/null
```

2. **File PERMESSI nel root**:
   - `chat.jsx` (entry point principale - può rimanere temporaneamente)

3. **File NON PERMESSI**:
   - Qualsiasi altro .jsx → deve essere spostato nella cartella appropriata

4. **Verifica struttura finale**:
```bash
echo "=== STRUTTURA FINALE ==="
ls -la components/ | grep "^d"
echo ""
echo "=== FILE ORFANI (dovrebbe essere vuoto o solo chat.jsx) ==="
ls components/*.jsx 2>/dev/null || echo "Nessun file orfano ✅"
```

### Verifica Finale Completa
```bash
echo "=== CHECKLIST FINALE ==="
echo ""
echo "1. Build passa:"
npm run build && echo "   ✅ BUILD OK" || echo "   ❌ BUILD FAILED"
echo ""
echo "2. analytics/ struttura:"
ls components/analytics/
echo ""
echo "3. explainability/ struttura:"
ls components/explainability/
echo ""
echo "4. deprecated/ struttura:"
ls components/deprecated/
echo ""
echo "5. Panels semplificati:"
wc -l components/analytics/panels/*.jsx
echo ""
echo "6. Root pulito:"
ls components/*.jsx 2>/dev/null || echo "   ✅ NESSUN ORFANO"
```

### Commit Finale
```bash
git add -A
git commit -m "refactor: [6.3] verify clean root structure - CONSOLIDATION COMPLETE"
```

---

## Segnale di Completamento

Quando hai finito:
1. Esegui verifica finale completa (script sopra)
2. Notifica: **"AGENT-D COMPLETATO - REFACTOR TERMINATO"**
3. Invia report struttura finale

---

# ✅ CHECKLIST POST-ESECUZIONE (TUTTI GLI AGENTI)

```
[ ] Root /components/ contiene SOLO cartelle (eccetto chat.jsx)
[ ] analytics/ contiene charts/ e panels/
[ ] explainability/ contiene vee/, tooltips/, badges/
[ ] adapters/ contiene SOLO adapter puri (no veeAdapter)
[ ] deprecated/ contiene file marcati per rimozione
[ ] utils/ contiene veeUtils.js e zscoreUtils.js
[ ] npm run build passa senza errori
[ ] FundamentalsPanel < 200 righe
[ ] RiskPanel < 150 righe
[ ] Nessuna funzione duplicata tra file
```

---

# 🔄 ROLLBACK PLAN

Se qualcosa va storto durante qualsiasi fase:

```bash
# Vedere ultimo commit
git log --oneline -5

# Rollback a commit precedente
git reset --hard HEAD~1

# Oppure tornare a un commit specifico
git reset --hard <commit-hash>
```

---

**Fine documento. Questo file è la fonte di verità per l'esecuzione del refactor.**
