// adapters/portfolioAdapter.js
export const portfolioAdapter = {
  map(finalState) {
    const canResponse = finalState.can_response || {}
    const portfolio = finalState.portfolio_data || {}
    const vee = finalState.vee_explanations || {}
    const numerical = finalState.numerical_panel || []
    const tickers = finalState.tickers || []

    // Build narrative from CAN or VEE summary
    let narrativeText = canResponse.narrative || ""
    if (!narrativeText && tickers.length > 0 && vee[tickers[0]]) {
      narrativeText = vee[tickers[0]].summary || ""
    }

    // Prepare sector breakdown for pie chart
    const sectorData = Object.entries(portfolio.sector_breakdown || {}).map(([sector, value]) => ({
      name: sector,
      value: value
    }))

    return {
      narrative: {
        text: narrativeText,
        tone: 'neutral',
        recommendation: null
      },
      followUps: canResponse.follow_ups || [],
      context: {
        tickers: tickers,
        horizon: finalState.horizon || null,
        intent: finalState.intent || null,
        missingSlots: null
      },
      evidence: {
        sections: [
          {
            id: 'holdings',
            title: 'Portfolio Holdings',
            priority: 1,
            defaultExpanded: true,
            content: {
              type: 'holdings',
              data: {
                holdings: portfolio.holdings || [],
                total_value: portfolio.total_value || 0
              }
            }
          },
          {
            id: 'risk',
            title: 'Risk Metrics',
            priority: 2,
            defaultExpanded: false,
            content: {
              type: 'metrics',
              data: {
                concentration_risk: portfolio.concentration_risk || 'unknown',
                diversification_score: portfolio.diversification_score || 0
              }
            }
          },
          {
            id: 'sectors',
            title: 'Sector Breakdown',
            priority: 3,
            defaultExpanded: false,
            content: {
              type: 'pie',
              data: sectorData
            }
          }
        ].filter(s => s.content.data && (Array.isArray(s.content.data) ? s.content.data.length > 0 : true))
      }
    }
  }
}