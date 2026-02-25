# Test Piano - Nodo per Nodo

**Data:** 30 Novembre 2025  
**Obiettivo:** Verificare singolarmente ogni NodeUI per capire il flusso dati e validare cosa viene prodotto

---

## 🎯 Strategia di Test

Per ogni nodo verificheremo:
1. **Input richiesto** - Quali dati dal backend triggera questo nodo
2. **Condizioni di rendering** - Quando appare (intent/action/dati)
3. **Output visuale** - Cosa mostra all'utente
4. **Integrazione** - Come interagisce con altri nodi
5. **Debug info** - Console logs per tracciare il flusso

---

## 1. IntentNodeUI

**Scopo:** Mostra l'intent identificato dal backend

**Input atteso:**
\`\`\`javascript
finalState: {
  intent: string  // es: "ticker_analysis", "portfolio", "comparison"
}
\`\`\`

**Condizioni rendering in chat.jsx:**
\`\`\`javascript
{msg.finalState.intent && (
  <IntentNodeUI intent={msg.finalState.intent} />
)}
\`\`\`

**Test Case 1.1 - Single Ticker:**
- Query: `"analyze AAPL"`
- Expected intent: `"ticker_analysis"`
- Expected UI: Badge con intent identificato

**Test Case 1.2 - Portfolio:**
- Query: `"analizza il mio portfolio"`
- Expected intent: `"portfolio"` o `"portfolio_review"`
- Expected UI: Badge portfolio intent

**Test Case 1.3 - Comparison:**
- Query: `"compare AAPL vs MSFT"`
- Expected intent: `"comparison"`
- Expected UI: Badge comparison intent

**Verifica:**
- [ ] Intent badge appare
- [ ] Testo intent corretto
- [ ] Styling appropriato per tipo intent

---

## 2. TickerResolverUI

**Scopo:** Mostra i ticker risolti dal backend

**Input atteso:**
\`\`\`javascript
finalState: {
  ticker_name_mapping: {
    "original_query": "resolved_ticker",
    // es: "apple": "AAPL"
  }
}
\`\`\`

**Condizioni rendering in chat.jsx:**
\`\`\`javascript
{msg.finalState.ticker_name_mapping && (
  <TickerResolverUI mapping={msg.finalState.ticker_name_mapping} />
)}
\`\`\`

**Test Case 2.1 - Nome colloquiale:**
- Query: `"analyze apple"`
- Expected mapping: `{"apple": "AAPL"}`
- Expected UI: Tabella con "apple" → "AAPL"

**Test Case 2.2 - Multi-ticker:**
- Query: `"compare apple vs microsoft"`
- Expected mapping: `{"apple": "AAPL", "microsoft": "MSFT"}`
- Expected UI: Tabella con entrambi i mapping

**Test Case 2.3 - Ticker già corretto:**
- Query: `"analyze AAPL"`
- Expected: Nessun mapping (ticker già valido)
- Expected UI: TickerResolverUI non appare

**Verifica:**
- [ ] Tabella mapping appare quando necessario
- [ ] Mapping corretto mostrato
- [ ] Non appare se ticker già valido

---

## 3. SentimentNodeUI

**Scopo:** Mostra analisi sentiment del ticker

**Input atteso:**
\`\`\`javascript
finalState: {
  sentiment_analysis: {
    ticker: string,
    sentiment: "bullish" | "bearish" | "neutral",
    score: number,
    factors: Array<{factor: string, impact: string}>
  }
}
\`\`\`

**Condizioni rendering in chat.jsx:**
\`\`\`javascript
{msg.finalState.sentiment_analysis && (
  <SentimentNodeUI sentimentData={msg.finalState.sentiment_analysis} />
)}
\`\`\`

**Test Case 3.1 - Sentiment positivo:**
- Query: `"analyze AAPL"`
- Expected sentiment: `"bullish"`
- Expected UI: Badge verde, score >0, fattori positivi

**Test Case 3.2 - Sentiment negativo:**
- Query: `"analyze [ticker ribassista]"`
- Expected sentiment: `"bearish"`
- Expected UI: Badge rosso, score <0, fattori negativi

**Verifica:**
- [ ] Badge sentiment appare con colore corretto
- [ ] Score visualizzato
- [ ] Lista fattori mostrata

---

## 4. NeuralEngineUI

**Scopo:** Mostra risultati analisi neural engine (VEE core)

**Input atteso:**
\`\`\`javascript
finalState: {
  neural_analysis: {
    composite_score: number,
    factors: Record<string, number>,
    technical_details: object
  }
}
\`\`\`

**Condizioni rendering in chat.jsx:**
\`\`\`javascript
{msg.finalState.neural_analysis && (
  <NeuralEngineUI analysis={msg.finalState.neural_analysis} />
)}
\`\`\`

**Test Case 4.1 - Analisi completa:**
- Query: `"analyze AAPL"`
- Expected: Composite score + breakdown fattori
- Expected UI: Gauge score, radar chart fattori

**Verifica:**
- [ ] Composite score gauge appare
- [ ] Fattori breakdown mostrato
- [ ] Chart rendering corretto

---

## 5. ComposeNodeUI ⭐ (Main VEE Display)

**Scopo:** Entry point principale per VEE unificata

**Input atteso:**
\`\`\`javascript
finalState: {
  narrative: string,
  vee_explanations: Record<ticker, {beginner, medium, technical}>,
  explainability: {
    detailed: {
      portfolio_metrics?: object,
      // ...altri dati
    }
  },
  numerical_panel: Array<{label, value, sentiment}>
}
\`\`\`

**Condizioni rendering in chat.jsx:**
\`\`\`javascript
{(msg.finalState.narrative || msg.finalState.vee_explanations) && (
  <ComposeNodeUI
    narrative={msg.finalState.narrative}
    veeExplanations={msg.finalState.vee_explanations}
    explainability={msg.finalState.explainability}
    numericalPanel={msg.finalState.numerical_panel}
  />
)}
\`\`\`

**Test Case 5.1 - Single Ticker (Main Use Case):**
- Query: `"analyze AAPL"`
- Expected:
  - Executive Summary con narrative
  - Numerical Panel in header (score + sentiment)
  - VEE Multi-Level Accordion per AAPL
  - NO Portfolio badge
  - NO Comparison info
- Expected UI: Card con gradient blu, Brain icon, accordions espandibili

**Test Case 5.2 - Portfolio Context:**
- Query: `"analizza il mio portfolio"`
- Expected:
  - Portfolio badge (purple)
  - Portfolio Insights section
  - Narrative portfolio-focused
  - VEE per ticker nel portfolio
- Expected UI: Purple badge in header, portfolio stats section

**Test Case 5.3 - Comparison Context:**
- Query: `"compare AAPL vs MSFT"`
- Expected:
  - "2 Tickers" badge (blue)
  - Comparison Mode info box
  - VEE accordions per entrambi i ticker
  - Narrative comparison-focused
- Expected UI: Blue badge in header, comparison info box

**Verifica:**
- [ ] Executive Summary appare con gradient
- [ ] Numerical Panel in header corretto
- [ ] Context badge appropriato (Portfolio/Multi-ticker/None)
- [ ] VEE Accordions per ogni ticker
- [ ] Advanced Details collapsible funziona
- [ ] Link parsing con scroll-to-anchor

---

## 6. PortfolioNodeUI ⚠️ (Intent-Based Rendering)

**Scopo:** Mostra analisi portfolio utente

**Input atteso:**
\`\`\`javascript
finalState: {
  intent: "portfolio" | "portfolio_review",
  action: "portfolio_review",
  portfolio_state: {
    total_value: number,
    num_holdings: number,
    concentration_risk: number,
    diversification_score: number,
    sector_breakdown: Record<string, number>,
    holdings: Array<{ticker, shares, avg_cost, current_value}>
  }
}
\`\`\`

**Condizioni rendering in chat.jsx (CRITICAL):**
\`\`\`javascript
{(() => {
  const isPortfolioIntent = msg.finalState.intent === "portfolio" || 
                           msg.finalState.intent === "portfolio_review" ||
                           msg.finalState.action === "portfolio_review"
  return isPortfolioIntent && msg.finalState.portfolio_state
})() && (
  <PortfolioNodeUI portfolioState={msg.finalState.portfolio_state} />
)}
\`\`\`

**Test Case 6.1 - Portfolio Esplicito (DEVE apparire):**
- Query: `"analizza il mio portfolio"`
- Expected intent: `"portfolio"` o action: `"portfolio_review"`
- Expected UI: Card con Total Value, Holdings, Sector Breakdown
- **CRITICAL:** Portfolio DEVE apparire

**Test Case 6.2 - Single Ticker (NON deve apparire):**
- Query: `"analyze AAPL"`
- Expected intent: `"ticker_analysis"`
- Expected: portfolio_state potrebbe esistere ma essere vuoto
- **CRITICAL:** Portfolio NON deve apparire (intent check blocca)

**Test Case 6.3 - Comparison (NON deve apparire):**
- Query: `"compare AAPL vs MSFT"`
- Expected intent: `"comparison"`
- **CRITICAL:** Portfolio NON deve apparire

**Test Case 6.4 - Mock Portfolio:**
- Query: `"!test_portfolio"`
- Expected: Mock data con $63,500
- Expected UI: 6 holdings, sector breakdown

**Verifica:**
- [ ] Appare SOLO quando intent=portfolio
- [ ] NON appare per "analyze AAPL" (regression test)
- [ ] NON appare per comparison
- [ ] Guard num_holdings=0 funziona
- [ ] Console debug log corretto

---

## 7. ComparisonNodeUI

**Scopo:** Mostra confronto multi-ticker

**Input atteso:**
\`\`\`javascript
finalState: {
  comparison_state: {
    tickers: Array<string>,
    ranking: Array<{ticker, composite_score, rank}>,
    factor_winners: Record<factor, ticker>,
    factor_deltas: Record<factor, Record<ticker, delta>>,
    range_dispersion: object
  }
}
\`\`\`

**Condizioni rendering in chat.jsx:**
\`\`\`javascript
{msg.finalState.comparison_state && (
  <ComparisonNodeUI comparisonState={msg.finalState.comparison_state} />
)}
\`\`\`

**Test Case 7.1 - Comparison 2 tickers:**
- Query: `"compare AAPL vs MSFT"`
- Expected: Ranking table, factor winners, deltas
- Expected UI: Card con tabella ranking, radar chart

**Test Case 7.2 - Comparison 3+ tickers:**
- Query: `"compare AAPL vs MSFT vs GOOGL"`
- Expected: Ranking 3 ticker, factor analysis estesa
- Expected UI: Tabella più ampia

**Test Case 7.3 - Mock Comparison:**
- Query: `"!test_comparison"`
- Expected: Mock data con 3 ticker (AAPL, MSFT, GOOGL)
- Expected UI: Full comparison display

**Verifica:**
- [ ] Ranking table corretto
- [ ] Factor winners mostrati
- [ ] Radar chart rendering
- [ ] Guard tickers.length < 2 funziona

---

## 8. FallbackNodeUI

**Scopo:** Fallback quando nessun nodo specifico match

**Input atteso:**
\`\`\`javascript
// Qualsiasi finalState che non match altri nodi
\`\`\`

**Condizioni rendering in chat.jsx:**
\`\`\`javascript
{(!msg.finalState.narrative && !msg.finalState.vee_explanations && 
  !msg.finalState.portfolio_state && !msg.finalState.comparison_state) && (
  <FallbackNodeUI data={msg.finalState} />
)}
\`\`\`

**Test Case 8.1 - Query ambigua:**
- Query: `"ciao"` o query senza intent chiaro
- Expected: Fallback con messaggio generico
- Expected UI: Card con messaggio di fallback

**Verifica:**
- [ ] Appare quando nessun altro nodo match
- [ ] Messaggio user-friendly
- [ ] Suggerimenti per l'utente

---

## 🔬 Test Flow Completo

### Flow 1: Single Ticker Analysis
\`\`\`
Query: "analyze AAPL"

Expected Node Sequence:
1. IntentNodeUI (intent="ticker_analysis") ✓
2. [TickerResolverUI - SKIP se ticker già valido]
3. ComposeNodeUI (main VEE display) ✓
   - Executive Summary
   - Numerical Panel (score + sentiment)
   - VEE Accordions (AAPL)
4. [Charts - CandlestickChart, RadarChart, RiskChart]
5. SentimentNodeUI (sentiment AAPL) ✓ (se presente)
6. ❌ PortfolioNodeUI (NON deve apparire - intent check)
7. ❌ ComparisonNodeUI (NON deve apparire)
\`\`\`

### Flow 2: Portfolio Analysis
\`\`\`
Query: "analizza il mio portfolio"

Expected Node Sequence:
1. IntentNodeUI (intent="portfolio") ✓
2. ComposeNodeUI (portfolio-aware) ✓
   - Portfolio badge (purple)
   - Portfolio Insights section
   - VEE per ticker nel portfolio
3. PortfolioNodeUI (portfolio stats) ✓
   - Total Value
   - Holdings breakdown
   - Sector diversification
4. [Charts per ticker nel portfolio]
\`\`\`

### Flow 3: Multi-Ticker Comparison
\`\`\`
Query: "compare AAPL vs MSFT"

Expected Node Sequence:
1. IntentNodeUI (intent="comparison") ✓
2. [TickerResolverUI se necessario]
3. ComposeNodeUI (comparison-aware) ✓
   - "2 Tickers" badge (blue)
   - Comparison Mode info
   - VEE accordions per AAPL e MSFT
4. ComparisonNodeUI (ranking + deltas) ✓
   - Ranking table
   - Factor winners
   - Radar chart comparative
5. ❌ PortfolioNodeUI (NON deve apparire)
\`\`\`

---

## 📋 Checklist Generale Test

**Pre-Test Setup:**
- [ ] Frontend running su http://localhost:3005
- [ ] Backend API up (vitruvyan_api_graph:8004)
- [ ] Console browser aperta (F12 → Console tab)
- [ ] Network tab aperta per vedere API calls

**Per Ogni Test:**
- [ ] Inserisci query nel chat
- [ ] Osserva quali nodi appaiono (in ordine)
- [ ] Verifica content di ogni nodo
- [ ] Controlla console per debug logs
- [ ] Screenshot se necessario
- [ ] Annota comportamenti inaspettati

**Post-Test:**
- [ ] Documenta risultati in questo file
- [ ] Identifica bug o regressioni
- [ ] Prioritizza fix necessari
- [ ] Aggiorna architettura se necessario

---

## 🐛 Bug Tracking

### Bug #1: Portfolio showing for non-portfolio queries
- **Status:** ✅ FIXED (intent-based rendering)
- **Fix:** Commit 5b7853c + intent check in chat.jsx
- **Test:** "analyze AAPL" → Portfolio NON deve apparire

### Bug #2: [Aggiungi qui nuovi bug scoperti]

---

## 📊 Test Results

### Test Run #1 - 30 Nov 2025

#### ✅ Test 1.1: Single Ticker Analysis ("analyze AAPL")
**Status:** ✅ PASSED

**Verifiche:**
- ✅ ComposeNodeUI renderizzato correttamente
- ✅ Executive Summary visibile
- ✅ Numerical Panel in header
- ✅ VEE Accordions espandibili
- ✅ NO Portfolio section (intent-based rendering working)
- ✅ NO Comparison info
- ✅ Charts rendering (se presenti)

**Note:** Funzionamento corretto post-FASE 2. VEE centralizzata in ComposeNodeUI.

---

#### ⏳ Test 1.2: Portfolio Analysis
- [ ] Portfolio (!test_portfolio)
- [ ] Real portfolio ("analizza il mio portfolio")

#### ⏳ Test 1.3: Comparison Analysis
- [ ] Comparison (!test_comparison)
- [ ] Real comparison ("compare AAPL vs MSFT")

---

## 🎯 Prossimi Passi

1. **Eseguire test sistematico** di ogni nodo
2. **Documentare comportamenti** osservati
3. **Identificare gap** tra atteso e reale
4. **Prioritizzare fix** necessari
5. **Iterare** fino a stabilità completa

**Focus immediato:**
- ✅ Validare ComposeNodeUI con tutti i contesti
- ✅ Verificare intent-based rendering portfolio
- ⏳ Test comparison flow
- ⏳ Test fallback scenarios
