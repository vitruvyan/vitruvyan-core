// adapters/portfolioGuardianAdapter.js
// Portfolio Guardian cognitive events adapter
// Created: Jan 18, 2026 - Task 18 Mercator Orchestration

export const portfolioGuardianAdapter = {
  map(finalState) {
    const guardianEvent = finalState.conclave_event || {}
    const payload = guardianEvent.payload || {}
    const canResponse = finalState.can_response || {}
    const responseText = finalState.response || canResponse.narrative || ""
    
    // Determine risk level and color
    const riskLevel = payload.risk_level || 'unknown'
    const riskScore = payload.risk_score || 0
    
    const riskColorMap = {
      'high': 'red',
      'critical': 'red',
      'medium': 'yellow',
      'warning': 'yellow',
      'low': 'green',
      'minimal': 'green',
      'unknown': 'gray'
    }
    
    const riskColor = riskColorMap[riskLevel.toLowerCase()] || 'gray'
    
    // Build narrative with urgency tone
    const tone = (riskLevel === 'high' || riskLevel === 'critical') ? 'urgent' : 'informative'
    
    // Generate contextual follow-ups based on event type
    const followUps = canResponse.follow_ups || _generateGuardianFollowUps(guardianEvent.event_type, riskLevel)
    
    // Build risk metrics section
    const riskMetrics = payload.risk_metrics || {}
    const metricsData = Object.entries(riskMetrics).map(([key, value]) => {
      const percentage = typeof value === 'number' ? Math.round(value * 100) : value
      const status = _determineMetricStatus(key, value)
      
      return {
        label: _formatMetricLabel(key),
        value: typeof percentage === 'number' ? `${percentage}%` : String(percentage),
        status: status,
        rawValue: value
      }
    })
    
    // Build affected tickers section
    const affectedTickers = payload.affected_tickers || []
    const portfolioValue = payload.portfolio_value || 0
    const tickersData = affectedTickers.map(ticker => ({
      ticker: ticker,
      // Will be enhanced by UI with ticker data if available
    }))
    
    // Build evidence sections (accordions)
    const evidenceSections = []
    
    // Section 1: Risk Metrics (if available)
    if (metricsData.length > 0) {
      evidenceSections.push({
        id: 'risk_metrics',
        title: '⚠️ Risk Metrics',
        priority: 1,
        defaultExpanded: true,
        content: {
          type: 'metrics',
          data: metricsData
        }
      })
    }
    
    // Section 2: Affected Positions (if available)
    if (affectedTickers.length > 0) {
      evidenceSections.push({
        id: 'affected_positions',
        title: '🎯 Affected Positions',
        priority: 2,
        defaultExpanded: true,
        content: {
          type: 'tickers',
          data: tickersData
        }
      })
    }
    
    // Section 3: Event Details
    if (guardianEvent.event_type) {
      evidenceSections.push({
        id: 'event_details',
        title: '📋 Event Details',
        priority: 3,
        defaultExpanded: false,
        content: {
          type: 'event_info',
          data: {
            eventType: guardianEvent.event_type,
            correlationId: guardianEvent.correlation_id || 'N/A',
            timestamp: guardianEvent.timestamp || new Date().toISOString(),
            triggerMetric: payload.trigger_metric || 'unknown',
            portfolioValue: portfolioValue ? `$${portfolioValue.toLocaleString()}` : 'N/A'
          }
        }
      })
    }
    
    return {
      narrative: {
        text: responseText,
        tone: tone,
        recommendation: null,
        badges: [
          {
            label: riskLevel.toUpperCase(),
            color: riskColor,
            score: riskScore
          }
        ]
      },
      followUps: followUps,
      context: {
        tickers: affectedTickers,
        horizon: null,
        intent: 'portfolio_guardian',
        eventType: guardianEvent.event_type,
        riskLevel: riskLevel,
        conversation_type: 'portfolio_guardian'
      },
      evidence: {
        sections: evidenceSections
      }
    }
  }
}

// Helper: Generate contextual follow-ups based on Guardian event
function _generateGuardianFollowUps(eventType, riskLevel) {
  const baseFollowUps = [
    "Show me portfolio details",
    "What should I do now?",
    "Analyze risk factors"
  ]
  
  if (eventType?.includes('emergency')) {
    return [
      "🚨 Show emergency protocols",
      "Suggest protective actions",
      "Check market conditions"
    ]
  }
  
  if (eventType?.includes('risk.assessed')) {
    if (riskLevel === 'high' || riskLevel === 'critical') {
      return [
        "Suggest hedging strategies",
        "Show diversification options",
        "Analyze correlation risks"
      ]
    }
    return [
      "Continue monitoring",
      "Show portfolio allocation",
      "Review risk thresholds"
    ]
  }
  
  if (eventType?.includes('alert.issued')) {
    return [
      "Acknowledge alert",
      "Show alert history",
      "Update risk preferences"
    ]
  }
  
  if (eventType?.includes('recovery.completed')) {
    return [
      "Show recovery details",
      "Resume normal monitoring",
      "Review incident report"
    ]
  }
  
  return baseFollowUps
}

// Helper: Determine metric status (critical/warning/normal)
function _determineMetricStatus(metricKey, value) {
  const numValue = typeof value === 'number' ? value : parseFloat(value) || 0
  
  // Concentration risk thresholds
  if (metricKey.includes('concentration')) {
    if (numValue > 0.6) return 'critical'  // >60% in single position
    if (numValue > 0.4) return 'warning'   // >40%
    return 'normal'
  }
  
  // Volatility thresholds
  if (metricKey.includes('volatility')) {
    if (numValue > 0.5) return 'critical'  // >50% volatility
    if (numValue > 0.3) return 'warning'   // >30%
    return 'normal'
  }
  
  // Correlation thresholds
  if (metricKey.includes('correlation')) {
    if (numValue > 0.8) return 'warning'   // >80% correlation (low diversification)
    return 'normal'
  }
  
  // Drawdown thresholds
  if (metricKey.includes('drawdown')) {
    if (numValue > 0.2) return 'critical'  // >20% drawdown
    if (numValue > 0.1) return 'warning'   // >10%
    return 'normal'
  }
  
  // Default: warning if >50%
  if (numValue > 0.5) return 'warning'
  return 'normal'
}

// Helper: Format metric labels for display
function _formatMetricLabel(key) {
  const labelMap = {
    'concentration': 'Concentration Risk',
    'concentration_risk': 'Concentration Risk',
    'volatility': 'Volatility',
    'correlation': 'Correlation',
    'drawdown': 'Max Drawdown',
    'beta': 'Market Beta',
    'sharpe': 'Sharpe Ratio',
    'var': 'Value at Risk',
    'liquidity': 'Liquidity Risk'
  }
  
  return labelMap[key.toLowerCase()] || key.split('_').map(word => 
    word.charAt(0).toUpperCase() + word.slice(1)
  ).join(' ')
}
