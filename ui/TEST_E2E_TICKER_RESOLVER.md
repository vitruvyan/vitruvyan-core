# 🧪 Test E2E - TickerResolverUI Integration

**Data**: 22 Novembre 2025  
**Branch**: graph-simplification-v1  
**Server**: http://localhost:3002

---

## ✅ Setup Completato

### 1. **Struttura /lib/**
- ✅ `/lib/types/graph.ts` - TypeScript interfaces (GraphFinalState)
- ✅ `/lib/utils/apiClient.ts` - runGraph() type-safe API client
- ✅ `/lib/utils/formatters.ts` - formatScore(), formatZScore(), etc.
- ✅ `/lib/utils/nodeGuards.ts` - hasTickerData(), hasSentimentData(), etc.

### 2. **Componenti /components/nodes/**
- ✅ `TickerResolverUI.jsx` - Ticker badges
- ✅ `IntentNodeUI.jsx` - Intent + horizon badges
- ✅ `SentimentNodeUI.jsx` - Sentiment z-score + labels
- ✅ `NeuralEngineUI.jsx` - Numerical panel table
- ✅ `ComposeNodeUI.jsx` - VEE narrative + explanations
- ✅ `FallbackNodeUI.jsx` - Clarification questions

### 3. **Integrazione chat.jsx**
- ✅ Import `runGraph` da apiClient
- ✅ Import tutti i node components
- ✅ Salvataggio `finalState` completo nei messaggi
- ✅ Rendering condizionale basato su `msg.finalState`
- ✅ Debug indicator (dev mode): mostra ticker count + route

---

## 🎯 Test Case

### **Query**: "analizza AAPL"

**Expected Behavior**:
1. User message appare con "analizza AAPL"
2. Processing message appare brevemente
3. AI response viene renderizzata con:
   - ✅ **Debug indicator** (verde): "final_state loaded • 1 ticker(s) • route: compose"
   - ✅ **TickerResolverUI**: Badge "AAPL" con icona TrendingUp
   - ✅ **IntentNodeUI**: Badge "Trend Analysis" + "Medium Term"
   - ✅ **SentimentNodeUI**: Sentiment label + z-score (se disponibile)
   - ✅ **NeuralEngineUI**: Tabella con composite_score, momentum_z, trend_z, vola_z
   - ✅ **ComposeNodeUI**: Narrative VEE completa

---

## 📋 Checklist Test Manuale

### Pre-test
- [x] Server Next.js running su localhost:3002
- [x] Backend API disponibile su 161.97.140.157:8004
- [x] No errori di compilazione
- [x] Browser aperto (Chrome/Firefox/Safari)

### Durante il Test
- [ ] Aprire http://localhost:3002
- [ ] Verificare che landing page appaia correttamente
- [ ] Cliccare input bar o premere invio
- [ ] Digitare "analizza AAPL"
- [ ] Premere invio
- [ ] Verificare che query venga inviata (console network)
- [ ] Attendere risposta backend (~2-3 secondi)

### Verifica Rendering
- [ ] **Debug indicator** visibile (dev mode) con dati corretti
- [ ] **TickerResolverUI** renderizzato con badge "AAPL"
- [ ] **IntentNodeUI** mostra "Trend Analysis"
- [ ] **SentimentNodeUI** appare (se sentiment_z disponibile)
- [ ] **NeuralEngineUI** mostra tabella con score
- [ ] **ComposeNodeUI** mostra narrative VEE

### Verifiche Console (F12)
\`\`\`javascript
// Nel browser, dopo risposta AI:
// 1. Ispeziona messaggio AI
document.querySelector('[class*="text-sm text-gray-800 space-y-4"]')

// 2. Verifica finalState object
// (dovrebbe contenere: tickers, intent, horizon, numerical_panel, narrative)

// 3. Controlla errori console
// (non dovrebbero esserci errori React)
\`\`\`

---

## 🐛 Troubleshooting

### Scenario 1: Componenti non appaiono
**Causa**: `msg.finalState` è `undefined`  
**Debug**:
\`\`\`javascript
// Aggiungi console.log in chat.jsx dopo runGraph:
console.log("[DEBUG] finalState:", finalState)
console.log("[DEBUG] tickers:", finalState.tickers)
\`\`\`

### Scenario 2: Backend non risponde
**Causa**: Timeout o backend down  
**Debug**:
\`\`\`bash
# Verifica backend health
curl http://161.97.140.157:8004/sacred-health

# Verifica endpoint /run
curl -X POST http://161.97.140.157:8004/run \
  -H "Content-Type: application/json" \
  -d '{"input_text": "analizza AAPL", "user_id": "test"}'
\`\`\`

### Scenario 3: TickerResolverUI non renderizza
**Causa**: `msg.finalState.tickers` è vuoto  
**Debug**:
\`\`\`javascript
// Nel componente, aggiungi:
console.log("[TickerResolverUI] props:", { tickers })
\`\`\`

### Scenario 4: Errore "Cannot find module @/lib/utils/apiClient"
**Causa**: Path alias non configurato  
**Fix**: Verificare `jsconfig.json` ha:
\`\`\`json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./*"]
    }
  }
}
\`\`\`

---

## 📊 Expected Console Output

### Success Case
\`\`\`
[Chat] Submit triggered: analizza AAPL
[Intent] Analyzing words: ["analizza", "AAPL"]
[Intent] → ANALYTICAL MODE (tickers: AAPL)
[Intent] Calling backend API /run...
[DEBUG] finalState: { tickers: ["AAPL"], intent: "trend", ... }
✅ Message added with finalState
\`\`\`

### Error Case
\`\`\`
[Chat] Submit triggered: analizza AAPL
API Error: Network error: Failed to fetch
⚠️ Analysis failed. Please check your connection to the server.
\`\`\`

---

## 🚀 Next Steps After Test

### Se Test PASS ✅
1. Commit changes: "✅ TickerResolverUI integration working"
2. Procedere con Punto 4: Creare `/components/panels/`
3. Testare multi-ticker: "analizza AAPL e TSLA"

### Se Test FAIL ❌
1. Raccogliere console logs
2. Verificare network tab (DevTools)
3. Controllare `finalState` object structure
4. **NON modificare backend** - aggiustare solo frontend

---

## 📸 Screenshot Checklist

Per documentazione:
- [ ] Landing page (before submit)
- [ ] Chat con "analizza AAPL" (user message)
- [ ] AI response con tutti i node components visibili
- [ ] Debug indicator (zoom su badge verde)
- [ ] Console logs (no errors)

---

**Status**: ⏳ IN ATTESA DI TEST BROWSER  
**Tester**: Caravaggio  
**Durata attesa**: 5-10 minuti
