// adapters/singleTickerAdapter.js
// UX Constitution compliant - Jan 2, 2026
// Single Ticker Analysis → Full Evidence Stack

export const singleTickerAdapter = {
  map(finalState) {
    const canResponse = finalState.can_response || {}
    const veeAll = finalState.vee_explanations || {}
    const numerical = finalState.numerical_panel?.[0] || {}
    const ticker = finalState.tickers?.[0] || ''
    const advisor = finalState.advisor_recommendation || {}
    const vee = veeAll[ticker] || {}

    // Build narrative (VEE Summary - NEVER include advisor rationale here)
    // Advisor Insight is separate cognitive layer (after accordions)
    const narrativeText = canResponse.narrative || vee.summary || ""

    return {
      // ═══════════════════════════════════════════════════════
      // LAYER 1: NARRATIVE (VEE Summary)
      // ═══════════════════════════════════════════════════════
      narrative: {
        text: narrativeText,
        tone: advisor.confidence > 0.7 ? 'confident' : 'neutral',
        recommendation: null  // Recommendation is in advisor_recommendation, not here
      },
      
      // ═══════════════════════════════════════════════════════
      // LAYER 2: FOLLOW-UPS
      // ═══════════════════════════════════════════════════════
      followUps: canResponse.follow_ups || [],
      
      // ═══════════════════════════════════════════════════════
      // LAYER 3: VEE EXPLANATIONS (for "Why?" accordion)
      // ═══════════════════════════════════════════════════════
      vee_explanations: {
        technical: vee.technical || null,
        detailed: vee.detailed || null,
        contextualized: vee.contextualized || null
      },
      
      // ═══════════════════════════════════════════════════════
      // LAYER 4: EVIDENCE (for "Supporting Data" accordion)
      // Order per Costituzione Art. XII: Solidità → Redditività → Crescita → Risk → Momentum → Sentiment
      // ═══════════════════════════════════════════════════════
      evidence: {
        sections: [
          // a) Signal Drivers (always first)
          {
            id: 'signal-drivers',
            title: 'Signal Drivers',
            priority: 1,
            defaultExpanded: true,
            content: {
              type: 'signal-drivers',
              data: {
                momentum_z: numerical.momentum_z,
                trend_z: numerical.trend_z,
                volatility_z: numerical.vola_z,  // Backend uses vola_z, not volatility_z
                sentiment_z: numerical.sentiment_z
              }
            }
          },
          // b) Price Chart
          {
            id: 'price-chart',
            title: 'Price History',
            priority: 2,
            defaultExpanded: true,
            content: {
              type: 'chart',
              data: {
                ticker: ticker,
                // Chart component will fetch data
              }
            }
          },
          // c) Fundamentals (collapsed, with micro-badge)
          {
            id: 'fundamentals',
            title: 'Fundamentals',
            priority: 3,
            defaultExpanded: false,
            microBadge: _getFundamentalsBadge(numerical),
            content: {
              type: 'fundamentals',
              data: _buildFundamentalsData(numerical)
            }
          },
          // d) Risk Assessment (VARE)
          {
            id: 'risk',
            title: 'Risk Assessment',
            priority: 4,
            defaultExpanded: false,
            microBadge: _getRiskBadge(numerical),
            content: {
              type: 'risk',
              data: _buildRiskData(numerical)
            }
          },
          // e) Explore Additional Perspectives
          {
            id: 'perspectives',
            title: 'Explore Additional Perspectives',
            priority: 5,
            defaultExpanded: false,
            content: {
              type: 'perspectives',
              data: {
                perspectives: [
                  { id: 'radar', label: 'Factor Breakdown', componentType: 'FactorRadarChart' },
                  { id: 'risk', label: 'Risk Profile', componentType: 'RiskBreakdownChart' }
                ],
                numerical: numerical,  // Pass numerical data for charts
                ticker: ticker
              }
            }
          }
        ].filter(s => _hasData(s.content.data))
      },
      
      // ═══════════════════════════════════════════════════════
      // LAYER 5: ADVISOR RECOMMENDATION
      // Passed directly to AdvisorInsight component
      // ═══════════════════════════════════════════════════════
      advisor_recommendation: advisor,
      
      // Context metadata
      context: {
        tickers: [ticker],
        horizon: finalState.horizon || null,
        intent: finalState.intent || null,
        conversation_type: 'single'
      }
    }
  }
}

// Helper: Check if section has meaningful data
function _hasData(data) {
  if (!data) return false
  // For fundamentals/risk, check if we have metrics array or dimensions
  if (data.metrics?.length > 0) return true
  if (data.dimensions?.length > 0) return true
  if (data.links?.length > 0) return true  // perspectives
  // For other types, check raw values
  return Object.values(data).some(v => v !== null && v !== undefined)
}

// Helper: Generate fundamentals micro-badge
function _getFundamentalsBadge(numerical) {
  const fz = numerical.fundamentals_z
  if (fz === null || fz === undefined) return null
  if (fz > 0.5) return { label: 'Solid', color: 'green' }
  if (fz < -0.5) return { label: 'Tension', color: 'red' }
  return { label: 'Neutral', color: 'gray' }
}

// Helper: Generate risk micro-badge
function _getRiskBadge(numerical) {
  const risk = numerical.vare_risk_category
  if (!risk) return null
  const lower = risk.toLowerCase()
  if (lower.includes('low')) return { label: 'Low Risk', color: 'green' }
  if (lower.includes('high') || lower.includes('critical')) return { label: 'High Risk', color: 'red' }
  return { label: 'Moderate', color: 'amber' }
}

// Helper: Build fundamentals data in renderer-expected format
// Per Decision Sheet #1: Cluster order = Solidity → Profitability → Growth
function _buildFundamentalsData(numerical) {
  const metrics = []
  
  // Cluster 1: SOLIDITY
  if (numerical.debt_to_equity_z !== null && numerical.debt_to_equity_z !== undefined) {
    metrics.push({ key: 'debt_to_equity', label: 'Debt/Equity', value: numerical.debt_to_equity_z, cluster: 'solidity' })
  }
  if (numerical.free_cash_flow_z !== null && numerical.free_cash_flow_z !== undefined) {
    metrics.push({ key: 'free_cash_flow', label: 'Free Cash Flow', value: numerical.free_cash_flow_z, cluster: 'solidity' })
  }
  
  // Cluster 2: PROFITABILITY
  if (numerical.net_margin_z !== null && numerical.net_margin_z !== undefined) {
    metrics.push({ key: 'net_margin', label: 'Net Margin', value: numerical.net_margin_z, cluster: 'profitability' })
  }
  
  // Cluster 3: GROWTH
  if (numerical.revenue_growth_yoy_z !== null && numerical.revenue_growth_yoy_z !== undefined) {
    metrics.push({ key: 'revenue_growth', label: 'Revenue Growth', value: numerical.revenue_growth_yoy_z, cluster: 'growth' })
  }
  if (numerical.eps_growth_yoy_z !== null && numerical.eps_growth_yoy_z !== undefined) {
    metrics.push({ key: 'eps_growth', label: 'EPS Growth', value: numerical.eps_growth_yoy_z, cluster: 'growth' })
  }
  
  // Determine overall status
  const fz = numerical.fundamentals_z
  let status = 'neutral'
  let statusLabel = 'Mixed signals, no strong evidence'
  if (fz > 0.5) { status = 'solid'; statusLabel = 'Solid fundamentals base' }
  else if (fz < -0.5) { status = 'tension'; statusLabel = 'Fundamentals under tension' }
  
  return { metrics, status, statusLabel }
}

// Helper: Build risk data in renderer-expected format
function _buildRiskData(numerical) {
  // RiskRenderer expects dimensions as object, not array
  const dimensions = {}
  
  if (numerical.market_risk !== null && numerical.market_risk !== undefined) {
    dimensions.market = numerical.market_risk
  }
  if (numerical.volatility_risk !== null && numerical.volatility_risk !== undefined) {
    dimensions.volatility = numerical.volatility_risk
  }
  if (numerical.liquidity_risk !== null && numerical.liquidity_risk !== undefined) {
    dimensions.liquidity = numerical.liquidity_risk
  }
  if (numerical.correlation_risk !== null && numerical.correlation_risk !== undefined) {
    dimensions.correlation = numerical.correlation_risk
  }
  
  return {
    score: numerical.vare_risk_score,
    category: numerical.vare_risk_category || 'Unknown',
    dimensions
  }
}