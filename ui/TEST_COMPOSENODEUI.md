# 🧪 ComposeNodeUI Unification - Test Plan
**Date:** November 30, 2025  
**Task:** #12 - Test ComposeNodeUI Unification  
**Frontend:** http://localhost:3005  
**Status:** ✅ Ready for Testing

---

## 🎯 Objective
Verify that ComposeNodeUI is now the unified entry point for VEE display across all analysis types (single ticker, multi-ticker, portfolio).

---

## 📋 Test Cases

### Test 1: Single Ticker Analysis ✅
**Query:** `analyze AAPL`

**Expected ComposeNodeUI Rendering:**
- ✅ Header: "VEE Analysis" (no ticker badge for single)
- ✅ Numerical Panel summary in header (Score + sentiment badge)
- ✅ Executive Summary box with gradient blue background + Brain icon
- ✅ Narrative text with markdown rendering
- ✅ VEE Multi-Level accordion for AAPL expandable
- ✅ Advanced Details (explainability.detailed) collapsible section
- ❌ **NO inline blue box** for conversational (removed in FASE 2.1)
- ✅ VEEMultiLevelAccordion still present below (backward compat)
- ✅ VEEMultiLevelAccordion shows **deprecation warning banner**

**Charts (should still render):**
- FactorRadarChart
- RiskBreakdownChart
- CandlestickChart

---

### Test 2: Multi-Ticker Comparison 🔵
**Query:** `compare AAPL vs MSFT`

**Expected ComposeNodeUI Rendering:**
- ✅ Header badge: "2 Tickers"
- ✅ Comparison Mode info box (blue background)
  - _"💡 Comparison Mode: Click on each ticker to see detailed VEE..."_
- ✅ VEE accordion for AAPL
- ✅ VEE accordion for MSFT
- ✅ ComparisonNodeUI still present (ranking, factor winners, deltas)
- ✅ General comparison narrative

**Backend Requirements:**
- Intent: `comparison`
- comparison_state populated
- vee_explanations with 2 entries (AAPL, MSFT)

---

### Test 3: Portfolio Analysis 🟣
**Query:** `analizza il mio portfolio`

**Expected ComposeNodeUI Rendering:**
- ✅ Header badge: "Portfolio"
- ✅ Portfolio Insights box (purple background)
  - Total Value
  - Diversification Score
- ✅ Portfolio narrative
- ✅ PortfolioNodeUI still present (metrics, holdings, sectors)
- ✅ VEE accordion for each ticker in portfolio (if available)

**⚠️ Prerequisites:**
- Task #1 must be completed (user_id mismatch fix)
- PostgreSQL portfolio data for `test_conversational_step2`

**Alternative:** Use `!test_portfolio` mock command

---

### Test 4: Mock Portfolio Command 🧪
**Query:** `!test_portfolio`

**Expected:**
- ✅ PortfolioNodeUI with mock data
- ✅ Total Value: **$63,500**
- ✅ 6 holdings: AAPL, GOOGL, META, MSFT, NVDA, TSLA
- ✅ Concentration Risk: 23.62% (AAPL)
- ✅ Diversification Score: 75%
- ✅ Sector Breakdown: Technology 100%

---

### Test 5: Mock Comparison Command 🧪
**Query:** `!test_comparison`

**Expected:**
- ✅ ComparisonNodeUI with mock data
- ✅ 3 tickers: AAPL, MSFT, GOOGL
- ✅ Overall Ranking table
- ✅ Factor Winners (Momentum, Trend, Sentiment, Risk)
- ✅ Radar Chart comparison

---

## ✅ Success Criteria

### Functional
- [ ] ComposeNodeUI renders for all test cases
- [ ] Inline conversational box **NOT present** (removed)
- [ ] VEEMultiLevelAccordion shows deprecation warning
- [ ] Context badges correct (Portfolio, N Tickers)
- [ ] Numerical panel summary visible in header
- [ ] Portfolio Insights section visible when portfolio
- [ ] Comparison info box visible when multi-ticker
- [ ] VEE accordions expandable and functional
- [ ] All existing NodeUI components still render (Comparison, Portfolio)

### Visual
- [ ] Executive Summary has gradient blue background
- [ ] Portfolio Insights has purple background
- [ ] Comparison Mode info has blue background
- [ ] Badges have correct colors (purple=Portfolio, blue=Multi-ticker)
- [ ] Icons render correctly (Brain, TrendingUp, AlertCircle)
- [ ] Typography consistent (font sizes, weights)

### Technical
- [ ] No console errors
- [ ] No React warnings
- [ ] Charts still render (Radar, Risk, Candlestick)
- [ ] Network requests successful (200 OK)
- [ ] Loading states work correctly

---

## 📝 Test Execution Steps

1. **Open Frontend:**
   \`\`\`
   http://localhost:3005
   \`\`\`

2. **Open Browser DevTools:**
   - Console tab (check for errors)
   - Network tab (monitor API calls)

3. **Execute Test Queries (in order):**
   \`\`\`
   1. analyze AAPL
   2. compare AAPL vs MSFT
   3. !test_portfolio
   4. !test_comparison
   5. analizza il mio portfolio (if Task #1 done)
   \`\`\`

4. **For Each Test:**
   - Wait for complete response
   - Verify ComposeNodeUI rendering
   - Check VEEMultiLevelAccordion deprecation warning
   - Inspect console for errors
   - Expand VEE accordions to test interactivity
   - Take screenshots if issues found

5. **Document Results:**
   - [ ] All tests pass → Mark Task #12 as completed
   - [ ] Issues found → Create bug report with screenshots
   - [ ] Performance issues → Note response times

---

## 🐛 Known Issues / Blockers

1. **Portfolio Real Data (Task #1):**
   - user_id mismatch blocks real portfolio testing
   - Use `!test_portfolio` as workaround
   - PostgreSQL not running in Docker

2. **Backend Requirements:**
   - compose_node.py must populate `vee_explanations`
   - Backend must return `narrative` field
   - `explainability.detailed` required for Advanced Details

---

## 📊 Test Results Template

\`\`\`
Date: ___________
Tester: ___________

Test 1 (Single Ticker): [ PASS / FAIL ]
- ComposeNodeUI rendered: [ YES / NO ]
- Deprecation warning shown: [ YES / NO ]
- Issues: _________________

Test 2 (Multi-Ticker): [ PASS / FAIL ]
- Comparison badge: [ YES / NO ]
- Info box visible: [ YES / NO ]
- Issues: _________________

Test 3 (Portfolio - Mock): [ PASS / FAIL ]
- Portfolio badge: [ YES / NO ]
- Mock data correct: [ YES / NO ]
- Issues: _________________

Test 4 (Comparison - Mock): [ PASS / FAIL ]
- ComparisonNodeUI + ComposeNodeUI both present: [ YES / NO ]
- Issues: _________________

Console Errors: [ NONE / SEE BELOW ]
_________________

Performance: [ GOOD / ACCEPTABLE / SLOW ]
_________________

Overall Result: [ ✅ PASS / ❌ FAIL ]
\`\`\`

---

## 🚀 Next Steps After Testing

**If All Tests Pass:**
- ✅ Mark Task #12 as completed
- ✅ Update UI_ARCHITECTURE_ASSESSMENT.md (status → tested)
- ✅ Move to Task #10 (Tab-based UI) or Task #13 (Extract chart logic)
- ✅ Create production deployment checklist

**If Tests Fail:**
- 🐛 Document bugs with screenshots
- 🐛 Create GitHub issues
- 🐛 Fix issues before proceeding
- 🐛 Re-run tests after fixes

---

**Document Version:** 1.0  
**Created:** November 30, 2025  
**Last Updated:** November 30, 2025  
**Related:** FASE 2 - ComposeNodeUI Unification
