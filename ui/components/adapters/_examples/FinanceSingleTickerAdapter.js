// ui/components/adapters/_examples/FinanceSingleTickerAdapter.js
// Finance Domain Adapter Example — Single Ticker Analysis
// Last updated: Feb 20, 2026

/**
 * Finance Single Ticker Adapter
 * 
 * Domain-specific adapter for finance vertical, demonstrating:
 * - Evidence ordering (Solidità → Redditività → Crescita → Risk)
 * - Finance-specific metrics (z-scores, fundamentals, risk)
 * - VEE content integration
 * 
 * This is an EXAMPLE adapter copied from Mercator UI.
 * Actual implementation should live in vitruvyan_core/domains/finance/ui/
 */

import { BaseAdapter } from '../../../contracts'

export class FinanceSingleTickerAdapter extends BaseAdapter {
  name = 'finance_single_ticker'

  constructor() {
    super({
      domain: 'finance',
      description: 'Single ticker financial analysis',
      conversationTypes: ['single_ticker', 'ticker_analysis'],
      version: '1.0.0',
      author: 'vitruvyan-finance'
    })
  }

  /**
   * Map backend state to UI payload
   */
  map(state) {
    const canResponse = state.can_response || {}
    const veeAll = state.vee_explanations || {}
    const numerical = state.numerical_panel?.[0] || {}
    const ticker = state.tickers?.[0] || ''
    const advisor = state.advisor_recommendation || {}
    const vee = veeAll[ticker] || {}

    // Narrative (VEE Summary)
    const narrativeText = canResponse.narrative || vee.summary || ""

    // Follow-ups
    const followUpQueries = (canResponse.follow_ups || []).map(query => ({
      label: query,
      query: query
    }))

    // Evidence sections (EPISTEMOLOGICAL ORDER - Finance Domain)
    const evidenceSections = []

    // 1. Signal Drivers (always first)
    evidenceSections.push(
      this.buildEvidenceSection(
        'signal-drivers',
        'Signal Drivers',
        'signal-drivers',
        {
          momentum_z: numerical.momentum_z,
          trend_z: numerical.trend_z,
          volatility_z: numerical.vola_z,
          sentiment_z: numerical.sentiment_z
        },
        {
          priority: 1,
          defaultExpanded: true,
          subtitle: 'Key technical indicators'
        }
      )
    )

    // 2. Price Chart
    evidenceSections.push(
      this.buildEvidenceSection(
        'price-chart',
        'Price History',
        'chart',
        { ticker },
        {
          priority: 2,
          defaultExpanded: true
        }
      )
    )

    // 3. Fundamentals (Solidità → Redditività → Crescita)
    if (this.hasFundamentals(numerical)) {
      const fundamentals_z = numerical.fundamentals_z || 0
      const badge = this.getFundamentalsBadge(fundamentals_z)

      evidenceSections.push(
        this.buildEvidenceSection(
          'fundamentals',
          'Fondamentali',
          'metrics',
          {
            // SOLIDITÀ
            debt_to_equity_z: numerical.debt_to_equity_z,
            free_cash_flow_z: numerical.free_cash_flow_z,
            // REDDITIVITÀ
            roic_z: numerical.roic_z,
            operating_margin_z: numerical.operating_margin_z,
            net_margin_z: numerical.net_margin_z,
            // CRESCITA
            revenue_growth_yoy_z: numerical.revenue_growth_yoy_z,
            eps_growth_yoy_z: numerical.eps_growth_yoy_z
          },
          {
            priority: 3,
            defaultExpanded: false,
            subtitle: this.getFundamentalsSubtitle(fundamentals_z),
            badge
          }
        )
      )
    }

    // 4. Risk
    if (this.hasRisk(numerical)) {
      evidenceSections.push(
        this.buildEvidenceSection(
          'risk',
          'Risk Analysis',
          'metrics',
          {
            market_risk_z: numerical.market_risk_z,
            volatility_risk_z: numerical.volatility_risk_z,
            liquidity_risk_z: numerical.liquidity_risk_z,
            correlation_risk_z: numerical.correlation_risk_z
          },
          {
            priority: 4,
            defaultExpanded: false
          }
        )
      )
    }

    // VEE explanations
    const veePayload = this.buildVEE(
      vee.technical,
      vee.detailed,
      vee.contextualized
    )

    // Context
    const contextPayload = this.buildContext(
      'single_ticker',
      [ticker],
      {
        intent: state.intent,
        advisor_confidence: advisor.confidence
      }
    )

    return {
      narrative: this.buildNarrative(
        narrativeText,
        advisor.confidence > 0.7 ? 'confident' : 'neutral',
        state.intent
      ),
      followUps: this.buildFollowUps(followUpQueries),
      evidence: { sections: evidenceSections },
      vee_explanations: veePayload,
      context: contextPayload,
      // Domain extensions
      advisor_recommendation: advisor
    }
  }

  /**
   * Helpers (Finance-specific)
   */
  hasFundamentals(numerical) {
    const fundamentalKeys = [
      'debt_to_equity_z', 'free_cash_flow_z', 'roic_z',
      'operating_margin_z', 'net_margin_z', 'revenue_growth_yoy_z', 'eps_growth_yoy_z'
    ]
    const availableCount = fundamentalKeys.filter(key => numerical[key] != null).length
    return availableCount >= 3 // Min 3 metriche per renderizzare (Costituzione Art. XI)
  }

  hasRisk(numerical) {
    const riskKeys = ['market_risk_z', 'volatility_risk_z', 'liquidity_risk_z', 'correlation_risk_z']
    return riskKeys.some(key => numerical[key] != null)
  }

  getFundamentalsBadge(fundamentals_z) {
    if (fundamentals_z > 0.5) {
      return { label: 'Solidi', color: 'green' }
    } else if (fundamentals_z < -0.5) {
      return { label: 'In tensione', color: 'orange' }
    } else {
      return { label: 'Neutrali', color: 'gray' }
    }
  }

  getFundamentalsSubtitle(fundamentals_z) {
    if (fundamentals_z > 0.5) {
      return 'Base razionale solida'
    } else if (fundamentals_z < -0.5) {
      return 'Attenzione: fondamentali in tensione'
    } else {
      return 'Segnali misti, nessuna evidenza forte'
    }
  }
}

/**
 * Usage (in domain plugin):
 * 
 * ```javascript
 * import { FinanceSingleTickerAdapter } from './FinanceSingleTickerAdapter'
 * import { domainPluginRegistry } from '@/ui/contracts'
 * 
 * const financePlugin = {
 *   metadata: {
 *     id: 'finance-ui-plugin',
 *     name: 'Finance UI Plugin',
 *     domain: 'finance',
 *     version: '1.0.0'
 *   },
 *   adapters: [
 *     new FinanceSingleTickerAdapter()
 *   ],
 *   vee_content: { ... }
 * }
 * 
 * domainPluginRegistry.register(financePlugin)
 * ```
 */
