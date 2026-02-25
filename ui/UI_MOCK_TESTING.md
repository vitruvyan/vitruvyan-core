# 🧪 UI Testing Guide - Portfolio & Comparison Nodes

## 🚀 Real Data Integration (LLM-powered)

### **Portfolio Analysis**
Digita query naturali in **qualsiasi lingua**:

\`\`\`
analyze my portfolio
come sta andando il mio portafoglio?
check my holdings
portfolio review
\`\`\`

**Come funziona:**
1. GPT-4o-mini rileva intent `portfolio_review`
2. Frontend chiama `/api/portfolio` → fetch tickers
3. Backend LangGraph fa analisi completa
4. UI mostra `PortfolioNodeUI` con dati reali

### **Comparison Analysis**
\`\`\`
compare AAPL vs MSFT
SHOP vs PLTR
confronta NVDA e AMD
\`\`\`

**Come funziona:**
1. GPT-4o-mini rileva intent `comparison`
2. Frontend valida tickers
3. Backend fa comparison analysis
4. UI mostra `ComparisonNodeUI`

---

## 🧪 Mock Testing (Development Only)

Comandi speciali per testare UI senza backend:

### 🔵 Portfolio Node UI (Mock)

\`\`\`
!test_portfolio
\`\`\`
Portfolio default (AAPL, MSFT, TSLA) - diversificazione moderata

\`\`\`
!test_portfolio_concentrated
\`\`\`
Portfolio concentrato (NVDA 93.75%) - **CRITICAL RISK**

\`\`\`
!test_portfolio_diversified
\`\`\`
Portfolio diversificato (SHOP, PLTR, COIN) - bassa concentrazione

### 🟣 Comparison Node UI (Mock)

\`\`\`
!test_comparison
\`\`\`
Comparison AAPL vs MSFT vs GOOGL con:
- Ranking order
- Factor winners (momentum, trend, volatility, sentiment)
- Factor deltas
- Score dispersion

---

## 📡 API Endpoints

### `/api/intent` - LLM Intent Detection
\`\`\`javascript
POST /api/intent
Body: { "query": "analyze my portfolio" }
Response: { 
  "intent": "portfolio_review",
  "confidence": 0.95,
  "tickers": []
}
\`\`\`

### `/api/portfolio` - Portfolio Tickers
\`\`\`javascript
GET /api/portfolio?user_id=default_user
Response: { 
  "tickers": ["AAPL", "MSFT", "TSLA"],
  "source": "json",
  "count": 3
}
\`\`\`

---

## ✅ Checklist

### PortfolioNodeUI
- ✅ Total portfolio value display
- ✅ Portfolio score badge
- ✅ Concentration risk (critical/high/medium/low con colori)
- ✅ Diversification score con progress bar
- ✅ Sector breakdown percentuali
- ✅ Holdings list con values
- ✅ Top 3 holdings

### ComparisonNodeUI
- ✅ Overall ranking con badge "Winner"
- ✅ Factor winners per ogni fattore
- ✅ Factor deltas con colori
- ✅ Score dispersion assessment
- ✅ FactorRadarChart integration

---

## 🔧 Configuration

**Environment Variables (`.env.local`):**
\`\`\`bash
OPENAI_API_KEY=sk-proj-xxx...
NEXT_PUBLIC_API_URL=http://localhost:8004
\`\`\`

**Mock Data Location:**
- JSON: `core/data/portfolio_mock.json`
- PostgreSQL: `user_mock_portfolio` table

---

## 🌐 Dev Server

**URL:** http://localhost:3003

---

## 🎯 Next Steps

1. ✅ Test portfolio query: "analyze my portfolio"
2. ✅ Test comparison: "compare AAPL vs MSFT"
3. ✅ Test multilingue: "come va il mio portafoglio?"
4. ✅ Verify LLM intent detection logs
5. ✅ Check portfolio data source (JSON vs PostgreSQL)
6. 🔄 Add Redis caching for LLM intents
7. 🔄 Add Portfolio button in header/sidebar
