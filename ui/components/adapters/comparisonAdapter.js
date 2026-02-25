// adapters/comparisonAdapter.js
// UX Constitution compliant - Jan 3, 2026
// Comparison Analysis → Winner vs Loser with Pattern Weavers

export const comparisonAdapter = {
  map(finalState) {
    const canResponse = finalState.can_response || {}
    const comparison = finalState.comparison_state || {}
    const veeAll = finalState.vee_explanations || {}
    const numerical = finalState.numerical_panel || []
    const tickers = finalState.tickers || []
    const advisor = finalState.advisor_recommendation || {}
    const weaver = finalState.weaver_context || {}

    // Build narrative (VEE Summary) with ticker mention
    let narrativeText = canResponse.narrative || ""
    if (!narrativeText && tickers.length > 0 && veeAll[tickers[0]]) {
      narrativeText = veeAll[tickers[0]].summary || ""
    }
    
    // ✅ FIX (Jan 3): Prepend comparison context to narrative
    if (narrativeText && tickers.length >= 2) {
      const tickerContext = `Comparing ${tickers[0]} vs ${tickers[1]}: `
      narrativeText = tickerContext + narrativeText
    }

    // ═══════════════════════════════════════════════════════════════
    // 🕸️ PATTERN WEAVERS: Extract semantic context
    // ═══════════════════════════════════════════════════════════════
    const semanticContext = {
      concepts: weaver.concepts || [],
      sectors: weaver.sectors || [],
      regions: weaver.regions || [],
      countries: weaver.countries || [],
      riskProfile: weaver.risk_profile || {}
    }

    // ═══════════════════════════════════════════════════════════════
    // 🏆 WINNER vs LOSER: Identify from numerical_panel
    // ═══════════════════════════════════════════════════════════════
    const sortedByComposite = [...numerical].sort((a, b) =>
      (b.composite_score || 0) - (a.composite_score || 0)
    )
    
    const winner = sortedByComposite[0] || {}
    const loser = sortedByComposite[sortedByComposite.length - 1] || {}

    // Build comparison summary
    const comparisonSummary = {
      winner: {
        ticker: winner.ticker,
        companyName: winner.company_name || winner.ticker,
        composite: winner.composite_score || 0
      },
      loser: {
        ticker: loser.ticker,
        companyName: loser.company_name || loser.ticker,
        composite: loser.composite_score || 0
      },
      deltaComposite: (winner.composite_score || 0) - (loser.composite_score || 0),
      verdict: determineComparisonVerdict(winner, loser, semanticContext)
    }

    // ═══════════════════════════════════════════════════════════════
    // 🧮 FACTOR COMPARISON TABLE: Build delta matrix
    // ═══════════════════════════════════════════════════════════════
    const factorComparison = buildFactorComparison(winner, loser)

    // ═══════════════════════════════════════════════════════════════
    // 📊 TICKERS DATA: Full dataset for charts
    // ═══════════════════════════════════════════════════════════════
    const tickersData = numerical.map(item => ({
      ticker: item.ticker,
      companyName: item.company_name || item.ticker,
      composite: item.composite_score || 0,
      factors: {
        momentum: item.momentum_z || 0,
        trend: item.trend_z || 0,
        volatility: item.vola_z || 0,
        sentiment: item.sentiment_z || 0
      }
    }))

    return {
      // ═══════════════════════════════════════════════════════════════
      // LAYER 1: NARRATIVE (VEE Summary)
      // ═══════════════════════════════════════════════════════════════
      narrative: {
        text: narrativeText,
        tone: 'neutral',
        recommendation: null
      },

      // ═══════════════════════════════════════════════════════════════
      // LAYER 2: WINNER vs LOSER SUMMARY (ALWAYS VISIBLE)
      // ═══════════════════════════════════════════════════════════════
      comparisonSummary: comparisonSummary,

      // ═══════════════════════════════════════════════════════════════
      // LAYER 3: FACTOR COMPARISON TABLE (ALWAYS VISIBLE)
      // ═══════════════════════════════════════════════════════════════
      factorComparison: factorComparison,

      // ═══════════════════════════════════════════════════════════════
      // LAYER 4: FOLLOW-UPS
      // ═══════════════════════════════════════════════════════════════
      followUps: canResponse.follow_ups || generateComparisonFollowUps(winner, loser),

      // ═══════════════════════════════════════════════════════════════
      // LAYER 5: CONTEXT
      // ═══════════════════════════════════════════════════════════════
      context: {
        tickers: tickers,
        horizon: finalState.horizon || null,
        intent: finalState.intent || null,
        conversation_type: 'comparison',
        semanticContext: semanticContext
      },

      // ═══════════════════════════════════════════════════════════════
      // LAYER 6: RATIONALE (for "Why This Verdict?" accordion)
      // ═══════════════════════════════════════════════════════════════
      rationale: {
        method: "head-to-head comparison",
        keyDifferentiator: factorComparison.keyDifferentiator || "composite score",
        winnerStrengths: factorComparison.winnerStrengths || [],
        loserWeaknesses: factorComparison.loserWeaknesses || [],
        veeDetailed: veeAll[winner.ticker]?.detailed || null
      },

      // ═══════════════════════════════════════════════════════════════
      // LAYER 7: EVIDENCE (for "Supporting Data" accordion)
      // ═══════════════════════════════════════════════════════════════
      evidence: {
        sections: [
          {
            id: 'comparison-table',
            title: 'Factor-by-Factor Comparison',
            priority: 1,
            defaultExpanded: false,
            content: {
              type: 'comparison-table',
              data: {
                factorComparison: factorComparison,
                winnerTicker: winner.ticker,
                loserTicker: loser.ticker
              }
            }
          },
          {
            id: 'winner-strengths',
            title: `${winner.ticker} Competitive Advantages`,
            priority: 2,
            defaultExpanded: false,
            content: {
              type: 'winner-strengths',
              data: {
                ticker: winner.ticker,
                strengths: factorComparison.winnerStrengths,
                keyDifferentiator: factorComparison.keyDifferentiator,
                keyDelta: factorComparison.keyDelta
              }
            }
          },
          {
            id: 'comparison-radar',
            title: 'Multi-Factor Radar',
            priority: 3,
            defaultExpanded: false,
            content: {
              type: 'comparison-radar',
              data: tickersData
            }
          }
        ]
      },

      // ═══════════════════════════════════════════════════════════════
      // LAYER 8: ADVISOR INSIGHT
      // ═══════════════════════════════════════════════════════════════
      advisorInsight: {
        signal_label: comparisonSummary.verdict.label,
        rationale: advisor.rationale || advisor.advisory || comparisonSummary.verdict.rationale,
        orientation: comparisonSummary.verdict.orientation
      }
    }
  }
}

// ═══════════════════════════════════════════════════════════════════════
// HELPER FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════

/**
 * Determine comparison verdict based on factor analysis
 */
function determineComparisonVerdict(winner, loser, semanticContext) {
  const deltaComposite = (winner.composite_score || 0) - (loser.composite_score || 0)

  // Determine orientation based on delta magnitude
  let orientation, label, rationale

  if (deltaComposite > 0.5) {
    orientation = "clear-winner"
    label = `${winner.ticker} Leads`
    rationale = `${winner.ticker} shows significantly stronger overall performance with a ${deltaComposite.toFixed(2)} point advantage.`
  } else if (deltaComposite > 0.2) {
    orientation = "moderate-lead"
    label = `${winner.ticker} Edges Ahead`
    rationale = `${winner.ticker} has a modest advantage, but ${loser.ticker} remains competitive.`
  } else {
    orientation = "tight-race"
    label = "Close Match"
    rationale = `Both tickers show similar performance with minimal differentiation.`
  }

  // Enrich with semantic context from Pattern Weavers
  if (semanticContext.concepts.length > 0) {
    rationale += ` Context: ${semanticContext.concepts.join(", ")}.`
  }

  return { orientation, label, rationale }
}

/**
 * Build factor-by-factor comparison matrix with deltas
 */
function buildFactorComparison(winner, loser) {
  const factors = [
    { key: 'momentum', label: 'Momentum' },
    { key: 'trend', label: 'Trend' },
    { key: 'volatility', label: 'Volatility' },
    { key: 'sentiment', label: 'Sentiment' }
  ]

  const factorData = factors.map(f => {
    const winnerValue = winner[`${f.key}_z`] || 0
    const loserValue = loser[`${f.key}_z`] || 0
    const delta = winnerValue - loserValue

    return {
      factor: f.label,
      winner: winnerValue,
      loser: loserValue,
      delta: delta,
      leader: delta > 0.1 ? winner.ticker : delta < -0.1 ? loser.ticker : "tie"
    }
  })

  // Identify key differentiator (largest delta)
  const maxDeltaFactor = factorData.reduce((max, f) =>
    Math.abs(f.delta) > Math.abs(max.delta) ? f : max, factorData[0]
  )

  // Winner strengths (positive deltas)
  const winnerStrengths = factorData
    .filter(f => f.delta > 0.3)
    .map(f => f.factor)

  // Loser weaknesses (negative deltas)
  const loserWeaknesses = factorData
    .filter(f => f.delta < -0.3)
    .map(f => f.factor)

  return {
    factors: factorData,
    keyDifferentiator: maxDeltaFactor.factor,
    keyDelta: maxDeltaFactor.delta,
    winnerStrengths: winnerStrengths,
    loserWeaknesses: loserWeaknesses
  }
}

/**
 * Generate comparison-specific follow-up suggestions
 */
function generateComparisonFollowUps(winner, loser) {
  return [
    `Analyze ${winner.ticker} in detail`,
    `Analyze ${loser.ticker} in detail`,
    `What are the risk factors for these companies?`,
    `Find similar alternatives to ${winner.ticker}`
  ]
}
