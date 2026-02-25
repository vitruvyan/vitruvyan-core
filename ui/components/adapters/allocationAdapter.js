// adapters/allocationAdapter.js
// UX Constitution compliant - Jan 3, 2026
// Allocation Analysis → Full Evidence Stack with Pattern Weavers

export const allocationAdapter = {
  map(finalState) {
    const canResponse = finalState.can_response || {}
    const allocation = finalState.allocation_data || {}
    const veeAll = finalState.vee_explanations || {}
    const numerical = finalState.numerical_panel || []
    const tickers = finalState.tickers || []
    const advisor = finalState.advisor_recommendation || {}
    const weaver = finalState.weaver_context || {}  // 🕸️ Pattern Weavers

    // Build narrative (VEE Summary - NEVER include advisor rationale here)
    const narrativeText = canResponse.narrative || ""
    if (!narrativeText && tickers.length > 0 && veeAll[tickers[0]]) {
      narrativeText = veeAll[tickers[0]].summary || ""
    }

    // ═══════════════════════════════════════════════════════════════
    // 🕸️ PATTERN WEAVERS: Build enriched allocation criteria
    // ═══════════════════════════════════════════════════════════════
    const enrichedCriteria = {
      mode: allocation.mode || 'optimized',
      // From weaver_context (semantic extraction)
      concepts: weaver.concepts || [],
      sectors: weaver.sectors || [],
      regions: weaver.regions || [],
      countries: weaver.countries || [],
      riskProfile: weaver.risk_profile || {},
      // From allocation_data
      amount: allocation.amount || null,
      currency: allocation.currency || 'USD',
      // Derived from weaver
      primarySector: weaver.sectors?.[0] || null,
      primaryConcept: weaver.concepts?.[0] || null,
      primaryRegion: weaver.regions?.[0] || null
    }

    // Build human-readable allocation description
    const allocationDescription = buildAllocationDescription(enrichedCriteria, tickers)

    // Prepare pie chart data (ALWAYS VISIBLE, outside accordions)
    const pieChartData = tickers.map(ticker => {
      const weight = (allocation.weights?.[ticker] || 0) * 100 // Convert to percentage
      const tickerData = numerical.find(n => n.ticker === ticker) || {}
      return {
        name: ticker,
        value: Math.round(weight * 100) / 100, // Round to 2 decimals
        composite: tickerData.composite_score || 0,
        momentum: tickerData.momentum_z || 0,
        trend: tickerData.trend_z || 0,
        volatility: tickerData.vola_z || 0,
        sentiment: tickerData.sentiment_z || 0,
        // 🕸️ Pattern Weavers: Add sector/concept context
        sector: enrichedCriteria.primarySector,
        concept: enrichedCriteria.primaryConcept
      }
    })

    // Calculate allocation orientation (enhanced with Pattern Weavers)
    const allocationOrientation = calculateAllocationOrientation(allocation.weights || {}, enrichedCriteria)

    // Build weights table data with insights (enhanced with Pattern Weavers)
    const weightsTableData = tickers.map(ticker => {
      const weight = (allocation.weights?.[ticker] || 0) * 100
      const tickerData = numerical.find(n => n.ticker === ticker) || {}
      const insight = getTickerInsight(tickerData, numerical, enrichedCriteria)
      return {
        ticker,
        weight: Math.round(weight * 100) / 100,
        insight,
        // 🕸️ Pattern Weavers: Add semantic context
        sectorFit: enrichedCriteria.primarySector ? `Fits ${enrichedCriteria.primarySector} sector` : null,
        conceptFit: enrichedCriteria.primaryConcept ? `Matches ${enrichedCriteria.primaryConcept} theme` : null
      }
    })

    // Build rationale text
    let rationaleText = allocation.rationale || ""
    if (tickers.length > 0 && veeAll[tickers[0]]?.detailed) {
      rationaleText += (rationaleText ? "\n\n" : "") + veeAll[tickers[0]].detailed
    }

    return {
      // ═══════════════════════════════════════════════════════
      // LAYER 1: NARRATIVE (VEE Summary)
      // ═══════════════════════════════════════════════════════
      narrative: {
        text: narrativeText,
        tone: 'neutral',
        recommendation: null
      },

      // ═══════════════════════════════════════════════════════
      // LAYER 2: PIE CHART (ALWAYS VISIBLE, outside accordions)
      // ═══════════════════════════════════════════════════════
      pieChart: {
        data: pieChartData,
      tooltipFormatter: (entry) => `${entry.name}: ${entry.value}% | Composite: ${entry.composite?.toFixed(2) || 'N/A'}${entry.sector ? ` | ${entry.sector} sector` : ''}`
    },

    // ═══════════════════════════════════════════════════════
    // LAYER 2.5: ALLOCATION DESCRIPTION (visible under pie chart)
    // ═══════════════════════════════════════════════════════
    allocationDescription: allocationDescription,

      // ═══════════════════════════════════════════════════════
      // LAYER 4: CONTEXT
      // ═══════════════════════════════════════════════════════
      context: {
        tickers: tickers,
        horizon: finalState.horizon || null,
        intent: finalState.intent || null,
        conversation_type: 'allocation'
      },

      // ═══════════════════════════════════════════════════════
      // LAYER 5: RATIONALE (for "Why?" accordion)
      // ═══════════════════════════════════════════════════════
      rationale: {
        method: allocation.mode || 'optimized',
        text: rationaleText,
      veeDetailed: tickers.length > 0 ? veeAll[tickers[0]]?.detailed || null : null,
      // 🕸️ Pattern Weavers: Add semantic context
      semanticContext: {
        sectors: enrichedCriteria.sectors,
        concepts: enrichedCriteria.concepts,
        regions: enrichedCriteria.regions,
        riskProfile: enrichedCriteria.riskProfile
      },
      sections: [
          {
            id: 'weights-table',
            title: 'Allocation Weights',
            priority: 1,
            defaultExpanded: false,
            content: {
              type: 'allocation-table',
              data: weightsTableData
            }
          }
        ].filter(s => s.content.data && s.content.data.length > 0)
      },

      // ═══════════════════════════════════════════════════════
      // LAYER 7: ADVISOR INSIGHT
      // ═══════════════════════════════════════════════════════
      advisorInsight: {
        signal_label: allocationOrientation.orientation,
        rationale: generateAllocationRationale(allocationOrientation, tickers, allocation.weights, enrichedCriteria),
        orientation: allocationOrientation.badge,
        interpretation: `Portfolio distributed across ${tickers.length} holdings with ${allocationOrientation.orientation.toLowerCase()} strategy${enrichedCriteria.primarySector ? ` focused on ${enrichedCriteria.primarySector}` : ''}.`,
        source: "allocation_analysis",
        // 🕸️ Pattern Weavers: Add semantic insights
        semanticInsights: {
          sectorAlignment: enrichedCriteria.primarySector ? `${tickers.length} holdings aligned with ${enrichedCriteria.primarySector} sector preferences` : null,
          conceptMatch: enrichedCriteria.primaryConcept ? `Portfolio matches ${enrichedCriteria.primaryConcept} investment theme` : null,
          regionalFocus: enrichedCriteria.primaryRegion ? `Geographic focus on ${enrichedCriteria.primaryRegion}` : null
        }
      }
    }
  }
}

// Helper: Calculate allocation orientation based on concentration (enhanced with Pattern Weavers)
function calculateAllocationOrientation(weights, criteria) {
  const weightValues = Object.values(weights)
  if (weightValues.length === 0) {
    return { orientation: "Balanced Allocation", badge: "balanced" }
  }

  const maxWeight = Math.max(...weightValues)

  // Adjust orientation based on Pattern Weavers risk profile
  const riskTolerance = criteria.riskProfile?.tolerance
  let concentrationThreshold = 0.40 // default

  if (riskTolerance === 'low') {
    concentrationThreshold = 0.30 // more conservative
  } else if (riskTolerance === 'high') {
    concentrationThreshold = 0.50 // more aggressive
  }

  if (maxWeight > concentrationThreshold + 0.20) {
    return { orientation: "Concentrated Allocation", badge: "concentrated" }
  } else if (maxWeight >= concentrationThreshold) {
    return { orientation: "Balanced Allocation", badge: "balanced" }
  } else {
    return { orientation: "Diversified Allocation", badge: "diversified" }
  }
}

// Helper: Generate mini-insight for weights table (enhanced with Pattern Weavers)
function getTickerInsight(tickerData, allTickersData, criteria) {
  const { momentum_z, vola_z, composite_score } = tickerData

  // Pattern Weavers: Sector fit takes priority
  if (criteria.primarySector) {
    // This would require sector classification data
    // For now, use existing logic
  }

  // Find ticker with highest momentum
  const maxMomentum = Math.max(...allTickersData.map(t => t.momentum_z || 0))
  if (momentum_z === maxMomentum && momentum_z > 0.5) {
    return "Highest momentum"
  }

  // Find ticker with lowest volatility
  const minVola = Math.min(...allTickersData.map(t => t.vola_z || 0))
  if (vola_z === minVola && vola_z < 0) {
    return "Most stable"
  }

  // Default based on composite score
  if (composite_score > 1.0) return "Strong performer"
  if (composite_score > 0.5) return "Solid contributor"
  if (composite_score > 0) return "Moderate exposure"
  return "Speculative position"
}

// Helper: Generate allocation-specific rationale (enhanced with Pattern Weavers)
function generateAllocationRationale(orientation, tickers, weights, criteria) {
  const tickerCount = tickers.length
  const maxWeight = Math.max(...Object.values(weights))
  const topTicker = Object.keys(weights).find(t => weights[t] === maxWeight)

  let baseRationale = ''

  switch (orientation.badge) {
    case 'concentrated':
      baseRationale = `This allocation concentrates ${Math.round(maxWeight * 100)}% of capital in ${topTicker}, offering potential for amplified returns from the top performer while accepting higher portfolio risk. The concentrated approach may suit investors with higher risk tolerance seeking maximum upside potential.`
      break

    case 'balanced':
      baseRationale = `This allocation maintains a balanced distribution with ${topTicker} receiving ${Math.round(maxWeight * 100)}% of capital. The balanced approach provides moderate risk-adjusted returns by avoiding over-concentration while maintaining meaningful exposure to top performers.`
      break

    case 'diversified':
      baseRationale = `This allocation emphasizes broad diversification across ${tickerCount} holdings, with the largest position (${topTicker}) at only ${Math.round(maxWeight * 100)}%. This conservative approach prioritizes risk management and capital preservation over concentrated upside potential.`
      break

    default:
      baseRationale = `This allocation distributes capital across ${tickerCount} holdings with a balanced approach, providing moderate risk exposure and diversified market participation.`
  }

  // 🕸️ Pattern Weavers: Add semantic context
  let semanticContext = ''

  if (criteria.primarySector) {
    semanticContext += ` The portfolio is strategically aligned with the ${criteria.primarySector} sector, focusing on companies that demonstrate strong fundamentals and growth potential in this area.`
  }

  if (criteria.primaryConcept) {
    semanticContext += ` This allocation embodies the ${criteria.primaryConcept} investment theme, selecting companies that exemplify these characteristics.`
  }

  if (criteria.regions && criteria.regions.length > 0) {
    semanticContext += ` Geographic exposure is concentrated in ${criteria.regions.join(', ')}, providing regional diversification and market-specific opportunities.`
  }

  if (criteria.riskProfile) {
    const riskContext = {
      'conservative': 'prioritizing stability and income generation',
      'balanced': 'balancing growth potential with risk management',
      'growth': 'emphasizing capital appreciation and innovation',
      'aggressive': 'seeking maximum upside potential'
    }[criteria.riskProfile] || 'maintaining prudent risk management'

    semanticContext += ` The strategy ${riskContext} while optimizing for long-term performance.`
  }

  return baseRationale + semanticContext
}

// ═══════════════════════════════════════════════════════════════════════
// PATTERN WEAVERS ENHANCED HELPER FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════

// Helper: Build human-readable allocation description with Pattern Weavers
function buildAllocationDescription(criteria, tickers) {
  const parts = []

  // Amount and currency
  if (criteria.amount) {
    parts.push(`$${criteria.amount.toLocaleString()} ${criteria.currency}`)
  }

  // Primary sector from Pattern Weavers
  if (criteria.primarySector) {
    parts.push(`allocated to ${criteria.primarySector} sector`)
  } else if (criteria.sectors.length > 0) {
    parts.push(`allocated across ${criteria.sectors.slice(0, 2).join(", ")} sectors`)
  }

  // Concepts from Pattern Weavers
  if (criteria.primaryConcept) {
    parts.push(`focused on ${criteria.primaryConcept}`)
  } else if (criteria.concepts.length > 0) {
    parts.push(`with ${criteria.concepts.slice(0, 2).join(", ")} themes`)
  }

  // Region from Pattern Weavers
  if (criteria.primaryRegion) {
    parts.push(`in ${criteria.primaryRegion}`)
  }

  // Mode
  const modeLabels = {
    "optimized": "optimized",
    "equal_weight": "equally weighted",
    "risk_parity": "risk-parity balanced"
  }
  const modeLabel = modeLabels[criteria.mode] || criteria.mode
  parts.push(`using ${modeLabel} strategy`)

  return parts.length > 0
    ? `Allocation of ${parts.join(" ")} across ${tickers.length} holdings.`
    : `Portfolio allocation across ${tickers.length} holdings using ${criteria.mode || 'optimized'} strategy.`
}