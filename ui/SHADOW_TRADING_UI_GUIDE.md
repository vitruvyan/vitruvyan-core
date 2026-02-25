# Shadow Trading System - Guida UI/UX
**Data**: 24 Gennaio 2026  
**Status**: ❌ UI NON ANCORA IMPLEMENTATA (Backend 100% funzionante)

---

## 🎯 Cos'è lo Shadow Trading?

Lo **Shadow Trading System** (Sacred Order #6) è il sistema di **trading simulato con soldi virtuali** che permette di:
- 💰 Comprare e vendere titoli senza rischio reale
- 📊 Tracciare performance del portfolio shadow
- 🤖 Ricevere suggerimenti AI per ogni trade
- 📈 Vedere P&L in tempo reale (unrealized + realized)
- 🧠 Ottenere spiegazioni VEE per ogni ordine eseguito

**NON è paper trading**: usa **AI reasoning** (GPT-4o) per analizzare ogni ordine PRIMA dell'esecuzione, come un broker intelligente.

---

## ⚠️ STATO ATTUALE (Jan 24, 2026)

### ✅ Backend COMPLETO (100%)
- API Shadow Trading: `docker/services/api_shadow_traders/` (1554 lines, port 8011)
- PostgreSQL tables: `shadow_positions`, `shadow_trades`, `shadow_portfolio_snapshots`, `shadow_cash_accounts`
- AI Reasoning Agent: `ShadowBrokerAgent` con GPT-4o approval workflow
- VEE Narratives: 3-level explanations per ogni trade
- Redis Cognitive Bus: Eventi publish/subscribe

### ❌ Frontend MANCANTE (0%)
- NO pagina `/shadow-trading` (404)
- NO componenti UI per buy/sell
- NO dashboard portfolio shadow
- NO visualizzazione P&L
- NO bottone "Buy"/"Sell" su ticker analysis

**TUTTO IL BACKEND È PRONTO** → Serve solo UI!

---

## 🛠️ API Backend Disponibili

### 1. Comprare Titoli (BUY)

**Endpoint**: `POST http://localhost:8011/shadow/buy`

**Request**:
```json
{
  "user_id": "beta_user_01",
  "ticker": "AAPL",
  "quantity": 100
}
```

**Response**:
```json
{
  "status": "filled",
  "message": "Order filled successfully",
  "order_id": "ORDER-20260124-123456",
  "ticker": "AAPL",
  "quantity": 100,
  "fill_price": 187.45,
  "total_cost": 18745.00,
  "vee_narrative": {
    "summary": "Apple acquisition at optimal momentum window (RSI 65, MACD bullish cross)",
    "technical": "Entry price $187.45 represents 3.2% below 52-week high with strong volume confirmation (120% avg). Momentum z-score +0.86 signals upward pressure...",
    "strategic": "Position sizing: 43.4% allocation (HIGH concentration risk). Consider diversification if portfolio >40% single ticker..."
  }
}
```

**Come funziona**:
1. User clicca "Buy 100 AAPL" nell'UI
2. Frontend chiama `POST /shadow/buy`
3. Backend usa GPT-4o per validare trade ("è un buon momento?")
4. Se approvato → esegue ordine, salva in PostgreSQL, aggiorna cash balance
5. Response include VEE narrative (spiegazione 3 livelli)
6. Frontend mostra success message + VEE accordion

---

### 2. Vendere Titoli (SELL)

**Endpoint**: `POST http://localhost:8011/shadow/sell`

**Request**:
```json
{
  "user_id": "beta_user_01",
  "ticker": "AAPL",
  "quantity": 50
}
```

**Response**: Identica a BUY, ma con `side: "sell"`

---

### 3. Vedere Portfolio Shadow

**Endpoint**: `GET http://localhost:8011/portfolio/{user_id}`

**Response**:
```json
{
  "user_id": "beta_user_01",
  "cash_balance": 10500.00,
  "total_value": 41500.00,
  "unrealized_pnl": 2150.00,
  "total_pnl": 2150.00,
  "num_positions": 3,
  "positions": [
    {
      "ticker": "AAPL",
      "quantity": 100,
      "entry_price": 185.00,
      "current_price": 187.45,
      "unrealized_pnl": 245.00,
      "unrealized_pnl_percent": 1.32,
      "weight": 43.4,
      "sector": "Technology"
    },
    {
      "ticker": "NVDA",
      "quantity": 50,
      "entry_price": 480.00,
      "current_price": 525.00,
      "unrealized_pnl": 2250.00,
      "unrealized_pnl_percent": 9.38,
      "weight": 61.0,
      "sector": "Technology"
    }
  ],
  "sector_allocation": {
    "Technology": 85.0,
    "Consumer": 15.0
  },
  "risk_metrics": {
    "concentration_risk": "high",
    "diversification_score": 0.65,
    "volatility": 0.28
  },
  "agent_insights": [
    "HIGH concentration in Technology (85%) - consider diversification",
    "NVDA unrealized gain 9.38% - strong momentum, watch for profit-taking signals"
  ],
  "timestamp": "2026-01-24T15:30:00Z"
}
```

**Cosa include**:
- 💵 Cash balance disponibile
- 📊 Total portfolio value (cash + positions)
- 📈 Unrealized P&L (guadagni/perdite non realizzati)
- 🎯 Singole posizioni con entry price, current price, P&L
- 🧠 AI insights (concentration warnings, profit-taking suggestions)
- ⚠️ Risk metrics (diversification score, volatility)

---

### 4. Ottenere Suggerimenti Trade

**Endpoint**: `POST http://localhost:8011/suggest_trades`

**Request**:
```json
{
  "user_id": "beta_user_01",
  "portfolio_context": {
    "cash_balance": 10500,
    "positions": [{"ticker": "AAPL", "quantity": 100}]
  },
  "preferences": {
    "risk_tolerance": "moderate",
    "sectors": ["Technology", "Healthcare"]
  }
}
```

**Response**:
```json
{
  "suggestions": [
    {
      "ticker": "MSFT",
      "action": "buy",
      "quantity": 30,
      "rationale": "Diversification: reduce AAPL concentration (43.4% → 35%), MSFT momentum z-score +0.92 (strong uptrend)",
      "expected_impact": {
        "new_concentration": 35.0,
        "diversification_improvement": 0.12
      }
    },
    {
      "ticker": "UNH",
      "action": "buy",
      "quantity": 10,
      "rationale": "Sector diversification: add Healthcare exposure (0% → 15%), defensive play for volatility hedge",
      "expected_impact": {
        "sector_allocation": {"Technology": 75, "Healthcare": 15, "Cash": 10}
      }
    }
  ],
  "overall_strategy": "Reduce Technology concentration below 80%, add defensive Healthcare exposure"
}
```

**Uso**: AI propone trade per ottimizzare portfolio (diversificazione, risk reduction, momentum opportunities)

---

## 🎨 UI da Implementare

### OPZIONE A: Chat Conversazionale (Quick Win - 4 ore)

**Dove**: Nella chat principale (già esistente)

**Come funziona**:
1. User scrive: "compra 100 AAPL"
2. Intent detection: `intent=shadow_buy, quantity=100`
3. Backend chiama `/shadow/buy`
4. Chat risponde con:
   ```
   ✅ Ordine eseguito: 100 AAPL @ $187.45 = $18,745.00
   
   💰 Cash rimanente: $10,500
   📊 Portfolio value: $41,500
   
   📈 VEE Analysis:
   [VEE Accordion 3 livelli]
   
   🔍 AI Insight: "Position sizing: 43.4% allocation (HIGH concentration risk)"
   
   [Vedi Portfolio Shadow] ← Link a /shadow-trading
   ```

**PRO**:
- ✅ Zero UI nuova (usa chat esistente)
- ✅ Intent detection già implementato (GPT-4o, 95% accuracy)
- ✅ VEE Accordions già esistenti
- ✅ 4 ore effort (backend integration only)

**CONTRO**:
- ❌ No visual portfolio dashboard
- ❌ No chart P&L nel tempo
- ❌ User deve ricordare holdings

---

### OPZIONE B: Dashboard Shadow Trading (Full Feature - 20 ore)

**Dove**: Nuova pagina `/shadow-trading`

**Sezioni**:

#### 1. **Header Portfolio** (simile a /portfolio page)
```
┌─────────────────────────────────────────────────────────┐
│  💰 Cash Balance        📊 Total Value      📈 P&L Today │
│    $10,500.00              $41,500.00         +$325 (2%) │
└─────────────────────────────────────────────────────────┘
```

#### 2. **Quick Trade Panel**
```
┌─────────────────────────────────────────┐
│  Quick Trade                            │
│  ┌─────────┐  ┌──────┐  ┌──────────┐  │
│  │ Ticker  │  │ Qty  │  │ BUY SELL │  │
│  │ [AAPL]  │  │ [100]│  │  🟢  🔴  │  │
│  └─────────┘  └──────┘  └──────────┘  │
│                                         │
│  ⚙️ AI Pre-Check: ✅ Approved          │
│  📊 Estimated cost: $18,745            │
└─────────────────────────────────────────┘
```

**Features**:
- Ticker autocomplete (già implementato in chat)
- Quantity input numerico
- Real-time price fetch
- AI pre-check prima di mostrare bottoni (GET `/pre_trade_check`)
- Click BUY/SELL → API call → success/error message

#### 3. **Holdings Table** (come /portfolio Composition)
```
┌───────────────────────────────────────────────────────────────┐
│  Holdings (3)                                                 │
│  ┌──────┬───────┬───────────┬──────────┬────────┬─────────┐ │
│  │Ticker│ Qty   │ Entry     │ Current  │ P&L    │ Weight  │ │
│  ├──────┼───────┼───────────┼──────────┼────────┼─────────┤ │
│  │ AAPL │ 100   │ $185.00   │ $187.45  │ +$245  │  43.4%  │ │
│  │ NVDA │  50   │ $480.00   │ $525.00  │+$2,250 │  61.0%  │ │
│  │ TSLA │  25   │ $210.00   │ $195.00  │  -$375 │  11.3%  │ │
│  └──────┴───────┴───────────┴──────────┴────────┴─────────┘ │
│                                                               │
│  🔴 WARNING: Technology concentration 85% (risky!)           │
└───────────────────────────────────────────────────────────────┘
```

**Features**:
- Color-coded P&L (green positive, red negative)
- Click ticker → single ticker analysis (già esiste in /chat)
- Concentration warnings (già calcolati da backend)

#### 4. **Performance Chart** (LineChart come /portfolio)
```
Portfolio Value History (30 days)
┌─────────────────────────────────────────┐
│  $42k ┤                         ╭─╮     │
│  $41k ┤                   ╭─────╯ ╰     │
│  $40k ┤         ╭─────────╯             │
│  $39k ┤   ╭─────╯                       │
│  $38k ┤───╯                             │
│       └─┬──┬──┬──┬──┬──┬──┬──┬──┬──┬───│
│         1  5 10 15 20 25 30 (days)      │
└─────────────────────────────────────────┘
```

**Data source**: `shadow_portfolio_snapshots` table (daily snapshots)

#### 5. **AI Suggestions Panel** (Optional)
```
┌─────────────────────────────────────────────┐
│  🤖 AI Trade Suggestions                    │
│  ┌────────────────────────────────────────┐ │
│  │ 1. BUY 30 MSFT                         │ │
│  │    Rationale: Reduce AAPL concentration│ │
│  │    [Execute] [Dismiss]                 │ │
│  └────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────┐ │
│  │ 2. BUY 10 UNH                          │ │
│  │    Rationale: Add Healthcare exposure  │ │
│  │    [Execute] [Dismiss]                 │ │
│  └────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

**Data source**: `POST /suggest_trades`

---

## 🎯 Roadmap Implementazione UI

### FASE 1: Chat Integration (4 ore) - QUICK WIN ⚡

**Obiettivo**: Buy/Sell via chat + link a portfolio shadow

**Files da modificare**:
1. `vitruvyan-ui/components/chat.jsx` (già esistente, 862 lines)
   - Detect `intent=shadow_buy` o `intent=shadow_sell`
   - Call API `/shadow/buy` o `/shadow/sell`
   - Render success message con VEE accordion
   - Add link "🔍 Vedi Portfolio Shadow" → `/shadow-trading`

**Tasks**:
- [ ] Add shadow trade handler in chat.jsx (1h)
- [ ] Format shadow trade response message (1h)
- [ ] Add portfolio link button (0.5h)
- [ ] Test E2E: "compra 100 AAPL" → order executed (1.5h)

**Test**:
```javascript
// Test query
"compra 100 AAPL"

// Expected response
{
  intent: "shadow_buy",
  route: "shadow_trading_exec",
  shadow_trade_result: {
    status: "filled",
    ticker: "AAPL",
    quantity: 100,
    fill_price: 187.45,
    total_cost: 18745.00,
    vee_narrative: {...}
  }
}

// UI displays
✅ Ordine eseguito: 100 AAPL @ $187.45
💰 Cash rimanente: $10,500
[VEE Accordion]
[Vedi Portfolio Shadow] ← Button
```

---

### FASE 2: Portfolio Shadow Page (16 ore)

**Obiettivo**: Dashboard completo `/shadow-trading`

**Files da creare**:
1. `vitruvyan-ui/app/shadow-trading/page.jsx` (800+ lines, simile a portfolio/page.jsx)
   - Header Portfolio (cash, total value, P&L today)
   - Quick Trade Panel (ticker input + qty + BUY/SELL buttons)
   - Holdings Table (simile a Composition section di portfolio)
   - Performance Chart (LineChart con timeseries)
   - AI Suggestions Panel (optional)

**Tasks**:
- [ ] Create /shadow-trading page structure (2h)
- [ ] Implement Quick Trade Panel (4h)
  - Ticker autocomplete integration
  - Quantity input validation
  - API call POST /shadow/buy|sell
  - Success/error handling
  - VEE modal on success
- [ ] Implement Holdings Table (3h)
  - Fetch GET /portfolio/{user_id}
  - Render positions with P&L color coding
  - Click ticker → redirect to chat analysis
- [ ] Implement Performance Chart (4h)
  - Fetch shadow_portfolio_snapshots (new API needed)
  - Recharts LineChart integration
  - Multi-timeframe selector (7D/1M/3M/YTD/ALL)
- [ ] Implement AI Suggestions (2h, optional)
  - Fetch POST /suggest_trades
  - Render suggestion cards
  - "Execute" button → call /shadow/buy
- [ ] Testing E2E (1h)

**Mock Data** (per sviluppo frontend):
```javascript
const mockPortfolio = {
  cash_balance: 10500,
  total_value: 41500,
  unrealized_pnl: 2150,
  positions: [
    {ticker: "AAPL", quantity: 100, entry_price: 185, current_price: 187.45},
    {ticker: "NVDA", quantity: 50, entry_price: 480, current_price: 525}
  ]
}
```

---

### FASE 3: Integration with Autopilot (8 ore)

**Obiettivo**: Autopilot può eseguire trade shadow automaticamente

**Features**:
- Guardian rileva opportunity → Autopilot propone trade → User approva → Shadow Trading esegue
- Toggle "Autopilot Shadow Trading" in `/portfolio` page
- Autopilot actions timeline mostra shadow trades eseguiti

**Tasks**:
- [ ] Add toggle in Autopilot tab (2h)
- [ ] Autopilot → Shadow Trading API integration (4h)
- [ ] Actions timeline render shadow trades (2h)

---

## 💰 Cash Balance & Initial Funding

**Come funziona**:
1. Ogni user parte con **$50,000 virtual cash** (default)
2. Cash balance stored in `shadow_cash_accounts` table
3. Buy trade → sottrae cash + fee (0.5%)
4. Sell trade → aggiunge cash - fee (0.5%)
5. Se cash insufficiente → order rejected

**Esempio**:
```
Initial: $50,000 cash
BUY 100 AAPL @ $187.45 = -$18,745 - $93.73 (fee) = -$18,838.73
Remaining: $31,161.27 cash
```

**Frontend deve mostrare**:
- Cash balance in header
- "Insufficient funds" error se user prova buy senza cash
- Fee preview nel Quick Trade Panel

---

## 🧪 Testing Backend (Senza UI)

**Test 1: Buy Order**
```bash
curl -X POST http://localhost:8011/shadow/buy \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "ticker": "AAPL",
    "quantity": 100
  }'
```

**Test 2: Get Portfolio**
```bash
curl http://localhost:8011/portfolio/test_user
```

**Test 3: Sell Order**
```bash
curl -X POST http://localhost:8011/shadow/sell \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "ticker": "AAPL",
    "quantity": 50
  }'
```

**Verify in PostgreSQL**:
```sql
-- Check positions
SELECT * FROM shadow_positions WHERE user_id = 'test_user';

-- Check cash
SELECT * FROM shadow_cash_accounts WHERE user_id = 'test_user';

-- Check trade history
SELECT * FROM shadow_trades WHERE user_id = 'test_user' ORDER BY created_at DESC;
```

---

## 🎯 Decision Point: Quale opzione?

### OPZIONE A: Chat Only (4 ore)
**PRO**: Zero UI nuova, quick win, testing immediato  
**CONTRO**: No visual dashboard, limitato UX

**Raccomandato per**: MVP testing, validare flusso buy/sell

### OPZIONE B: Full Dashboard (20 ore)
**PRO**: Professional UX, portfolio tracking, AI suggestions  
**CONTRO**: Più effort, richiede design system consistency

**Raccomandato per**: Production release, user retention

### OPZIONE C: Hybrid (12 ore)
**Fase 1**: Chat integration (4h)  
**Fase 2**: Minimal dashboard (holdings table + quick trade) (8h)  
**Fase 3**: Performance chart + AI suggestions (postponed to Sprint 2)

**Raccomandato per**: Balanced approach, progressive enhancement

---

## 🚀 Immediate Next Steps

**Decisione richiesta**:
1. Vuoi OPZIONE A (chat only, 4h)?
2. Vuoi OPZIONE B (full dashboard, 20h)?
3. Vuoi OPZIONE C (hybrid, 12h)?

Una volta deciso, posso:
- Creare wireframe UI dettagliato
- Implementare FASE 1 (chat integration)
- Creare `/shadow-trading/page.jsx` boilerplate

**Backend è 100% pronto** → Basta collegare UI! 🎉
