# Portfolio Dashboard - Backend Audit Report
**Date**: January 24, 2026  
**Purpose**: Identify existing backend code before implementing Task 24-25 Day 4-12

---

## 🎯 Executive Summary

**Percentuale esistente**: ~70% della logica backend già implementata  
**Lavoro necessario**: API wrappers + performance calculation + export tools  
**Timeline aggiornata**: 36 ore (vs 60 ore stimata inizialmente) = **-40% effort**

---

## ✅ BACKEND ESISTENTE (Già Implementato)

### 1. Portfolio Data Foundation ✅ (90% COMPLETO)

**Tabelle PostgreSQL**:
```sql
shadow_portfolio_snapshots (migrations/shadow_trading_schema_v1.sql:168)
  - snapshot_id, user_id, snapshot_date
  - total_value, cash_balance, positions_value
  - pnl_absolute, pnl_percent
  - risk_score, diversification_score
  - metadata JSONB

shadow_positions (migrations/shadow_trading_schema_v1.sql:98)
  - position_id, user_id, ticker
  - quantity, entry_price, current_price
  - pnl_absolute, pnl_percent
  - weight, sector
```

**API Esistenti**:
- ✅ `GET /portfolio/{user_id}` (api_shadow_traders:581) → Returns PortfolioSnapshotResponse
- ✅ `GET /portfolios/{user_id}` (api_portfolio_architects:208) → Returns all user portfolios

**LangGraph Node**:
- ✅ `portfolio_analysis_node.py` (511 lines) → Complete quantitative analysis
  - Sector breakdown computation
  - Factor averages (momentum_z, trend_z, sentiment_z)
  - Concentration risk calculation
  - Diversification scoring
  - Neural Engine ranking integration

**Cosa manca (10%)**:
- Frontend integration (fetch API + state management)
- P&L today calculation (needs daily snapshots comparison)

---

### 2. Guardian Insights ✅ (95% COMPLETO)

**Tabelle PostgreSQL**:
```sql
guardian_insights (migrations/portfolio_architects/002:42)
  - insight_id, user_id, snapshot_id
  - insight_type (risk_alert, opportunity, rebalance, regime_change, performance_attribution)
  - severity (info, warning, critical)
  - title, description
  - metrics JSONB, recommendations JSONB
  - vee_explanations JSONB, conversational_summary TEXT
  - created_at
```

**Agenti Implementati**:
- ✅ `PortfolioGuardianAgent` (862 lines, portfolio_guardian_agent.py)
  - 5 insight types generation
  - VEE conversational mode integration
  - ChatGPT fallback for natural summaries
  - Risk categorization (concentration, volatility, drawdown, correlation, liquidity)
  - Prometheus metrics

**API Esistenti**:
- ✅ `GET /guardian/portfolio` (api_portfolio_guardian:293) → Portfolio monitoring

**LangGraph Nodes**:
- ✅ `guardian_monitor_node.py` (277 lines) → Fetches snapshots + runs Guardian analysis
- ✅ `portfolio_guardian_node.py` (existing) → Guardian orchestration

**Cosa manca (5%)**:
- API endpoint specifico: `GET /guardian/insights/{user_id}?limit=10`
- Frontend integration (Guardian tab UI)

---

### 3. Autopilot Control ✅ (85% COMPLETO)

**Tabelle PostgreSQL**:
```sql
user_autopilot_settings (migrations/portfolio_architects/002:128)
  - user_id, autopilot_mode (manual, autonomous, disabled)
  - risk_tolerance (1-10), max_position_size
  - allowed_actions JSONB
  - emergency_stop BOOLEAN
  - updated_at

autopilot_actions (migrations/portfolio_architects/002:83)
  - action_id, user_id, insight_id
  - action_type (buy, sell, rebalance, hedge, no_action)
  - ticker, quantity, target_weight
  - rationale, risk_score
  - status (pending, approved, rejected, executed, failed, cancelled)
  - executed_at, execution_metadata JSONB
```

**Agenti Implementati**:
- ✅ `AutopilotAgent` (753 lines, autopilot_agent.py)
  - Guardian insight → trade action mapping
  - Safety layer (manual/autonomous/disabled modes)
  - Risk threshold checks
  - Emergency stop mechanism
  - Shadow Trading API integration
  - PostgreSQL audit trail

**LangGraph Nodes**:
- ✅ `autopilot_node.py` (existing) → Evaluates Guardian insights + orchestrates actions

**Cosa manca (15%)**:
- API endpoints:
  - `POST /autopilot/toggle` (enable/disable + risk slider)
  - `GET /autopilot/actions/{user_id}` (action history)
- Frontend integration (toggle button + risk slider + actions timeline)
- Cron job trigger (hourly autopilot analyzer)

---

### 4. Risk Dashboard ❌ (30% COMPLETO)

**Logica Esistente**:
- ✅ `VARE Engine` (core/logic/vitruvyan_proprietary/vare_engine.py)
  - Multi-dimensional risk analysis
  - Beta calculation
  - Volatility (annualized)
  - Liquidity scoring
  - Correlation risk
- ✅ Portfolio snapshots have `risk_score` field

**Cosa manca (70%)**:
- ❌ VaR (Value at Risk) calculation
- ❌ Correlation matrix computation
- ❌ Risk radar data aggregation
- ❌ API endpoint: `GET /portfolio/risk/{user_id}`
- ❌ Frontend integration

---

### 5. Performance Analytics ❌ (20% COMPLETO)

**Logica Esistente**:
- ✅ `shadow_portfolio_snapshots` table has historical data
- ✅ `pnl_absolute`, `pnl_percent` fields exist

**Cosa manca (80%)**:
- ❌ Timeseries aggregation (daily/weekly/monthly snapshots)
- ❌ Benchmark data fetching (SPY, QQQ via yfinance)
- ❌ Metrics calculation:
  - Total Return (current vs initial value)
  - Max Drawdown (peak-to-trough)
  - Sharpe Ratio (risk-adjusted return)
  - Volatility (annualized std)
- ❌ API endpoint: `GET /portfolio/performance/{user_id}?timeframe=1M`
- ❌ Frontend integration

---

### 6. Advanced Tools ❌ (0% COMPLETO)

**Niente implementato**:
- ❌ PDF report generation (reportlab)
- ❌ CSV export
- ❌ Email delivery
- ❌ Rebalancing simulator
- ❌ Dividends calendar (yfinance integration)

---

## 📊 Roadmap Aggiornata (36 ore vs 60 ore originale)

### MILESTONE 1: Portfolio Data Foundation (2 ore vs 6h) ⚡ 70% già fatto
**Esistente**:
- ✅ shadow_portfolio_snapshots table
- ✅ shadow_positions table
- ✅ GET /portfolio/{user_id} API
- ✅ portfolio_analysis_node.py (sector breakdown, factor averages, risk scoring)

**Da fare** (2 ore):
1. Frontend integration: `useEffect` fetch API (1h)
2. P&L today calculation: Compare latest 2 snapshots (1h)

---

### MILESTONE 2: Guardian Integration (3 ore vs 6h) ⚡ 95% già fatto
**Esistente**:
- ✅ guardian_insights table
- ✅ PortfolioGuardianAgent (862 lines, 5 insight types)
- ✅ guardian_monitor_node.py
- ✅ VEE + ChatGPT conversational mode

**Da fare** (3 ore):
1. New API endpoint: `GET /guardian/insights/{user_id}?limit=10` (1h)
2. Frontend Guardian tab integration (2h)

---

### MILESTONE 3: Autopilot Control (6 ore vs 16h) ⚡ 85% già fatto
**Esistente**:
- ✅ user_autopilot_settings table
- ✅ autopilot_actions table
- ✅ AutopilotAgent (753 lines, safety layer, trade orchestration)
- ✅ autopilot_node.py

**Da fare** (6 ore):
1. API endpoint: `POST /autopilot/toggle` (user_id, enabled, risk_tolerance) (2h)
2. API endpoint: `GET /autopilot/actions/{user_id}` (action history) (1h)
3. Frontend toggle button + risk slider integration (2h)
4. Cron job setup (hourly autopilot analyzer if enabled) (1h)

---

### MILESTONE 4: Risk Dashboard (8 ore - UNCHANGED) ⚠️ 70% da fare
**Esistente**:
- ✅ VARE Engine (beta, volatility, liquidity, correlation logic)
- ✅ shadow_portfolio_snapshots.risk_score

**Da fare** (8 ore):
1. VaR calculation (95% confidence, 1-day horizon, Monte Carlo) (3h)
2. Correlation matrix computation (yfinance price data, numpy) (2h)
3. Risk radar data aggregation (6 dimensions normalized 0-10) (1h)
4. API endpoint: `GET /portfolio/risk/{user_id}` (1h)
5. Frontend integration (Risk Dashboard section) (1h)

---

### MILESTONE 5: Performance Analytics (12 ore - UNCHANGED) ⚠️ 80% da fare
**Esistente**:
- ✅ shadow_portfolio_snapshots table (historical data)

**Da fare** (12 ore):
1. Timeseries query optimization (daily snapshots aggregation) (2h)
2. Benchmark data fetching (yfinance SPY/QQQ, Redis cache 1h TTL) (3h)
3. Metrics calculation engine (total return, drawdown, Sharpe, volatility) (4h)
4. API endpoint: `GET /portfolio/performance/{user_id}?timeframe=1M` (2h)
5. Frontend integration (Performance chart + metrics cards) (1h)

---

### MILESTONE 6: Advanced Tools (5 ore vs 12h) ⚡ Simplified scope
**Priorità ridotta** (nice-to-have, non bloccante):

**PDF/CSV Export** (3 ore):
1. CSV export: Simple pandas DataFrame.to_csv() (1h)
2. PDF report: Minimal reportlab (portfolio summary + holdings table) (2h)

**Dividends Calendar** (2 ore):
1. yfinance ticker.calendar integration (1h)
2. Frontend calendar UI (1h)

**Rebalancing Simulator** (POSTPONED to Q2 2026):
- Complex logic (trade simulation, impact analysis)
- Low priority for MVP

---

## 📈 Timeline Finale

| Milestone | Effort Originale | Effort Reale | Risparmio | Priority |
|-----------|------------------|--------------|-----------|----------|
| M1: Portfolio Data | 6h | **2h** | -67% ⚡ | P0 |
| M2: Guardian | 6h | **3h** | -50% ⚡ | P1 |
| M3: Autopilot | 16h | **6h** | -63% ⚡ | P2 |
| M4: Risk Dashboard | 8h | **8h** | 0% | P1 |
| M5: Performance | 12h | **12h** | 0% | P0 |
| M6: Advanced Tools | 12h | **5h** | -58% ⚡ | P3 |
| **TOTAL** | **60h** | **36h** | **-40%** | |

**Timeline**:
- Week 1 (Day 4-5): M1 + M5 = 14h (Portfolio data + Performance analytics)
- Week 2 (Day 6-7): M2 + M4 = 11h (Guardian + Risk dashboard)
- Week 3 (Day 8-9): M3 + M6 = 11h (Autopilot + Export tools)

**Total: 36 ore = 4.5 giorni lavorativi (8h/day)**

---

## 🔑 Key Insights

1. **Shadow Trading System = Portfolio Foundation**
   - 90% della logica portfolio già implementata nel sistema Shadow Trading
   - shadow_portfolio_snapshots = production-ready historical data
   - shadow_positions = real-time holdings tracking

2. **Portfolio Architects = Guardian + Autopilot**
   - PortfolioGuardianAgent (862 lines) = 5 insight types già implementati
   - AutopilotAgent (753 lines) = trade orchestration + safety layer completo
   - PostgreSQL schema già migrato (guardian_insights, autopilot_actions, user_autopilot_settings)

3. **Performance Gap = Timeseries Analytics**
   - Historical data esiste (snapshots), manca solo aggregation engine
   - Benchmark integration (yfinance) = 3 ore effort
   - Metrics calculation (Sharpe, Drawdown) = 4 ore effort

4. **Risk Gap = Statistical Computation**
   - VARE logic esiste, manca VaR + Correlation matrix
   - yfinance + numpy = 5 ore effort
   - Frontend integration = 1 ora

5. **Advanced Tools = Low Priority**
   - CSV export = trivial (pandas)
   - PDF report = nice-to-have (reportlab simple template)
   - Rebalancing simulator = complex, postpone to Q2 2026

---

## 🎯 Priorità di Esecuzione (Revised)

**Week 1 (P0 - Must Have)**:
- M1: Portfolio Data Foundation (2h) → Header mostra dati reali
- M5: Performance Analytics (12h) → Chart funziona con timeseries + benchmarks

**Week 2 (P1 - Should Have)**:
- M2: Guardian Integration (3h) → Timeline insights popolata da DB
- M4: Risk Dashboard (8h) → VaR + Correlation matrix + Risk radar

**Week 3 (P2-P3 - Nice to Have)**:
- M3: Autopilot Control (6h) → Toggle funziona + actions history
- M6: Advanced Tools (5h) → CSV export + Dividends calendar

---

## 🚀 Action Plan (Immediate Next Steps)

**Step 1**: Frontend Portfolio Data Integration (M1 - 2h)
```javascript
// app/portfolio/page.jsx
useEffect(() => {
  const fetchPortfolio = async () => {
    const res = await fetch(`${API_URL}/portfolio/${userId}`)
    const data = await res.json()
    setPortfolioStats({
      totalValue: data.total_value,
      pnlToday: data.pnl_absolute,
      pnlPercent: data.pnl_percent,
      riskScore: data.risk_score
    })
  }
  fetchPortfolio()
}, [userId])
```

**Step 2**: Performance Analytics Engine (M5 - 12h)
```python
# New file: core/api/portfolio_performance.py
@router.get("/portfolio/performance/{user_id}")
def get_performance(user_id: str, timeframe: str = "1M"):
    # 1. Query shadow_portfolio_snapshots (historical timeseries)
    # 2. Fetch benchmark data (yfinance SPY/QQQ with Redis cache)
    # 3. Calculate metrics (total_return, max_drawdown, sharpe, volatility)
    # 4. Return JSON {timeseries: [...], metrics: {...}}
```

**Step 3**: Test with real data
```bash
# Create test snapshot
curl -X POST http://localhost:8011/shadow/portfolio/snapshot \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user", "tickers": ["AAPL", "MSFT", "TSLA"]}'

# Verify frontend
http://localhost:3000/portfolio
```

---

## ✅ Success Criteria

**M1 Complete** when:
- [ ] Header shows real `totalValue` from API
- [ ] P&L today calculated from snapshot comparison
- [ ] All portfolio stats (risk, diversification) from DB

**M5 Complete** when:
- [ ] Performance chart renders 30-day timeseries (portfolio + SPY + QQQ)
- [ ] Metrics cards show real Total Return, Max Drawdown, Sharpe, Volatility
- [ ] Timeframe selector (7D/1M/3M/1Y/ALL) works

**M2 Complete** when:
- [ ] Guardian tab shows real insights from guardian_insights table
- [ ] Severity badges (critical/high/medium/low) color-coded
- [ ] Click "View Details" opens insight detail modal

**M4 Complete** when:
- [ ] VaR metric card shows real 95% confidence value
- [ ] Correlation matrix populated with real ticker correlations
- [ ] Risk radar chart shows 6 real dimensions (market, volatility, liquidity, concentration, correlation, drawdown)

**M3 Complete** when:
- [ ] Toggle button reads/writes user_autopilot_settings table
- [ ] Risk slider (1-10) updates risk_tolerance in DB
- [ ] Actions timeline shows real autopilot_actions history
- [ ] Cron job runs hourly if autopilot enabled

**M6 Complete** when:
- [ ] CSV export downloads real portfolio holdings
- [ ] Dividends calendar shows upcoming payments (yfinance)

---

**Date**: January 24, 2026  
**Status**: ✅ AUDIT COMPLETE - Ready for implementation  
**Estimated Savings**: 24 hours (-40% vs original estimate)
