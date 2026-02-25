// adapters/screeningAdapter.js
// UX Constitution compliant - Jan 3, 2026
// Screening Analysis → Candidate Discovery with Pattern Weavers

export const screeningAdapter = {
  map(finalState) {
    const canResponse = finalState.can_response || {}
    const screening = finalState.screening_data || {}
    const screeningCriteria = finalState.screening_criteria || {}
    const veeAll = finalState.vee_explanations || {}
    const numerical = finalState.numerical_panel || []
    const tickers = finalState.tickers || []
    const advisor = finalState.advisor_recommendation || {}
    const weaver = finalState.weaver_context || {}

    // Build narrative (VEE Summary)
    let narrativeText = canResponse.narrative || ""
    if (!narrativeText && tickers.length > 0 && veeAll[tickers[0]]) {
      narrativeText = veeAll[tickers[0]].summary || ""
    }

    // ═══════════════════════════════════════════════════════════════
    // 🕸️ PATTERN WEAVERS: Build enriched criteria from weaver_context
    // ═══════════════════════════════════════════════════════════════
    const enrichedCriteria = {
      profile: screeningCriteria.profile || "balanced",
      mode: screeningCriteria.mode || "discovery",
      // From weaver_context (semantic extraction)
      concepts: weaver.concepts || [],
      sectors: weaver.sectors || [],
      regions: weaver.regions || [],
      countries: weaver.countries || [],
      riskProfile: weaver.risk_profile || {},
      // From backend screening_criteria
      sector: screeningCriteria.sector || weaver.sectors?.[0] || null,
      riskTolerance: screeningCriteria.risk_tolerance || weaver.risk_profile?.tolerance || null,
      // Filters applied
      filters: screeningCriteria.filters || {},
      // Stats
      universeScanned: screeningCriteria.universe_scanned || 519,
      topKRequested: screeningCriteria.top_k_requested || 5
    }

    // Build human-readable criteria description
    const criteriaDescription = buildCriteriaDescription(enrichedCriteria)

    // ═══════════════════════════════════════════════════════════════
    // 🏆 CANDIDATE LIST: Build from numerical_panel with new fields
    // ═══════════════════════════════════════════════════════════════
    const candidates = numerical.map((item, idx) => ({
      rank: item.rank || idx + 1,
      ticker: item.ticker,
      companyName: item.company_name || item.ticker,
      composite: item.composite_score || 0,
      // 🆕 MODIFICA 2: dominant_factor
      dominantFactor: item.dominant_factor || determineDominantFactor(item),
      // 🆕 MODIFICA 3: selection_reason
      selectionReason: item.selection_reason || `Rank #${idx + 1} in ${enrichedCriteria.profile} profile`,
      // Factor data for tooltips
      factors: {
        momentum: item.momentum_z || item.factors?.momentum_z || 0,
        trend: item.trend_z || item.factors?.trend_z || 0,
        volatility: item.vola_z || item.factors?.vola_z || 0,
        sentiment: item.sentiment_z || item.factors?.sentiment_z || 0
      }
    }))

    // Determine screening orientation for Advisor Insight
    const screeningOrientation = determineScreeningOrientation(candidates, enrichedCriteria)

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
      // LAYER 2: CANDIDATE LIST (ALWAYS VISIBLE, outside accordions)
      // ═══════════════════════════════════════════════════════════════
      candidates: candidates,
      candidateCount: candidates.length,

      // ═══════════════════════════════════════════════════════════════
      // LAYER 3: CRITERIA DESCRIPTION (visible under candidates)
      // ═══════════════════════════════════════════════════════════════
      screeningCriteria: enrichedCriteria,
      criteriaDescription: criteriaDescription,

      // ═══════════════════════════════════════════════════════════════
      // LAYER 4: FOLLOW-UPS
      // ═══════════════════════════════════════════════════════════════
      followUps: canResponse.follow_ups || generateDefaultFollowUps(candidates, enrichedCriteria),

      // ═══════════════════════════════════════════════════════════════
      // LAYER 5: CONTEXT
      // ═══════════════════════════════════════════════════════════════
      context: {
        tickers: tickers,
        horizon: finalState.horizon || null,
        intent: finalState.intent || null,
        conversation_type: 'screening'
      },

      // ═══════════════════════════════════════════════════════════════
      // LAYER 6: RATIONALE (for "Why These?" accordion)
      // ═══════════════════════════════════════════════════════════════
      rationale: {
        method: enrichedCriteria.profile,
        filtersApplied: Object.entries(enrichedCriteria.filters || {})
          .filter(([k, v]) => v === true)
          .map(([k]) => k.replace(/_/g, ' ')),
        universeStats: `Scanned ${enrichedCriteria.universeScanned} tickers → ${candidates.length} candidates`,
        veeDetailed: tickers.length > 0 ? veeAll[tickers[0]]?.detailed || null : null
      },

      // ═══════════════════════════════════════════════════════════════
      // LAYER 7: EVIDENCE (for "Supporting Data" accordion)
      // ═══════════════════════════════════════════════════════════════
      evidence: {
        sections: [
          {
            id: 'ranking-table',
            title: 'Full Ranking',
            priority: 1,
            defaultExpanded: false,
            content: {
              type: 'screening-table',
              data: candidates
            }
          },
          {
            id: 'factor-heatmap',
            title: 'Factor Comparison',
            priority: 2,
            defaultExpanded: false,
            content: {
              type: 'heatmap',
              data: numerical
            }
          }
        ].filter(s => s.content.data && s.content.data.length > 0)
      },

      // ═══════════════════════════════════════════════════════════════
      // LAYER 8: ADVISOR INSIGHT
      // ═══════════════════════════════════════════════════════════════
      advisorInsight: {
        signal_label: screeningOrientation.label,
        rationale: advisor.rationale || advisor.advisory || screeningOrientation.rationale,
        orientation: screeningOrientation.badge
      }
    }
  }
}

// ═══════════════════════════════════════════════════════════════════════
// HELPER FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════

/**
 * Build human-readable criteria description from enriched criteria
 * Integrates Pattern Weavers concepts/sectors/regions
 */
function buildCriteriaDescription(criteria) {
  const parts = []

  // Profile (if not balanced)
  if (criteria.profile && criteria.profile !== "balanced" && criteria.profile !== "short_spec") {
    const profileLabels = {
      "momentum_focus": "Momentum",
      "low_risk": "Low Risk",
      "trend_follow": "Trend Following",
      "sentiment_boost": "Sentiment-Driven",
      "value_screening": "Value"
    }
    parts.push(profileLabels[criteria.profile] || criteria.profile)
  }

  // Concepts from Pattern Weavers
  if (criteria.concepts.length > 0) {
    parts.push(criteria.concepts.slice(0, 2).join(", "))
  }

  // Sector
  if (criteria.sector) {
    parts.push(criteria.sector)
  } else if (criteria.sectors.length > 0) {
    parts.push(criteria.sectors[0])
  }

  // Region from Pattern Weavers
  if (criteria.regions.length > 0) {
    parts.push(`in ${criteria.regions[0]}`)
  }

  // Risk tolerance
  if (criteria.riskTolerance) {
    const riskLabels = { "low": "conservative", "medium": "balanced risk", "high": "aggressive" }
    parts.push(riskLabels[criteria.riskTolerance] || criteria.riskTolerance)
  }

  // Active filters
  const activeFilters = Object.entries(criteria.filters || {})
    .filter(([k, v]) => v === true)
    .map(([k]) => {
      const filterLabels = {
        "momentum_breakout": "breakout",
        "value_screening": "undervalued",
        "divergence_detection": "divergence",
        "multi_timeframe_filter": "MTF aligned"
      }
      return filterLabels[k] || k
    })

  if (activeFilters.length > 0) {
    parts.push(activeFilters.join(", "))
  }

  return parts.length > 0
    ? `Top ${criteria.topKRequested} stocks: ${parts.join(" • ")}`
    : `Top ${criteria.topKRequested} stocks from full universe`
}

/**
 * Fallback: Determine dominant factor from numerical data
 * Used when backend doesn't provide dominant_factor
 */
function determineDominantFactor(item) {
  const factors = {
    momentum: Math.abs(item.momentum_z || item.factors?.momentum_z || 0),
    trend: Math.abs(item.trend_z || item.factors?.trend_z || 0),
    volatility: Math.abs(item.vola_z || item.factors?.vola_z || 0),
    sentiment: Math.abs(item.sentiment_z || item.factors?.sentiment_z || 0)
  }

  const maxFactor = Object.entries(factors).reduce((max, [name, val]) =>
    val > max.val ? { name, val } : max, { name: "balanced", val: 0 }
  )

  return maxFactor.val > 0.5 ? maxFactor.name : "balanced"
}

/**
 * Determine screening orientation for Advisor Insight
 */
function determineScreeningOrientation(candidates, criteria) {
  if (candidates.length === 0) {
    return { label: "No Results", badge: "neutral", rationale: "No candidates matched the criteria." }
  }

  // Check dominant factors across top candidates
  const factorCounts = {}
  candidates.slice(0, 3).forEach(c => {
    const factor = c.dominantFactor || "balanced"
    factorCounts[factor] = (factorCounts[factor] || 0) + 1
  })

  const dominantTheme = Object.entries(factorCounts)
    .sort((a, b) => b[1] - a[1])[0]?.[0] || "balanced"

  // Map to orientation
  const orientations = {
    "momentum": {
      label: "Momentum Focus",
      badge: "momentum",
      rationale: "This selection emphasizes stocks with strong price acceleration and buying pressure."
    },
    "trend": {
      label: "Trend Following",
      badge: "trend",
      rationale: "These picks show consistent directional movement across multiple timeframes."
    },
    "volatility": {
      label: "Low Risk Picks",
      badge: "low-risk",
      rationale: "Selection prioritizes stability and lower price fluctuation."
    },
    "sentiment": {
      label: "Sentiment Driven",
      badge: "sentiment",
      rationale: "These stocks benefit from positive market sentiment and analyst consensus."
    },
    "balanced": {
      label: "Balanced Selection",
      badge: "balanced",
      rationale: "A diversified selection balancing multiple factors for broad exposure."
    }
  }

  return orientations[dominantTheme] || orientations.balanced
}

/**
 * Generate default follow-up suggestions
 */
function generateDefaultFollowUps(candidates, criteria) {
  const followUps = []

  if (candidates.length > 0) {
    followUps.push(`Analyze ${candidates[0].ticker} in detail`)
  }

  if (candidates.length >= 2) {
    followUps.push(`Compare ${candidates[0].ticker} vs ${candidates[1].ticker}`)
  }

  if (criteria.sector) {
    followUps.push(`Show more ${criteria.sector} stocks`)
  } else {
    followUps.push("Filter by sector")
  }

  if (criteria.profile !== "low_risk") {
    followUps.push("Show low risk alternatives")
  }

  return followUps.slice(0, 4)
}