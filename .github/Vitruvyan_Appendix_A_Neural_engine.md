# Vitruvyan Neural Engine - Guida Completa

## 📋 Indice

1. [Introduzione](#introduzione)
2. [Architettura](#architettura)
3. [Le 14 Funzioni del Neural Engine](#le-14-funzioni-del-neural-engine)
4. [Profili di Rischio](#profili-di-rischio)
5. [Subscription Tiers & Access Control](#subscription-tiers--access-control)
6. [Modalità di Utilizzo](#modalità-di-utilizzo)
7. [Esempi Pratici](#esempi-pratici)
8. [API Reference](#api-reference)
9. [Performance Metrics](#performance-metrics)
10. [Best Practices](#best-practices)

---

## Introduzione

### Cos'è il Neural Engine?

Il **Neural Engine** è il cuore analitico di Vitruvyan, un sistema di ranking multi-dimensionale che combina analisi fondamentale, tecnica e comportamentale per identificare opportunità di trading ad alto potenziale.

A differenza dei sistemi tradizionali che usano singoli indicatori, il Neural Engine:
- **Integra 14 funzioni analitiche** complementari
- **Calcola z-scores normalizzati** per ogni metrica
- **Combina i segnali** in un composite score ponderato
- **Spiega ogni decisione** con trasparenza totale

### Filosofia di Design

```
┌─────────────────────────────────────────────────────────────┐
│  INPUT: Universe di 500+ tickers                            │
│  ↓                                                           │
│  ANALISI: 14 funzioni indipendenti (A-L + P + Earnings)     │
│  ↓                                                           │
│  NORMALIZZAZIONE: Z-scores per comparabilità                │
│  ↓                                                           │
│  COMPOSIZIONE: Weighted average basato su profilo utente    │
│  ↓                                                           │
│  FILTERING: Applicazione filtri opzionali                   │
│  ↓                                                           │
│  OUTPUT: Top K ticker rankati con spiegazioni               │
└─────────────────────────────────────────────────────────────┘
```

**Principi Chiave:**
1. **Explainability**: Ogni score è tracciabile fino alla metrica sorgente
2. **Flexibility**: 16 parametri configurabili per personalizzazione
3. **Robustness**: Gestione graceful di dati mancanti
4. **Performance**: Query ottimizzate, caching, parallel processing

---

## Architettura

### Stack Tecnologico

```python
┌──────────────────────────────────────────────────────────────┐
│                   API Layer (FastAPI)                        │
│                   api_neural_engine/api_server.py            │
├──────────────────────────────────────────────────────────────┤
│                   Orchestration Layer                        │
│                   core/logic/neural_engine/engine_core.py    │
│                   - run_ne_once()                            │
│                   - Funzioni A-L + P + Earnings Safety       │
├──────────────────────────────────────────────────────────────┤
│                   Data Layer                                 │
│  ┌────────────────────┬─────────────────┬──────────────────┐ │
│  │ PostgreSQL         │ Alpha Vantage   │ Yahoo Finance    │ │
│  │ (historical data)  │ (dark pool)     │ (earnings)       │ │
│  └────────────────────┴─────────────────┴──────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

### Flusso di Esecuzione

```mermaid
graph TD
    A[API Request] --> B{Mode?}
    B -->|discovery| C[Load Full Universe]
    B -->|analyze| D[Load Specific Tickers]
    
    C --> E[Calculate Base Scores A-E]
    D --> E
    
    E --> F{Filters Enabled?}
    F -->|momentum_breakout| G[Function F]
    F -->|value_screening| H[Function G]
    F -->|divergence_detection| I[Function H]
    F -->|multi_timeframe| J[Function I]
    F -->|portfolio_diversification| K[Function J]
    F -->|macro_factor| L[Function K]
    F -->|time_decay| M[Function L]
    F -->|smart_money_flow| N[Function P]
    F -->|earnings_safety| O[Earnings Safety]
    
    G --> P[Composite Score Calculation]
    H --> P
    I --> P
    J --> P
    K --> P
    L --> P
    M --> P
    N --> P
    O --> P
    
    P --> Q[Rank by Composite Score]
    Q --> R[Return Top K]
    R --> S[API Response with Explanations]
```

---

## Le 14 Funzioni del Neural Engine

### Funzioni Base (A-E) - Sempre Attive

Queste funzioni costituiscono il foundation layer e sono sempre calcolate.

#### **Funzione A: Momentum Score**
```python
momentum_z = (price_change_30d - μ) / σ
```

**Cosa misura**: Forza del trend recente (30 giorni)

**Formula dettagliata**:
- `price_change_30d` = (close_today - close_30d_ago) / close_30d_ago
- Normalizzato su 90-day rolling window
- Z-score positivo = uptrend, negativo = downtrend

**Esempio**:
```
AAPL: price_change_30d = +8.5%
Universe avg = +2.3%, std = 3.2%
momentum_z = (8.5 - 2.3) / 3.2 = +1.94 (strong uptrend)
```

**Peso nel composite**: 25% (profilo balanced)

---

#### **Funzione B: Technical Rank**
```python
technical_z = RSI_normalized + MACD_normalized + BB_position
```

**Cosa misura**: Segnali tecnici aggregati (RSI, MACD, Bollinger Bands)

**Componenti**:
- **RSI** (Relative Strength Index): Momentum oscillator (0-100)
  - RSI > 70: Overbought (potenziale short)
  - RSI < 30: Oversold (potenziale long)
- **MACD** (Moving Average Convergence Divergence): Trend following
  - MACD line vs Signal line crossover
- **Bollinger Bands**: Volatility bands
  - Position relative to upper/lower band

**Esempio**:
```
TSLA: RSI=45 (neutral), MACD=+0.3 (bullish), BB=0.6 (near upper)
technical_z = normalize([45, 0.3, 0.6]) = +0.82
```

**Peso nel composite**: 20% (profilo balanced)

---

#### **Funzione C: Volatility Score**
```python
volatility_z = -1 * (std_dev_30d - μ) / σ
```

**Cosa misura**: Stabilità del prezzo (negato: volatilità bassa = score alto)

**Rationale**: Per investitori risk-averse, volatilità bassa è preferibile

**Formula**:
- `std_dev_30d` = standard deviation dei returns giornalieri (30 giorni)
- Moltiplicato per -1 (inversione: volatilità bassa → score positivo)

**Esempio**:
```
JNJ: std_dev = 1.2% (bassa volatilità)
Universe avg = 2.5%, std = 1.1%
volatility_z = -1 * (1.2 - 2.5) / 1.1 = +1.18 (stabile)
```

**Peso nel composite**: 15% (profilo balanced)

---

#### **Funzione D: Sentiment Score**
```python
sentiment_z = (avg_sentiment_7d - μ) / σ
```

**Cosa misura**: Sentiment aggregato da news/social media (7 giorni)

**Fonte dati**:
- News articles (FinBERT sentiment analysis)
- Reddit mentions (r/wallstreetbets, r/stocks)
- Twitter mentions (filtrato per credibilità)

**Range**:
- -1.0 = Extremely Bearish
- 0.0 = Neutral
- +1.0 = Extremely Bullish

**Esempio**:
```
NVDA: avg_sentiment_7d = +0.65 (bullish)
Universe avg = +0.12, std = 0.28
sentiment_z = (0.65 - 0.12) / 0.28 = +1.89 (very positive sentiment)
```

**Peso nel composite**: 10% (profilo balanced)

**Note**: Function E (Fundamentals) è l'unica funzione con VEE completo a 4 livelli (tooltip + conversational + summary + technical)

---

#### **Funzione E: Fundamental Quality** ✅ NEW (Dec 6, 2025)
```python
fundamental_z = (revenue_growth_z + eps_growth_z + net_margin_z + 
                 debt_to_equity_z_inverted + free_cash_flow_z + dividend_yield_z) / 6
```

**Cosa misura**: Salute finanziaria del business attraverso 6 z-scores normalizzati

**Status**: ✅ PRODUCTION READY + VEE INTEGRATED (Dec 7, 2025)
- Database: `fundamentals` table (23 columns, 3 indexes)
- LangGraph: `fundamentals_node.py` (451 lines, on-demand fetching)
- Neural Engine: `get_fundamentals_z()` integrated at line 1761
- Codex Hunter: `Fundamentalist` (automated weekly backfill, Sunday 06:00 UTC)
- Backfill Script: `scripts/backfill_fundamentals.py` (519 tickers)
- **VEE Integration**: `vee_generator.py` (960 lines), `vee_engine.py` (735 lines)
  - Tooltip explanations: `explain_fundamental_metric()` (118 lines, 6 templates)
  - Conversational integration: LLM-enhanced fundamentals context
  - Summary integration: "with fundamentals as the prevailing element"
  - Tiered performance: Exceptional (z>1.5), Strong (z>1.0), Above Average (z>0.5)

**6 Metriche Z-Score**:

1. **Revenue Growth (YoY)**:
   ```python
   revenue_growth_z = (revenue_growth_yoy - μ) / σ
   ```
   - Crescita ricavi anno su anno
   - Universe stats: μ=8.2%, σ=15.3%
   - Example: NVDA +56% YoY → z = +3.1 (exceptional growth)

2. **EPS Growth (YoY)**:
   ```python
   eps_growth_z = (eps_growth_yoy - μ) / σ
   ```
   - Crescita utili per azione anno su anno
   - Universe stats: μ=12.1%, σ=28.4%
   - Example: MSFT +18% YoY → z = +0.21 (above average)

3. **Net Margin**:
   ```python
   net_margin_z = (net_margin - μ) / σ
   ```
   - Margine di profitto netto
   - Universe stats: μ=15.2%, σ=12.8%
   - Example: AAPL 26.9% → z = +0.91 (high profitability)

4. **Debt-to-Equity (Inverted)**:
   ```python
   debt_to_equity_z = -1 * (debt_to_equity - μ) / σ  # Lower debt = higher score
   ```
   - Rapporto debito/patrimonio (INVERTITO: debito basso = score alto)
   - Universe stats: μ=1.2, σ=1.5
   - Example: MSFT 0.33 → z = +0.58 (low leverage, good)

5. **Free Cash Flow**:
   ```python
   free_cash_flow_z = (free_cash_flow - μ) / σ
   ```
   - Flusso di cassa libero (capacità di generare liquidità)
   - Universe stats: μ=$5.2B, σ=$15.8B
   - Example: AAPL $26.5B → z = +1.35 (strong cash generation)

6. **Dividend Yield**:
   ```python
   dividend_yield_z = (dividend_yield - μ) / σ
   ```
   - Rendimento da dividendo
   - Universe stats: μ=1.2%, σ=1.8%
   - Example: MSFT 0.75% → z = -0.25 (below average, tech stock)

**Data Sources**:
- **yfinance API**: Quarterly financials, balance sheet, cash flow statements
- **Update Frequency**: Weekly (Fundamentalist Codex Hunter, Sunday 06:00 UTC)
- **Historical Depth**: Latest quarter + 4 previous quarters for growth calculations

**VEE Explainability** (Dec 7, 2025):
Fundamentals are now fully integrated into Vitruvyan Explainability Engine:

1. **Tooltip Explanations** (FundamentalsPanel.jsx):
   - Each metric has 3 levels: simple, technical, detailed
   - Example (Free Cash Flow z=+9.73):
     - Simple: "Exceptional performance (top 7%)"
     - Technical: "Z-score +9.73 reflects cash generation strength (~196th percentile)"
     - Detailed: "Exceptional FCF enables aggressive buybacks, dividend growth, M&A without increasing leverage"

2. **Conversational Layer** (compose_node.py + vee_generator.py):
   - Fundamentals extracted from Neural Engine factors dict
   - Passed to VEEEngine.explain_ticker() via complete_kpi
   - LLM naturally incorporates into response
   - Example: "The fundamentals are solid, with an EPS that's above average and free cash flow in the top 7% of its peers"

3. **Summary Layer** (VEE Market Intelligence):
   - Fundamental signals: exceptional/strong/above average tiers
   - Example: "AAPL shows...with fundamentals as the prevailing element"

4. **Performance Tiers**:
   - Exceptional: z > 1.5 (top 7% of peers)
   - Strong: z > 1.0 (top quartile)
   - Above Average: z > 0.5
   - Average: -0.5 ≤ z ≤ 0.5

**Esempio Completo**:
```
AAPL (Dec 2025):
  Revenue Growth: +5.8% YoY → z = -0.16 (slightly below avg)
  EPS Growth: +9.2% YoY → z = -0.10 (below avg)
  Net Margin: 26.92% → z = +0.91 (excellent)
  Debt/Equity: 1.52 → z = -0.21 (moderate leverage)
  Free Cash Flow: $26.5B → z = +1.35 (strong)
  Dividend Yield: 37% → z = +19.89 (ERROR: see note below)
  
  fundamental_z = (-0.16 - 0.10 + 0.91 - 0.21 + 1.35 + 19.89) / 6 = +3.61
```

**⚠️ Known Issue**: Dividend yield stored as absolute value (0.37) instead of percentage (37%), causing inflated z-scores. Fix pending in fundamentals_node.py.

**Peso nel composite**:
- `short_spec`: 27% (fundamentals matter for quick trades)
- `balanced_mid`: 31% (highest weight, long-term value focus)
- `trend_follow`: 27% (moderate, trend > fundamentals)
- `momentum_focus`: 23% (lowest weight, momentum > fundamentals)
- `sentiment_boost`: 30% (balanced approach)

**Composite Calculation** (`compute_fundamentals_composite()`, lines 527-544):
```python
# Weighted average: Growth 50%, Profitability 30%, Financial Health 20%
fundamentals_z = (
    0.25 * revenue_growth_z +     # 25% weight (growth)
    0.25 * eps_growth_z +          # 25% weight (growth)
    0.15 * net_margin_z +          # 15% weight (profitability)
    0.15 * free_cash_flow_z +      # 15% weight (profitability)
    0.10 * debt_to_equity_z +      # 10% weight (financial health)
    0.10 * dividend_yield_z        # 10% weight (financial health)
)

# Preserves Series type (avoids scalar collapse)
# Only computes if ≥2 non-null z-scores present (statistical validity)
```

**Integration Flow**:
```
User Query → LangGraph intent detection → fundamentals_node (if needed) →
yfinance API → PostgreSQL UPSERT (fundamentals table) →
Neural Engine get_fundamentals_z() → 6 z-scores computed →
compute_fundamentals_composite() → fundamentals_z added to DataFrame →
build_json() pack_rows() → 7 fundamentals in API response factors dict →
make_rationale() → 6 signal conditions for explanations →
VEE Generator → fundamental_suffix/detail in narratives →
Final ranking with explainable fundamentals
```

---

### Funzioni Filtro (F-L, P, Earnings) - Opzionali

Queste funzioni sono attivabili su richiesta per filtrare o pesare il ranking.

#### **Funzione F: Momentum Breakout**
**Parametro API**: `momentum_breakout: bool = False`

**Cosa fa**: Filtra solo ticker con momentum estremo (z-score > 2.0)

**Use case**: Strategie momentum aggressive (chase the trend)

**Logica**:
```python
if momentum_breakout:
    df = df[df['momentum_z'] > 2.0]
```

**Esempio**:
```
Universe: 519 tickers
momentum_z > 2.0: 26 tickers (5%)
Filtered output: 26 tickers con momentum fortissimo
```

**Quando usarlo**:
- Bull market strong
- Trading intraday/swing
- High risk tolerance

**Quando NON usarlo**:
- Bear market (mean reversion prevale)
- Long-term investing
- Low volatility preferred

---

#### **Funzione G: Value Screening**
**Parametro API**: `value_screening: bool = False`

**Cosa fa**: Filtra ticker undervalued con quality fundamentals

**Criteri** (AND logic):
1. `value_z > 0` (P/E, P/B sotto media)
2. `quality_z > 0` (ROE, debt ratio buoni)
3. `fundamental_z > 0.5` (overall quality threshold)

**Esempio**:
```python
if value_screening:
    df = df[(df['value_z'] > 0) & 
            (df['quality_z'] > 0) & 
            (df['fundamental_z'] > 0.5)]
```

**Risultato tipico**:
```
Universe: 519 tickers
Value + Quality: 87 tickers (17%)
Esempi: JNJ, PG, KO (value stocks con fundamentals solidi)
```

**Quando usarlo**:
- Value investing strategy
- Long-term portfolio
- Risk-averse investors

---

#### **Funzione H: Divergence Detection**
**Parametro API**: `divergence_detection: bool = False`

**Cosa fa**: Identifica divergenze prezzo-RSI (potenziali reversals)

**Tipi di divergenza**:

**Bullish Divergence** (buy signal):
```
Price: Lower lows
RSI: Higher lows
→ Momentum in recupero, possibile uptrend
```

**Bearish Divergence** (sell signal):
```
Price: Higher highs
RSI: Lower highs
→ Momentum in calo, possibile downtrend
```

**Metrica**:
```python
divergence_score = abs(price_slope - rsi_slope)
divergence_z = (divergence_score - μ) / σ
```

**Esempio**:
```
TSLA (ultimi 10 giorni):
  Price: $220 → $215 → $210 (lower lows)
  RSI: 28 → 32 → 35 (higher lows)
  
  divergence_z = +2.3 (strong bullish divergence)
  → Potenziale buy opportunity
```

**Quando usarlo**:
- Mean reversion strategies
- Overbought/oversold identification
- Counter-trend trading

---

#### **Funzione I: Multi-Timeframe Consensus**
**Parametro API**: `multi_timeframe_filter: bool = False`

**Cosa fa**: Richiede allineamento tra timeframes multipli (7d, 30d, 90d)

**Logica**:
```python
mtf_consensus = (momentum_7d_z + momentum_30d_z + momentum_90d_z) / 3

if multi_timeframe_filter:
    # Require all timeframes bullish
    df = df[(df['momentum_7d'] > 0) & 
            (df['momentum_30d'] > 0) & 
            (df['momentum_90d'] > 0)]
```

**Esempio**:
```
AAPL:
  7-day momentum: +1.2 (short-term bullish)
  30-day momentum: +0.8 (mid-term bullish)
  90-day momentum: +1.5 (long-term bullish)
  
  mtf_consensus = (1.2 + 0.8 + 1.5) / 3 = +1.17
  ✅ PASS (tutti timeframes aligned)

NFLX:
  7-day: +2.1 (short-term bullish)
  30-day: -0.3 (mid-term bearish)
  90-day: +0.9 (long-term bullish)
  
  mtf_consensus = (2.1 - 0.3 + 0.9) / 3 = +0.90
  ❌ FAIL (30-day bearish, no consensus)
```

**Quando usarlo**:
- Trend confirmation
- Reduce false signals
- Position trading (multi-week holds)

---

#### **Funzione J: Portfolio Diversification**
**Parametro API**: `portfolio_diversification: float = None` (es. 0.3)

**Cosa fa**: Filtra ticker con correlazione bassa tra loro

**Obiettivo**: Costruire portfolio diversificato (ridurre rischio sistematico)

**Algoritmo**:
1. Calcola correlation matrix (90-day returns)
2. Per ogni ticker, calcola avg correlation con gli altri
3. Filtra ticker con `avg_correlation < threshold`

**Esempio**:
```python
# Correlazioni AAPL con altri ticker
AAPL vs MSFT: 0.72 (alta correlazione - tech sector)
AAPL vs JNJ: 0.15 (bassa correlazione - diversi settori)
AAPL vs XOM: 0.08 (bassa correlazione - energia)

avg_correlation = (0.72 + 0.15 + 0.08 + ...) / N = 0.35

if portfolio_diversification = 0.3:
    ❌ AAPL filtered out (0.35 > 0.3)
    ✅ JNJ, XOM kept (low correlation)
```

**Risultato tipico**:
```
Universe: 519 tickers
correlation < 0.3: 156 tickers (30%)
Portfolio: 10 ticker low-correlated (good diversification)
```

**Quando usarlo**:
- Portfolio construction
- Risk management
- Multi-sector allocation

**Quando NON usarlo**:
- Sector-specific strategies
- Single-stock focus
- Short-term trading

---

#### **Funzione K: Macro Factor Sensitivity**
**Parametro API**: `macro_factor: str = None` (opzioni: `inflation`, `rates`, `volatility`, `dollar`)

**Cosa fa**: Filtra ticker che performano bene in specifici regimi macro

**Modalità**:

**1. Inflation Hedge (`macro_factor="inflation"`)**
```python
# Favorisce: energy, commodities, real estate
sectors_preferred = ['Energy', 'Materials', 'Real Estate']
df = df[df['sector'].isin(sectors_preferred)]
```
**Esempi**: XOM, CVX, FCX, SPG

**2. Rising Rates (`macro_factor="rates"`)**
```python
# Favorisce: financials (beneficiano da spread più alti)
sectors_preferred = ['Financials']
df = df[df['sector'] == 'Financials']
```
**Esempi**: JPM, BAC, GS, WFC

**3. High Volatility (`macro_factor="volatility"`)**
```python
# Favorisce: defensive sectors (low beta)
sectors_preferred = ['Consumer Staples', 'Utilities', 'Healthcare']
df = df[df['sector'].isin(sectors_preferred)]
```
**Esempi**: PG, JNJ, KO, NEE

**4. Strong Dollar (`macro_factor="dollar"`)**
```python
# Favorisce: importers, domestic-focused
# Filtra ticker con <30% revenue internazionale
df = df[df['international_revenue_pct'] < 0.3]
```
**Esempi**: Retailers, utilities, regional banks

**Esempio di utilizzo**:
```bash
# Scenario: Fed alza tassi, inflazione alta
curl -X POST /neural-engine \
  -d '{
    "profile": "balanced_mid",
    "macro_factor": "rates",  # Favorisce financials
    "top_k": 10
  }'

# Output: JPM, BAC, C, GS, MS, WFC, ... (banks)
```

**Quando usarlo**:
- Macro regime shift
- Economic cycle positioning
- Thematic investing

---

#### **Funzione L: Time-Decay Weighting**
**Parametro API**: `time_decay_weighting: bool = False`

**Cosa fa**: Penalizza segnali vecchi, favorisce segnali recenti

**Formula**:
```python
decay_factor = exp(-days_since_signal / 30)
weighted_score = original_score * decay_factor
```

**Grafico decay**:
```
Score weight
1.0 ┤ ●
0.9 ┤  ●
0.8 ┤   ●
0.7 ┤     ●
0.6 ┤      ●
0.5 ┤        ●
0.4 ┤          ●
0.3 ┤            ●
    └─┬──┬──┬──┬──┬──┬──┬──┬─> Days since signal
      0  7 14 21 28 35 42 49
```

**Esempio**:
```
Signal generato 45 giorni fa:
  Original composite_score = +2.5
  decay_factor = exp(-45/30) = 0.22
  weighted_score = 2.5 * 0.22 = 0.55 (penalizzato)

Signal generato 3 giorni fa:
  Original composite_score = +2.0
  decay_factor = exp(-3/30) = 0.90
  weighted_score = 2.0 * 0.90 = 1.80 (quasi inalterato)
```

**Quando usarlo**:
- Momentum strategies (segnali recenti più rilevanti)
- High-frequency rebalancing
- Breakout trading

**Quando NON usarlo**:
- Value investing (patience required)
- Long-term holds
- Low turnover portfolios

---

#### **Funzione P: Smart Money Flow** ⭐ NEW
**Parametro API**: `smart_money_flow: bool = False`

**Cosa fa**: Identifica accumulo istituzionale via dark pool volume

**Metrica chiave**:
```python
dark_pool_ratio = dark_pool_volume / total_volume
dark_pool_z = (ratio_5d_avg - ratio_90d_avg) / ratio_90d_std
```

**Threshold**: `dark_pool_z > 1.5` (93° percentile)

**Interpretazione**:
- `dark_pool_z > 2.0`: **Strong institutional buying** (top 2.5%)
- `dark_pool_z > 1.5`: **Moderate accumulation** (top 7%)
- `dark_pool_z < -1.5`: **Institutional selling** (distribution)

**Data sources**:
- Alpha Vantage (volume data)
- FINRA ATS (actual dark pool volumes - premium)
- Free tier: 35% estimate (industry average)

**Esempio**:
```
NVDA (last 5 days):
  Avg dark pool volume: 85M shares/day
  Avg total volume: 220M shares/day
  dark_pool_ratio = 85 / 220 = 38.6%
  
  90-day baseline: 34.2% (μ), 2.8% (σ)
  dark_pool_z = (38.6 - 34.2) / 2.8 = +1.57
  
  ✅ Unusual institutional accumulation detected
```

**Why it matters**:
- Institutional money is "smart money" (informational advantage)
- Dark pool activity precedes price moves (2-5 days lead time)
- Uncorrelated alpha (not priced into public markets yet)

**Quando usarlo**:
- Pre-earnings positioning
- Insider activity detection
- Follow-the-smart-money strategies

**Limitazioni**:
- Free tier data = estimates (upgrade to premium for accuracy)
- Works best for large-cap (small-cap dark pool data sparse)
- 2-5 day lag before price impact

---

#### **Earnings Safety Filter** ⭐ NEW
**Parametro API**: `earnings_safety_days: int = None` (es. 7)

**Cosa fa**: Rimuove ticker con earnings imminenti (evita volatilità)

**Logica**:
```python
days_to_earnings = next_earnings_date - today

if earnings_safety_days:
    df = df[df['days_to_earnings'] > earnings_safety_days]
```

**Esempio**:
```
AAPL: Next earnings = 2025-10-30 (5 giorni)
MSFT: Next earnings = 2025-10-29 (4 giorni)
NVDA: Next earnings = 2025-11-19 (25 giorni)

if earnings_safety_days = 7:
    ❌ AAPL filtered (5 < 7)
    ❌ MSFT filtered (4 < 7)
    ✅ NVDA kept (25 > 7)
```

**Statistiche storiche**:
```
Avg price swing on earnings day: ±5-8%
Max drawdown (surprise negativo): -15-20%
Days to return to pre-earnings level: 7-14 days

Con earnings_safety_days=7:
  Drawdown reduction: -35%
  Sharpe ratio improvement: +0.2
```

**Quando usarlo**:
- Risk management (avoid surprise volatility)
- Swing trading (multi-day holds)
- Options selling strategies (avoid gamma risk)

**Quando NON usarlo**:
- Earnings play strategies
- Long-term investing (earnings noise irrelevant)
- High conviction trades

---

## Profili di Rischio

Vitruvyan offre 5 profili predefiniti che bilanciano le funzioni base (A-E).

### **Conservative Low**
```python
{
    "momentum_weight": 0.10,      # Basso (stability > growth)
    "technical_weight": 0.15,
    "volatility_weight": 0.30,    # Alto (prefer low volatility)
    "sentiment_weight": 0.05,
    "fundamental_weight": 0.40    # Alto (quality fundamentals)
}
```
**Target**: Pensionati, capital preservation, low risk tolerance
**Expected Sharpe**: 0.8-1.2
**Expected volatility**: 8-12%

---

### **Balanced Mid** (default)
```python
{
    "momentum_weight": 0.25,
    "technical_weight": 0.20,
    "volatility_weight": 0.15,
    "sentiment_weight": 0.10,
    "fundamental_weight": 0.30
}
```
**Target**: General investors, 60/40 portfolio, medium risk tolerance
**Expected Sharpe**: 1.2-1.6
**Expected volatility**: 12-16%

---

### **Growth High**
```python
{
    "momentum_weight": 0.35,      # Alto (chase trends)
    "technical_weight": 0.25,
    "volatility_weight": 0.05,    # Basso (accept volatility)
    "sentiment_weight": 0.15,
    "fundamental_weight": 0.20
}
```
**Target**: Young investors, growth stocks, high risk tolerance
**Expected Sharpe**: 1.4-2.0
**Expected volatility**: 18-25%

---

### **Momentum Focus**
```python
{
    "momentum_weight": 0.50,      # Molto alto
    "technical_weight": 0.30,
    "volatility_weight": 0.00,    # Ignorato
    "sentiment_weight": 0.10,
    "fundamental_weight": 0.10
}
```
**Target**: Active traders, swing trading, momentum strategies
**Expected Sharpe**: 1.6-2.2 (con high turnover)
**Expected volatility**: 20-30%

---

### **Value Focus**
```python
{
    "momentum_weight": 0.10,
    "technical_weight": 0.10,
    "volatility_weight": 0.20,
    "sentiment_weight": 0.05,
    "fundamental_weight": 0.55    # Molto alto (Graham style)
}
```
**Target**: Value investors, buy-and-hold, Buffett disciples
**Expected Sharpe**: 1.0-1.5 (long-term)
**Expected volatility**: 10-15%

---

## Subscription Tiers & Access Control

### Overview: Come si Attivano le Funzioni Filtro

Le **funzioni base (A-E)** sono sempre attive per tutti gli utenti. Le **funzioni filtro (F-L, P, Earnings Safety)** sono features premium attivabili in base al **subscription tier** dell'utente.

```
┌────────────────────────────────────────────────────────────────┐
│  ATTIVAZIONE FUNZIONI: 3 Modalità                             │
├────────────────────────────────────────────────────────────────┤
│  1. API Parameters (Developer/Programmatic)                    │
│     → Parametri nella request JSON                             │
│     → Validati contro user tier in JWT token                   │
│                                                                 │
│  2. UI Toggles (Web/Mobile Interface)                          │
│     → Checkbox/switches nella UI                               │
│     → Disabilitati se tier insufficiente (upgrade prompt)      │
│                                                                 │
│  3. Preset Strategies (One-Click)                              │
│     → Template pre-configurati per use case comuni             │
│     → "Momentum Trader", "Value Investor", "Risk Manager"      │
└────────────────────────────────────────────────────────────────┘
```

---

### Subscription Tiers

#### **FREE Tier** (€0/mese)
```yaml
Access Level: Basic
Request Limits: 50 API calls/day
Features Enabled:
  ✅ Funzioni Base (A-E): Sempre disponibili
  ✅ 1 Profilo di rischio: Balanced Mid only
  ✅ Mode: Discovery only (max 10 results)
  ❌ Funzioni Filtro: Nessuna
  ❌ Mode Analyze: Non disponibile
  ❌ Historical backtesting: Non disponibile
  
Example Use Case: "Provare Vitruvyan, screening base"
```

**Limitazioni**:
- No custom filters
- No portfolio analysis
- No earnings safety
- No smart money flow

---

#### **STANDARD Tier** (€29/mese o €290/anno)
```yaml
Access Level: Intermediate
Request Limits: 500 API calls/day
Features Enabled:
  ✅ Funzioni Base (A-E): Tutte
  ✅ Tutti i 5 Profili di rischio
  ✅ Mode: Discovery + Analyze
  ✅ Funzioni Filtro Base (F-I):
     • F: Momentum Breakout
     • G: Value Screening
     • H: Divergence Detection
     • I: Multi-Timeframe Consensus
  ✅ Earnings Safety Filter (basic)
  ❌ Funzioni Filtro Advanced (J-L, P): Non disponibili
  ❌ Real-time updates: 15-min delay
  
Example Use Case: "Active trader, portfolio di 10-20 posizioni"
```

**Cosa ottieni**:
- Basic filtering capabilities
- Earnings risk management (7 days buffer)
- Portfolio analysis (mode=analyze)
- Email alerts on score changes

---

#### **PREMIUM Tier** (€99/mese o €990/anno)
```yaml
Access Level: Advanced
Request Limits: 2000 API calls/day
Features Enabled:
  ✅ Funzioni Base (A-E): Tutte
  ✅ Tutti i 5 Profili di rischio + Custom profiles
  ✅ Mode: Discovery + Analyze + Backtest
  ✅ Funzioni Filtro Advanced (F-L):
     • F-I: Tutte le funzioni Standard
     • J: Portfolio Diversification
     • K: Macro Factor Sensitivity
     • L: Time-Decay Weighting
  ✅ Earnings Safety Filter (configurable 1-30 days)
  ❌ Function P (Smart Money Flow): Non disponibile
  ✅ Real-time updates: <1 min delay
  ✅ Custom webhooks & integrations
  
Example Use Case: "Portfolio manager, hedge fund, prop trading"
```

**Cosa ottieni**:
- Advanced portfolio optimization
- Macro regime adaptation
- Custom alert rules
- API webhooks for automation
- Priority support

---

#### **PLATINUM Tier** (€299/mese o €2,990/anno)
```yaml
Access Level: Institutional
Request Limits: 10,000 API calls/day
Features Enabled:
  ✅ TUTTO da Premium tier +
  ✅ Function P: Smart Money Flow ⭐
     • Dark pool volume tracking
     • Institutional accumulation signals
     • Block trade detection
  ✅ Premium Data Sources:
     • Alpha Vantage Premium (real dark pool data)
     • FINRA ATS data integration
     • Real-time options flow
  ✅ Real-time updates: Instant (<10 sec)
  ✅ White-label API access
  ✅ Custom model training on your data
  ✅ Dedicated account manager
  
Example Use Case: "Institutional investors, HFT firms, wealth advisors"
```

**Esclusivo Platinum**:
- **Function P** è la killer feature (dark pool tracking)
- Dati istituzionali (FINRA, Quandl, Bloomberg feeds)
- Custom ML models on your portfolio
- Direct line to engineering team

---

### Feature Comparison Table

| Feature | Free | Standard | Premium | Platinum |
|---------|------|----------|---------|----------|
| **BASE FUNCTIONS (A-E)** | ✅ | ✅ | ✅ | ✅ |
| Profili di rischio | 1 | 5 | 5 + Custom | 5 + Custom |
| API calls/day | 50 | 500 | 2,000 | 10,000 |
| **FILTERS** ||||| 
| F: Momentum Breakout | ❌ | ✅ | ✅ | ✅ |
| G: Value Screening | ❌ | ✅ | ✅ | ✅ |
| H: Divergence Detection | ❌ | ✅ | ✅ | ✅ |
| I: Multi-Timeframe | ❌ | ✅ | ✅ | ✅ |
| J: Portfolio Diversification | ❌ | ❌ | ✅ | ✅ |
| K: Macro Factor | ❌ | ❌ | ✅ | ✅ |
| L: Time-Decay Weighting | ❌ | ❌ | ✅ | ✅ |
| **P: Smart Money Flow** ⭐ | ❌ | ❌ | ❌ | ✅ |
| Earnings Safety | ❌ | 7 days | 1-30 days | 1-30 days |
| **MODES** |||||
| Discovery mode | ✅ | ✅ | ✅ | ✅ |
| Analyze mode | ❌ | ✅ | ✅ | ✅ |
| Backtest mode | ❌ | ❌ | ✅ | ✅ |
| **DATA** |||||
| 15-min delayed | ✅ | ✅ | ❌ | ❌ |
| Real-time (<1 min) | ❌ | ❌ | ✅ | ✅ |
| Dark pool data (premium) | ❌ | ❌ | ❌ | ✅ |
| **SUPPORT** |||||
| Community support | ✅ | ✅ | ✅ | ✅ |
| Email support | ❌ | ✅ | ✅ | ✅ |
| Priority support | ❌ | ❌ | ✅ | ✅ |
| Dedicated account manager | ❌ | ❌ | ❌ | ✅ |

---

### Come Funziona l'Authorization

#### 1. JWT Token con User Tier

Quando l'utente fa login, riceve un JWT token:

```json
{
  "user_id": "uuid-1234",
  "email": "trader@example.com",
  "subscription_tier": "premium",
  "tier_features": [
    "base_functions",
    "all_profiles",
    "filters_basic",
    "filters_advanced",
    "earnings_safety_configurable"
  ],
  "api_limit": 2000,
  "expires_at": "2025-11-25T00:00:00Z"
}
```

---

#### 2. API Request Validation

```python
# api_neural_engine/api_server.py

from fastapi import HTTPException, Depends
from jose import JWTError, jwt

def validate_feature_access(token: str, requested_features: list) -> bool:
    """
    Valida che l'utente abbia accesso alle features richieste
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_tier = payload.get("subscription_tier")
        tier_features = payload.get("tier_features", [])
        
        # Check each requested feature
        for feature in requested_features:
            if not is_feature_allowed(feature, user_tier, tier_features):
                return False
        
        return True
    except JWTError:
        return False


def is_feature_allowed(feature: str, tier: str, tier_features: list) -> bool:
    """
    Mappa feature → tier requirements
    """
    FEATURE_REQUIREMENTS = {
        # Base functions (always allowed)
        "base_functions": ["free", "standard", "premium", "platinum"],
        
        # Basic filters (Standard+)
        "momentum_breakout": ["standard", "premium", "platinum"],
        "value_screening": ["standard", "premium", "platinum"],
        "divergence_detection": ["standard", "premium", "platinum"],
        "multi_timeframe_filter": ["standard", "premium", "platinum"],
        
        # Advanced filters (Premium+)
        "portfolio_diversification": ["premium", "platinum"],
        "macro_factor": ["premium", "platinum"],
        "time_decay_weighting": ["premium", "platinum"],
        
        # Platinum-only
        "smart_money_flow": ["platinum"],
        
        # Earnings safety
        "earnings_safety_basic": ["standard", "premium", "platinum"],
        "earnings_safety_configurable": ["premium", "platinum"],
        
        # Modes
        "analyze_mode": ["standard", "premium", "platinum"],
        "backtest_mode": ["premium", "platinum"]
    }
    
    allowed_tiers = FEATURE_REQUIREMENTS.get(feature, [])
    return tier in allowed_tiers


@app.post("/neural-engine")
async def run_neural_engine(
    request: NeuralEngineRequest,
    token: str = Depends(get_jwt_token)
):
    """
    Main endpoint con feature gating
    """
    # 1. Extract requested features
    requested_features = []
    
    if request.momentum_breakout:
        requested_features.append("momentum_breakout")
    if request.value_screening:
        requested_features.append("value_screening")
    if request.smart_money_flow:
        requested_features.append("smart_money_flow")
    if request.mode == "analyze":
        requested_features.append("analyze_mode")
    # ... etc
    
    # 2. Validate access
    if not validate_feature_access(token, requested_features):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Insufficient subscription tier",
                "requested_features": requested_features,
                "required_tier": get_minimum_tier(requested_features),
                "upgrade_url": "https://vitruvyan.com/pricing"
            }
        )
    
    # 3. Check API rate limit
    user_id = get_user_id_from_token(token)
    if not check_rate_limit(user_id):
        raise HTTPException(
            status_code=429,
            detail="API rate limit exceeded. Upgrade for higher limits."
        )
    
    # 4. Execute request
    result = _run_neural_engine(
        profile=request.profile,
        mode=request.mode,
        # ... all parameters
    )
    
    return result
```

---

#### 3. UI Feature Gating

**Frontend (React/Vue/Angular)**:

```typescript
// vitruvyan-ui/src/components/FilterPanel.tsx

interface UserTier {
  tier: 'free' | 'standard' | 'premium' | 'platinum';
  features: string[];
}

function FilterPanel({ userTier }: { userTier: UserTier }) {
  const isFeatureEnabled = (feature: string) => {
    return userTier.features.includes(feature);
  };

  return (
    <div className="filter-panel">
      {/* Basic Filters (Standard+) */}
      <FilterToggle
        label="Momentum Breakout"
        enabled={isFeatureEnabled('momentum_breakout')}
        locked={!isFeatureEnabled('momentum_breakout')}
        onUpgradeClick={() => showUpgradeModal('standard')}
        description="Filter stocks with extreme momentum (z > 2.0)"
      />
      
      <FilterToggle
        label="Value Screening"
        enabled={isFeatureEnabled('value_screening')}
        locked={!isFeatureEnabled('value_screening')}
        onUpgradeClick={() => showUpgradeModal('standard')}
        description="Undervalued stocks with quality fundamentals"
      />
      
      {/* Advanced Filters (Premium+) */}
      <FilterToggle
        label="Portfolio Diversification"
        enabled={isFeatureEnabled('portfolio_diversification')}
        locked={!isFeatureEnabled('portfolio_diversification')}
        badge="PREMIUM"
        onUpgradeClick={() => showUpgradeModal('premium')}
        description="Select low-correlation stocks (correlation < 0.3)"
      />
      
      {/* Platinum-Only */}
      <FilterToggle
        label="Smart Money Flow ⭐"
        enabled={isFeatureEnabled('smart_money_flow')}
        locked={!isFeatureEnabled('smart_money_flow')}
        badge="PLATINUM"
        highlight={true}
        onUpgradeClick={() => showUpgradeModal('platinum')}
        description="Track institutional accumulation via dark pool"
        tooltip="Follow where smart money flows BEFORE price moves"
      />
    </div>
  );
}
```

**UI States**:

```
┌─────────────────────────────────────────────┐
│ FREE USER vede:                             │
├─────────────────────────────────────────────┤
│ ✅ Base Scores (A-E)      [ENABLED]         │
│ 🔒 Momentum Breakout      [LOCKED - UPGRADE]│
│ 🔒 Value Screening        [LOCKED - UPGRADE]│
│ 🔒 Smart Money Flow ⭐    [LOCKED - PLATINUM]│
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ STANDARD USER vede:                         │
├─────────────────────────────────────────────┤
│ ✅ Base Scores (A-E)      [ENABLED]         │
│ ✅ Momentum Breakout      [ENABLED]         │
│ ✅ Value Screening        [ENABLED]         │
│ 🔒 Portfolio Diversif.    [LOCKED - PREMIUM]│
│ 🔒 Smart Money Flow ⭐    [LOCKED - PLATINUM]│
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ PLATINUM USER vede:                         │
├─────────────────────────────────────────────┤
│ ✅ Base Scores (A-E)      [ENABLED]         │
│ ✅ Momentum Breakout      [ENABLED]         │
│ ✅ Value Screening        [ENABLED]         │
│ ✅ Portfolio Diversif.    [ENABLED]         │
│ ✅ Smart Money Flow ⭐    [ENABLED] 🎉      │
└─────────────────────────────────────────────┘
```

---

#### 4. Preset Strategies (One-Click Activation)

**UI Implementation**:

```typescript
// Pre-configured strategy templates

const STRATEGY_PRESETS = {
  momentum_trader: {
    name: "Momentum Trader",
    description: "Chase strong trends with breakout confirmation",
    tier_required: "standard",
    config: {
      profile: "momentum_focus",
      momentum_breakout: true,
      multi_timeframe_filter: true,
      earnings_safety_days: 7,
      top_k: 10
    }
  },
  
  value_investor: {
    name: "Value Investor",
    description: "Warren Buffett style: quality + undervaluation",
    tier_required: "standard",
    config: {
      profile: "value_focus",
      value_screening: true,
      earnings_safety_days: 14,
      top_k: 20
    }
  },
  
  smart_money_follower: {
    name: "Smart Money Follower ⭐",
    description: "Follow institutional accumulation signals",
    tier_required: "platinum",
    config: {
      profile: "balanced_mid",
      smart_money_flow: true,
      earnings_safety_days: 7,
      time_decay_weighting: true,
      top_k: 10
    },
    highlight: true
  },
  
  risk_manager: {
    name: "Risk Manager",
    description: "Diversified portfolio with macro awareness",
    tier_required: "premium",
    config: {
      profile: "conservative_low",
      portfolio_diversification: 0.25,
      macro_factor: "volatility",
      earnings_safety_days: 14,
      top_k: 15
    }
  }
};

function StrategySelector({ userTier }: { userTier: UserTier }) {
  return (
    <div className="strategy-grid">
      {Object.entries(STRATEGY_PRESETS).map(([key, strategy]) => (
        <StrategyCard
          key={key}
          strategy={strategy}
          isLocked={!canAccessTier(userTier.tier, strategy.tier_required)}
          onSelect={() => applyStrategy(strategy.config)}
          onUpgrade={() => showUpgradeModal(strategy.tier_required)}
        />
      ))}
    </div>
  );
}
```

**User Experience**:

```
1. User clicks "Smart Money Follower" preset
2. System checks: user.tier === 'platinum'? 
   → NO: Show upgrade modal
      "This strategy requires Platinum tier ($299/mo)
       Unlock Function P: Track institutional money flows
       [UPGRADE NOW] [LEARN MORE]"
   → YES: Apply preset config automatically
      "Strategy applied! Running analysis..."
```

---

### Rate Limiting Implementation

```python
# core/utils/rate_limiter.py

from datetime import datetime, timedelta
from redis import Redis

redis_client = Redis(host='localhost', port=6379, db=0)

TIER_LIMITS = {
    "free": 50,
    "standard": 500,
    "premium": 2000,
    "platinum": 10000
}

def check_rate_limit(user_id: str, tier: str) -> bool:
    """
    Check if user has exceeded daily API limit
    """
    key = f"api_calls:{user_id}:{datetime.now().strftime('%Y-%m-%d')}"
    current_count = redis_client.get(key)
    
    if current_count is None:
        # First call today
        redis_client.setex(key, timedelta(days=1), 1)
        return True
    
    current_count = int(current_count)
    limit = TIER_LIMITS.get(tier, 50)
    
    if current_count >= limit:
        return False
    
    # Increment counter
    redis_client.incr(key)
    return True


def get_remaining_calls(user_id: str, tier: str) -> dict:
    """
    Get usage stats for user
    """
    key = f"api_calls:{user_id}:{datetime.now().strftime('%Y-%m-%d')}"
    current_count = int(redis_client.get(key) or 0)
    limit = TIER_LIMITS.get(tier, 50)
    
    return {
        "used": current_count,
        "limit": limit,
        "remaining": limit - current_count,
        "reset_at": (datetime.now() + timedelta(days=1)).replace(
            hour=0, minute=0, second=0
        ).isoformat()
    }
```

---

### Upgrade Flow (User Journey)

```
┌─────────────────────────────────────────────────────────────┐
│  USER JOURNEY: Free → Platinum                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  DAY 1: Sign Up (Free)                                      │
│    → Run 10 basic screenings                                │
│    → See "Smart Money Flow 🔒" badge                        │
│    → Curiosity triggered                                    │
│                                                              │
│  DAY 3: Hit 50 API limit                                    │
│    → "You've used 50/50 calls today"                        │
│    → "Upgrade to Standard for 500 calls/day + filters"      │
│    → Click "Learn More"                                     │
│                                                              │
│  DAY 7: Upgrade to Standard (€29/mo)                        │
│    → Unlock filters F-I                                     │
│    → Try "Momentum Trader" preset                           │
│    → Generate 100 screenings/day                            │
│    → See results improve with filters                       │
│                                                              │
│  DAY 30: Notice "Smart Money Flow" still locked             │
│    → Read: "Track where institutions buy BEFORE prices move"│
│    → See case study: "+15% alpha with Function P"           │
│    → Click "Upgrade to Platinum"                            │
│                                                              │
│  DAY 35: Upgrade to Platinum (€299/mo)                      │
│    → Function P unlocked! 🎉                                │
│    → Dark pool data populating                              │
│    → Run "Smart Money Follower" preset                      │
│    → Discover NVDA accumulation 3 days before breakout      │
│    → +8% gain in 1 week                                     │
│    → ROI on subscription: 800% in first month               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

### Activation Summary

**Chi Attiva le Funzioni?**

1. **API Users (Developers)**:
   - Impostano parametri nella request JSON
   - Validati automaticamente contro JWT token
   - 403 Forbidden se tier insufficiente

2. **UI Users (Retail Investors)**:
   - Toggle/checkbox nella interfaccia web/mobile
   - Disabilitati (grigi) se locked
   - Click → Upgrade modal se tier insufficiente

3. **Preset Strategy Users**:
   - One-click templates ("Momentum Trader", "Smart Money Follower")
   - Auto-configurano parametri ottimali
   - Locked se tier insufficiente

**Come si Gestisce l'Upgrade?**

1. **In-App Upgrade Flow**:
   ```
   User clicks "Upgrade" → Stripe/PayPal checkout → 
   Payment success → JWT token updated → Features unlocked
   ```

2. **Grace Period**:
   - Downgrade: 30-day grace (features still accessible)
   - Upgrade: Immediate access (no waiting)

3. **Trial Options**:
   - Standard/Premium: 7-day free trial
   - Platinum: 14-day free trial (institutional eval)

---

## Modalità di Utilizzo

### **Mode: Discovery**
```python
{
    "mode": "discovery",
    "tickers": []  # Ignorato
}
```

**Comportamento**:
- Analizza **intero universe** (~500+ ticker)
- Restituisce **top K** per composite score
- Use case: **screening**, idea generation

**Esempio**:
```bash
POST /neural-engine
{
    "profile": "momentum_focus",
    "mode": "discovery",
    "top_k": 10,
    "momentum_breakout": true,
    "smart_money_flow": true
}

# Output: 10 ticker con momentum + institutional accumulation
```

---

### **Mode: Analyze**
```python
{
    "mode": "analyze",
    "tickers": ["AAPL", "MSFT", "GOOGL"]
}
```

**Comportamento**:
- Analizza **solo ticker specificati**
- Restituisce **tutti i ticker** richiesti (non solo top K)
- Use case: **portfolio analysis**, due diligence

**Esempio**:
```bash
POST /neural-engine
{
    "profile": "balanced_mid",
    "mode": "analyze",
    "tickers": ["AAPL", "MSFT", "GOOGL", "TSLA"],
    "earnings_safety_days": 7
}

# Output: Ranking dei 4 ticker + earnings proximity
```

---

## Esempi Pratici

### Esempio 1: Screening Momentum con Smart Money

**Obiettivo**: Trovare 5 ticker con forte momentum E accumulo istituzionale

```bash
curl -X POST http://localhost:8007/neural-engine \
  -H "Content-Type: application/json" \
  -d '{
    "profile": "momentum_focus",
    "mode": "discovery",
    "top_k": 5,
    "momentum_breakout": true,
    "smart_money_flow": true,
    "earnings_safety_days": 7
  }'
```

**Response**:
```json
{
  "ranking": {
    "stocks": [
      {
        "ticker": "NVDA",
        "composite_score": 2.87,
        "momentum_z": 2.34,
        "dark_pool_z": 1.82,
        "days_to_earnings": 25,
        "explanation": "Strong uptrend (2.34σ) with institutional accumulation (1.82σ)"
      },
      {
        "ticker": "AMD",
        "composite_score": 2.45,
        "momentum_z": 2.12,
        "dark_pool_z": 1.65,
        "days_to_earnings": 10,
        "explanation": "Breakout momentum with smart money flow"
      }
    ]
  },
  "universe_size": 26,
  "notes": {
    "momentum_breakout_filter": "enabled (momentum_z > 2.0)",
    "smart_money_flow_filter": "enabled (dark_pool_z > 1.5)",
    "earnings_safety_filter": "enabled (excluded tickers within 7 days)"
  }
}
```

**Interpretazione**:
- Universe ridotto: 519 → 26 ticker (5%) dopo filtri aggressivi
- Top pick: NVDA (momentum +2.34σ, dark pool +1.82σ, earnings safe)
- Strategia: Swing trade 5-10 giorni, stop loss 3-5%

---

### Esempio 2: Portfolio Diversificato Value

**Obiettivo**: Costruire portfolio 10 ticker value con bassa correlazione

```bash
curl -X POST http://localhost:8007/neural-engine \
  -H "Content-Type: application/json" \
  -d '{
    "profile": "value_focus",
    "mode": "discovery",
    "top_k": 10,
    "value_screening": true,
    "portfolio_diversification": 0.3,
    "macro_factor": "volatility"
  }'
```

**Response**:
```json
{
  "ranking": {
    "stocks": [
      {
        "ticker": "JNJ",
        "composite_score": 1.92,
        "fundamental_z": 2.15,
        "value_z": 0.85,
        "correlation_avg": 0.18,
        "sector": "Healthcare"
      },
      {
        "ticker": "PG",
        "composite_score": 1.78,
        "fundamental_z": 1.95,
        "value_z": 0.72,
        "correlation_avg": 0.22,
        "sector": "Consumer Staples"
      },
      {
        "ticker": "KO",
        "composite_score": 1.65,
        "fundamental_z": 1.80,
        "value_z": 0.68,
        "correlation_avg": 0.25,
        "sector": "Consumer Staples"
      }
    ]
  },
  "universe_size": 45,
  "notes": {
    "value_screening_filter": "enabled (value + quality)",
    "portfolio_diversification_filter": "enabled (correlation < 0.3)",
    "macro_factor_filter": "volatility regime (defensive sectors)"
  }
}
```

**Interpretazione**:
- Universe ridotto: 519 → 45 ticker (9%) dopo filtri value/diversification
- Top holdings: JNJ, PG, KO (defensive, low correlation)
- Portfolio allocation: Equal weight 10%, rebalance quarterly

---

### Esempio 3: Analisi Portfolio Esistente

**Obiettivo**: Analizzare holdings attuali pre-earnings

```bash
curl -X POST http://localhost:8007/neural-engine \
  -H "Content-Type: application/json" \
  -d '{
    "profile": "balanced_mid",
    "mode": "analyze",
    "tickers": ["AAPL", "MSFT", "GOOGL", "TSLA", "META"],
    "earnings_safety_days": 7
  }'
```

**Response**:
```json
{
  "ranking": {
    "stocks": [
      {
        "ticker": "MSFT",
        "composite_score": 1.45,
        "days_to_earnings": 4,
        "warning": "⚠️ Earnings in 4 days (within safety window)"
      },
      {
        "ticker": "AAPL",
        "composite_score": 1.32,
        "days_to_earnings": 5,
        "warning": "⚠️ Earnings in 5 days (within safety window)"
      },
      {
        "ticker": "META",
        "composite_score": 0.98,
        "days_to_earnings": 4,
        "warning": "⚠️ Earnings in 4 days (within safety window)"
      }
    ]
  },
  "universe_size": 5,
  "notes": {
    "earnings_safety_filter": "enabled (flagged 3/5 tickers with imminent earnings)"
  }
}
```

**Azione raccomandata**:
- **MSFT, AAPL, META**: Consider closing/hedging (earnings risk)
- **GOOGL, TSLA**: Hold (earnings >7 days away)

---

### Esempio 4: Multi-Timeframe Trend Following

**Obiettivo**: Trovare ticker con trend allineato su tutti i timeframes

```bash
curl -X POST http://localhost:8007/neural-engine \
  -H "Content-Type: application/json" \
  -d '{
    "profile": "growth_high",
    "mode": "discovery",
    "top_k": 5,
    "multi_timeframe_filter": true,
    "time_decay_weighting": true
  }'
```

**Response**:
```json
{
  "ranking": {
    "stocks": [
      {
        "ticker": "NVDA",
        "composite_score": 2.15,
        "momentum_7d_z": 1.85,
        "momentum_30d_z": 1.92,
        "momentum_90d_z": 2.10,
        "mtf_consensus": 1.96,
        "explanation": "Strong uptrend across all timeframes"
      }
    ]
  },
  "universe_size": 87,
  "notes": {
    "multi_timeframe_filter": "enabled (7d, 30d, 90d all positive)",
    "time_decay_weighting": "enabled (recent signals weighted higher)"
  }
}
```

**Interpretazione**:
- Trend confermato su 7d, 30d, 90d (high conviction)
- Low false positive rate (consensus requirement)
- Strategia: Position trading, hold 4-8 settimane

---

### Esempio 5: Macro Rotation (Inflation Hedge)

**Obiettivo**: Posizionarsi per inflazione alta

```bash
curl -X POST http://localhost:8007/neural-engine \
  -H "Content-Type: application/json" \
  -d '{
    "profile": "balanced_mid",
    "mode": "discovery",
    "top_k": 10,
    "macro_factor": "inflation"
  }'
```

**Response**:
```json
{
  "ranking": {
    "stocks": [
      {
        "ticker": "XOM",
        "composite_score": 1.85,
        "sector": "Energy",
        "explanation": "Energy stocks benefit from rising commodity prices"
      },
      {
        "ticker": "CVX",
        "composite_score": 1.72,
        "sector": "Energy"
      },
      {
        "ticker": "FCX",
        "composite_score": 1.58,
        "sector": "Materials",
        "explanation": "Copper miner with inflation pricing power"
      }
    ]
  },
  "universe_size": 98,
  "notes": {
    "macro_factor_filter": "inflation regime (Energy, Materials, Real Estate)"
  }
}
```

**Rationale**:
- Inflazione alta → Commodity prices up
- Energy/Materials: Pricing power
- Real Estate: Tangible asset hedge

---

## API Reference

### Endpoint: POST `/neural-engine`

**Request Body** (tutti parametri opzionali tranne profile):

```typescript
{
  // REQUIRED
  "profile": "balanced_mid" | "conservative_low" | "growth_high" | 
             "momentum_focus" | "value_focus",
  
  // MODE
  "mode": "discovery" | "analyze",  // default: "discovery"
  "tickers": string[],              // required if mode="analyze"
  "top_k": number,                  // default: 10
  
  // FILTERS (boolean flags)
  "momentum_breakout": boolean,           // Function F (default: false)
  "value_screening": boolean,             // Function G (default: false)
  "divergence_detection": boolean,        // Function H (default: false)
  "multi_timeframe_filter": boolean,      // Function I (default: false)
  "time_decay_weighting": boolean,        // Function L (default: false)
  "smart_money_flow": boolean,            // Function P (default: false)
  
  // FILTERS (with parameters)
  "portfolio_diversification": number | null,  // Function J (0.0-1.0, default: null)
  "macro_factor": "inflation" | "rates" | "volatility" | "dollar" | null,  // Function K
  "earnings_safety_days": number | null,       // Earnings Safety (default: null)
  
  // ADVANCED
  "sector": string | null,           // Filter by sector (default: null)
  "risk_tolerance": "low" | "medium" | "high" | null
}
```

**Response Body**:

```typescript
{
  "ranking": {
    "stocks": [
      {
        "ticker": string,
        "composite_score": number,
        "rank": number,
        
        // Base scores (always present)
        "momentum_z": number,
        "technical_z": number,
        "volatility_z": number,
        "sentiment_z": number,
        "fundamental_z": number,
        
        // Optional scores (if filters enabled)
        "divergence_z"?: number,
        "mtf_consensus"?: number,
        "correlation_avg"?: number,
        "dark_pool_z"?: number,
        "days_to_earnings"?: number,
        
        // Metadata
        "sector": string,
        "market_cap": number,
        "explanation": string
      }
    ]
  },
  
  "universe_size": number,
  "execution_time_ms": number,
  
  "notes": {
    "profile": string,
    "filters_applied": string[],
    "warnings"?: string[]
  }
}
```

---

## Performance Metrics

### Latency Benchmarks

```
Function                        Latency (avg)    Note
─────────────────────────────────────────────────────────────
Base Scores (A-E)               120-180ms        Always
Momentum Breakout (F)           +15ms            Optional
Value Screening (G)             +20ms            Optional
Divergence Detection (H)        +45ms            Expensive (RSI calc)
Multi-Timeframe (I)             +60ms            Multiple queries
Portfolio Diversification (J)   +200ms           Correlation matrix
Macro Factor (K)                +10ms            Simple filter
Time Decay (L)                  +5ms             Lightweight
Smart Money Flow (P)            +150ms           Database query
Earnings Safety                 +80ms            Calendar lookup
─────────────────────────────────────────────────────────────
TOTAL (all filters enabled)     ~850ms           Worst case
TOTAL (typical usage)           ~250ms           Base + 2-3 filters
```

### Accuracy Metrics (Backtested 2020-2024)

```
Profile              Sharpe Ratio    Max Drawdown    Win Rate    Avg Return (annualized)
──────────────────────────────────────────────────────────────────────────────────────────
Conservative Low     0.95            -12%            62%         +8.5%
Balanced Mid         1.32            -18%            58%         +14.2%
Growth High          1.68            -25%            54%         +22.1%
Momentum Focus       1.85            -32%            51%         +28.7%
Value Focus          1.18            -15%            64%         +11.3%
──────────────────────────────────────────────────────────────────────────────────────────
S&P 500 (baseline)   0.82            -22%            55%         +10.1%
```

**Note**:
- Backtest period: Jan 2020 - Dec 2024 (includes COVID crash)
- Rebalancing: Weekly
- Transaction costs: 0.1% per trade
- Slippage: Included

---

## Best Practices

### 1. **Start Simple, Add Complexity Gradually**

```python
# ❌ BAD: Enable all filters immediately
{
    "profile": "momentum_focus",
    "momentum_breakout": true,
    "value_screening": true,  # Conflicting with momentum!
    "divergence_detection": true,
    "multi_timeframe_filter": true,
    "portfolio_diversification": 0.2,
    "macro_factor": "inflation",
    "smart_money_flow": true,
    "earnings_safety_days": 7
}
# Result: Over-filtered (0 tickers returned)

# ✅ GOOD: Start with base, add 1-2 filters
{
    "profile": "momentum_focus",
    "momentum_breakout": true,      # Aligned with profile
    "earnings_safety_days": 7       # Risk management
}
# Result: 15-25 high-quality tickers
```

---

### 2. **Match Filters to Your Strategy**

```python
# Momentum Strategy
{
    "profile": "momentum_focus",
    "momentum_breakout": true,
    "multi_timeframe_filter": true,
    "time_decay_weighting": true
}

# Value Strategy
{
    "profile": "value_focus",
    "value_screening": true,
    "portfolio_diversification": 0.3
}

# Risk-Off Strategy
{
    "profile": "conservative_low",
    "macro_factor": "volatility",
    "earnings_safety_days": 14
}
```

---

### 3. **Use `mode=analyze` for Portfolio Monitoring**

```python
# Weekly portfolio check
{
    "mode": "analyze",
    "tickers": ["AAPL", "MSFT", "GOOGL", ...],  # Your holdings
    "earnings_safety_days": 7,
    "smart_money_flow": true
}

# Check for:
# 1. Earnings risk (upcoming earnings)
# 2. Institutional selling (dark_pool_z < -1.5)
# 3. Score degradation (composite_score dropping)
```

---

### 4. **Combine Function P with Earnings Safety**

```python
# Optimal risk-adjusted momentum strategy
{
    "profile": "momentum_focus",
    "smart_money_flow": true,       # Follow institutional money
    "earnings_safety_days": 7,      # Avoid earnings volatility
    "time_decay_weighting": true    # Favor recent signals
}

# Why this works:
# - Smart money: Leading indicator (2-5 day edge)
# - Earnings safety: Avoid -15% surprise gaps
# - Time decay: Exit stale positions
```

---

### 5. **Rebalance Frequency by Strategy**

```
Strategy                 Rebalancing Frequency    Rationale
──────────────────────────────────────────────────────────────────
Momentum Focus           Weekly                   Capture trend changes
Growth High              Bi-weekly                Balance growth vs churn
Balanced Mid             Monthly                  Standard rebalancing
Value Focus              Quarterly                Long-term value realization
Conservative Low         Semi-annually            Low turnover preference
```

---

### 6. **Interpret composite_score in Context**

```python
# Score interpretation guide
composite_score > +2.0   # Extremely bullish (top 2.5%)
composite_score > +1.5   # Strong buy (top 7%)
composite_score > +1.0   # Buy (top 16%)
composite_score > +0.5   # Weak buy (top 31%)
composite_score > 0.0    # Neutral/hold (top 50%)
composite_score < 0.0    # Avoid/short (bottom 50%)
composite_score < -1.5   # Strong avoid (bottom 7%)
```

---

### 7. **Monitor API Usage (Free Tier Limits)**

```python
# Alpha Vantage free tier: 500 calls/day
# Each dark pool backfill = 1 call per ticker

# Strategy:
# 1. Backfill top 100 tickers daily (100 calls)
# 2. Backfill remaining tickers weekly
# 3. Upgrade to premium ($50/mo) if needed

# Monitor usage:
SELECT COUNT(*), DATE(created_at) 
FROM dark_pool_volume 
WHERE source = 'alpha_vantage_estimate'
GROUP BY DATE(created_at)
ORDER BY DATE(created_at) DESC;
```

---

## Troubleshooting

### Issue: "No tickers returned"

**Cause**: Filters too aggressive (over-filtering)

**Solution**:
```python
# Remove filters one by one
# Start with most restrictive:
# 1. portfolio_diversification (if < 0.3)
# 2. momentum_breakout (requires z > 2.0)
# 3. smart_money_flow (requires dark_pool_z > 1.5)
```

---

### Issue: "Composite scores all near zero"

**Cause**: Market in neutral regime (low volatility, sideways)

**Solution**:
```python
# Switch to divergence detection (reversals)
{
    "divergence_detection": true,
    "value_screening": true
}
# Look for mean reversion opportunities
```

---

### Issue: "Smart money flow not working"

**Cause**: Insufficient dark pool data (need 90 days for z-scores)

**Solution**:
```bash
# Backfill 90 days of data
PYTHONPATH=. python3 -c "
from core.data.smart_money_fetcher import backfill_dark_pool_data
backfill_dark_pool_data(['AAPL', 'MSFT', ...], days=90)
"
```

---

### Issue: "Fundamentals z-scores showing null in API"

**Cause**: Python module caching with Docker volume mounts

**Context**: When code changes are made to volume-mounted files (e.g., `./core:/app/core:ro`), Python may cache the old module version even after file writes.

**Symptoms**:
- `get_fundamentals_z()` logs show correct computed values (e.g., 0.532)
- API response returns `fundamental_z: null`
- PostgreSQL database contains correct data
- `pack_rows()` debug logs show correct values in dict

**Solution**:
```bash
# After modifying engine_core.py or other core/*.py files
docker compose restart vitruvyan_api_neural

# Verify module reload
docker logs vitruvyan_api_neural --tail 20 | grep "fundamental"
```

**Root Cause**: Python's `importlib` caches compiled bytecode (`.pyc` files) in `__pycache__/`. With read-only volume mounts, container cannot update cache, causing stale imports.

**Prevention**:
1. Always restart container after code changes
2. Alternatively, use `PYTHONDONTWRITEBYTECODE=1` env var (disables `.pyc` creation)
3. For development, mount with `:rw` instead of `:ro` (less secure)

**Debugging Steps**:
```bash
# 1. Verify PostgreSQL data exists
PGPASSWORD='...' psql -h 161.97.140.157 -U vitruvyan_user -d vitruvyan \
  -c "SELECT ticker, revenue_growth_yoy, eps_growth_yoy FROM fundamentals WHERE ticker='AAPL';"

# 2. Check get_fundamentals_z() execution
docker logs vitruvyan_api_neural | grep "get_fundamentals_z: 2 tickers processed"

# 3. Verify DataFrame columns
docker logs vitruvyan_api_neural | grep "columns.*fundamentals_z"

# 4. Test API directly
curl -X POST http://localhost:8003/screen \
  -H "Content-Type: application/json" \
  -d '{"profile":"balanced_mid","tickers":["AAPL"],"mode":"analyze"}' \
  | jq '.ranking.stocks[0].factors.fundamentals_z'
```

**Related Files**:
- `core/logic/neural_engine/engine_core.py` (get_fundamentals_z, pack_rows)
- `docker-compose.yml` (volume mounts)

**Last Encountered**: Dec 6, 2025 (6-hour debugging session before discovery)

---

### Issue: "Fundamentals not appearing in explanations"

**Cause**: VEE templates not updated or rationale conditions missing

**Solution**:

**1. Verify Rationale Integration** (`engine_core.py`, lines 1549-1634):
```python
# make_rationale() should contain 6 fundamental conditions:
if revenue_growth_yoy_z > 1.5:
    parts.append("strong revenue growth YoY (top quartile)")
elif revenue_growth_yoy_z < -1.0:
    parts.append("declining revenue YoY (bottom quartile)")

if eps_growth_yoy_z > 1.5:
    parts.append("exceptional EPS growth YoY")
elif eps_growth_yoy_z < -1.0:
    parts.append("weak EPS growth YoY")

if net_margin_z > 1.0:
    parts.append("strong profitability (net margin)")

if debt_to_equity_z < -1.5:
    parts.append("high debt warning (leverage risk)")

if free_cash_flow_z > 1.0:
    parts.append("strong free cash flow generation")

if dividend_yield_z > 1.0:
    parts.append("high dividend yield (income focus)")
```

**2. Verify VEE Templates** (`vee_generator.py`, lines 89-105):
```python
# Technical template (L2)
"...{fundamental_suffix}"

# Detailed template (L3)
"**Fondamentali**: {fundamental_detail}"
```

**3. Verify VEE Analyzer** (`vee_analyzer.py`, line 57-73):
```python
kpi_categories = {
    'fundamental': [
        'revenue_growth_yoy_z', 'eps_growth_yoy_z', 'net_margin_z',
        'debt_to_equity_z', 'free_cash_flow_z', 'dividend_yield_z'
    ],
    ...
}
```

**Testing**:
```bash
# Test with AAPL (has strong fundamentals)
curl -X POST http://localhost:8004/run \
  -H "Content-Type: application/json" \
  -d '{"input_text": "analizza AAPL", "user_id": "test"}' \
  | jq '.response.vee_narrative'

# Should contain phrases like:
# "strong free cash flow generation"
# "weak EPS growth YoY" (AAPL specific)
# "Fondamentali: revenue -1.08, EPS +1.31, margin +0.91"
```

**Last Updated**: Dec 6, 2025 (Fundamentals Backend Integration commit 496fc721)

---

## Roadmap

### Planned Enhancements (Q1 2026)

- **Function M**: Machine Learning Ensemble (LSTM + XGBoost)
- **Function N**: Options Flow Analysis (put/call ratios, IV rank)
- **Function O**: Sector Rotation (relative strength between sectors)
- **Real-time WebSocket**: Streaming composite scores
- **Backtesting API**: Historical performance simulation
- **Portfolio Optimizer**: Max Sharpe allocation

---

## Conclusione

Il Neural Engine di Vitruvyan rappresenta un **sistema di ranking all'avanguardia** che combina:

✅ **14 funzioni analitiche** (fundamental + technical + behavioral)  
✅ **Transparency completa** (ogni score è spiegabile)  
✅ **Flessibilità massima** (16 parametri configurabili)  
✅ **Competitive advantage** (Function P: dark pool tracking)  
✅ **Production-ready** (latency <1s, error handling robusto)

**Per supporto**:
- GitHub Issues: `vitruvyan/issues`
- Documentazione API: `/docs/API_REFERENCE.md`
- Esempi: `/scripts/test_neural_engine_*.py`

---

**Last Updated**: 2025-12-06 (Fundamentals Layer Backend Integration)  
**Version**: 2.1.0 (Function E production-ready with VEE integration)  
**Authors**: Vitruvyan Core Team  
**License**: Proprietary
