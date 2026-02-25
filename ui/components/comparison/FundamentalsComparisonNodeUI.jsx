/**
 * FundamentalsComparisonNodeUI.jsx
 * 
 * Comparison view for fundamental metrics across 2-3 tickers.
 * Displays revenue growth, EPS growth, margins, debt, FCF, dividend in table format.
 * Collapsed by default, green/yellow/red color coding for performance.
 * 
 * PHASE 4 of Comparison UX refactoring (Dec 19, 2025)
 */

import React, { useState } from 'react'
import { ChevronDown, ChevronUp, TrendingUp, DollarSign, PieChart, Percent } from 'lucide-react'
import { Badge } from '../ui/badge'
import { DarkTooltip } from '../explainability/tooltips/TooltipLibrary'

/**
 * FundamentalsComparisonNodeUI
 * 
 * @param {Array} tickers - Array of ticker objects from numericalPanel
 * @param {string} veeNarrative - Optional VEE unified narrative for fundamentals
 * @param {string} className - Optional CSS classes
 */
const FundamentalsComparisonNodeUI = ({ tickers = [], veeNarrative, className = '' }) => {
  const [isExpanded, setIsExpanded] = useState(false)

  if (!tickers || tickers.length === 0) {
    return null
  }

  /**
   * Get fundamental metric value from ticker (fallback to 0 if missing)
   * CRITICAL: Backend sends Z-SCORES (_z suffix), not raw values
   * We use z-scores directly for comparison (already normalized)
   */
  const getMetric = (ticker, key) => {
    // Try _z suffix first (backend format), then raw key (legacy)
    const zScoreKey = `${key}_z`
    const value = ticker[zScoreKey] ?? ticker[key] ?? null
    
    // Log missing values for debugging
    if (value === null) {
      console.warn(`[FundamentalsComparison] Missing ${key} / ${zScoreKey} for ${ticker.ticker}`)
    }
    
    return value
  }

  /**
   * Format percentage (e.g., 0.15 → "15.0%")
   * CRITICAL: Backend sends Z-SCORES, not percentages!
   * Z-scores are already normalized (-3 to +3 range)
   * For display, we show z-score directly with sigma symbol
   */
  const formatPercent = (value) => {
    if (value === null || value === undefined) return 'N/A'
    // If it's a z-score (range -3 to +3), show as sigma
    if (Math.abs(value) <= 5) {
      return `${value.toFixed(2)}σ`
    }
    // Legacy: actual percentage value
    return `${(value * 100).toFixed(1)}%`
  }

  /**
   * Format decimal (e.g., 1.234 → "1.23")
   * Z-scores shown as sigma values
   */
  const formatDecimal = (value) => {
    if (value === null || value === undefined) return 'N/A'
    // If it's a z-score (range -3 to +3), show as sigma
    if (Math.abs(value) <= 5) {
      return `${value.toFixed(2)}σ`
    }
    return value.toFixed(2)
  }

  /**
   * Get color badge for metric (green = good, yellow = average, red = bad)
   * 
   * CRITICAL: Backend sends Z-SCORES (normalized values, -3 to +3 range)
   * 
   * Z-score interpretation:
   * - >1.0σ = Top quartile (green/strong)
   * - 0 to 1.0σ = Above average (yellow)
   * - -1.0 to 0σ = Below average (yellow)
   * - <-1.0σ = Bottom quartile (red/weak)
   * 
   * Special case for debt_to_equity: Lower is better (inverted)
   */
  const getMetricBadge = (metricKey, value) => {
    if (value === null || value === undefined) return { color: 'bg-gray-400', label: 'N/A' }

    // For debt_to_equity, invert logic (lower is better)
    if (metricKey === 'debt_to_equity') {
      if (value < -1.0) return { color: 'bg-green-500', label: 'Low' }      // Much lower than average
      if (value < 0) return { color: 'bg-yellow-500', label: 'Moderate' }  // Below average
      if (value < 1.0) return { color: 'bg-yellow-500', label: 'Moderate' } // Above average
      return { color: 'bg-red-500', label: 'High' }                        // Much higher than average
    }

    // For all other metrics: Higher is better
    if (value > 1.5) return { color: 'bg-green-500', label: 'Exceptional' } // Top 7%
    if (value > 1.0) return { color: 'bg-green-500', label: 'Strong' }      // Top quartile
    if (value > 0) return { color: 'bg-yellow-500', label: 'Average' }      // Above average
    if (value > -1.0) return { color: 'bg-yellow-500', label: 'Below Avg' } // Below average
    return { color: 'bg-red-500', label: 'Weak' }                          // Bottom quartile
  }

  /**
   * Fundamental metrics configuration
   */
  const fundamentalMetrics = [
    {
      key: 'revenue_growth_yoy',
      label: 'Revenue Growth (YoY)',
      icon: TrendingUp,
      format: formatPercent,
      description: 'Year-over-year revenue growth rate',
      tooltip: 'Measures top-line growth. Strong: >15% (expanding market share), Average: 5-15% (steady growth), Weak: <5% (stagnant or declining).'
    },
    {
      key: 'eps_growth_yoy',
      label: 'EPS Growth (YoY)',
      icon: TrendingUp,
      format: formatPercent,
      description: 'Year-over-year earnings per share growth',
      tooltip: 'Bottom-line profitability growth. Strong: >15% (improving margins + revenue), Average: 5-15%, Weak: <5% (profit compression).'
    },
    {
      key: 'net_margin',
      label: 'Net Margin',
      icon: Percent,
      format: formatPercent,
      description: 'Net income as percentage of revenue',
      tooltip: 'Profitability efficiency. Strong: >20% (high margin business), Average: 10-20%, Weak: <10% (low margin or commodity).'
    },
    {
      key: 'debt_to_equity',
      label: 'Debt-to-Equity',
      icon: PieChart,
      format: formatDecimal,
      description: 'Total debt divided by shareholder equity',
      tooltip: 'Financial leverage. Low: <0.5 (conservative balance sheet), Moderate: 0.5-1.5, High: >1.5 (elevated financial risk).'
    },
    {
      key: 'free_cash_flow',
      label: 'Free Cash Flow',
      icon: DollarSign,
      format: (val) => val === null || val === undefined ? 'N/A' : `$${(val / 1e9).toFixed(2)}B`,
      description: 'Operating cash flow minus capital expenditures',
      tooltip: 'Cash generation after investments. Positive: healthy cash generation for dividends/buybacks. Negative: cash burn (growth or distress).'
    },
    {
      key: 'dividend_yield',
      label: 'Dividend Yield',
      icon: DollarSign,
      format: formatPercent,
      description: 'Annual dividend as percentage of stock price',
      tooltip: 'Shareholder returns. High: >3% (income stock), Moderate: 1-3%, Low: <1% (growth stock, reinvesting profits).'
    }
  ]

  return (
    <div className={`bg-white rounded-lg border border-gray-200 overflow-hidden ${className}`}>
      {/* Header (Collapsible) */}
      <div
        className="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          <PieChart className="w-5 h-5 text-blue-600" />
          <h3 className="text-sm font-semibold text-gray-900">Fundamental Comparison</h3>
          <Badge variant="outline" className="text-xs">
            {tickers.length} tickers
          </Badge>
        </div>
        <button className="p-1 hover:bg-gray-100 rounded">
          {isExpanded ? (
            <ChevronUp className="w-4 h-4 text-gray-600" />
          ) : (
            <ChevronDown className="w-4 h-4 text-gray-600" />
          )}
        </button>
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="p-4 bg-gray-50 border-t border-gray-200">
          {/* Fundamentals Table */}
          <div className="overflow-x-auto mb-4">
            <table className="w-full text-sm">
              <thead className="bg-white border-b">
                <tr>
                  <th className="px-3 py-2 text-left text-xs font-semibold text-gray-700">Metric</th>
                  {tickers.map((t) => (
                    <th key={t.ticker} className="px-3 py-2 text-center text-xs font-semibold text-gray-700">
                      {t.ticker}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-100">
                {fundamentalMetrics.map((metric) => {
                  const Icon = metric.icon
                  return (
                    <tr key={metric.key} className="hover:bg-gray-50 transition-colors">
                      <td className="px-3 py-3">
                        <div className="flex items-center gap-2">
                          <Icon className="w-4 h-4 text-gray-500" />
                          <div className="flex-1">
                            <div className="flex items-center gap-1">
                              <div className="font-medium text-gray-900">{metric.label}</div>
                              <DarkTooltip content={metric.tooltip} />
                            </div>
                            <div className="text-xs text-gray-500">{metric.description}</div>
                          </div>
                        </div>
                      </td>
                      {tickers.map((t) => {
                        const value = getMetric(t, metric.key)
                        const badge = getMetricBadge(metric.key, value)
                        return (
                          <td key={t.ticker} className="px-3 py-3 text-center">
                            <div className="flex flex-col items-center gap-1">
                              <span className="text-base font-semibold text-gray-900">
                                {metric.format(value)}
                              </span>
                              <Badge className={`${badge.color} text-white text-xs px-2 py-0.5`}>
                                {badge.label}
                              </Badge>
                            </div>
                          </td>
                        )
                      })}
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          {/* VEE Narrative (if provided) */}
          {veeNarrative && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <PieChart className="w-4 h-4 text-blue-600" />
                <h4 className="text-sm font-semibold text-blue-900">Fundamental Analysis</h4>
              </div>
              <p className="text-sm text-gray-700 leading-relaxed">{veeNarrative}</p>
            </div>
          )}

          {/* Auto-generated comparison text (if VEE not provided) */}
          {!veeNarrative && (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <p className="text-sm text-gray-700 leading-relaxed">
                Fundamental comparison across <strong>{tickers.length} tickers</strong>. 
                Review revenue growth, profitability margins, debt levels, cash generation, and shareholder returns 
                to assess financial health and sustainability.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default FundamentalsComparisonNodeUI
