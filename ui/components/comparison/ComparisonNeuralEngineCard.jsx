/**
 * COMPARISON NEURAL ENGINE CARD
 * 
 * Side-by-side z-score comparison for 3 factors (Momentum, Trend, Volatility)
 * Shows which ticker wins each factor with visual indicators
 * 
 * @component ComparisonNeuralEngineCard
 * @created Dec 14, 2025
 * @updated Dec 14, 2025 - Removed sentiment_z (kept separate for consistency with single ticker UI)
 * @usage Comparison node only (NOT for single ticker analysis)
 * 
 * Features:
 * - Factor-by-factor comparison grid (3 factors)
 * - Winner badges per factor
 * - Color-coded z-scores (green=positive, red=negative)
 * - Emoji indicators for performance tier
 * - Tooltips with VEE explanations
 * - Sentiment kept separate in ComparisonSentimentCard (FinBERT)
 */

'use client'

import { TrendingUp, Activity, AlertTriangle, MessageCircle, Crown, Trophy } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { DarkTooltip } from '../explainability/tooltips/TooltipLibrary'
// import { TickerLogo } from '../images/TickerLogo'

/**
 * Factor configuration
 */
const FACTORS = [
  {
    key: 'momentum_z',
    label: 'Momentum',
    icon: TrendingUp,
    color: 'blue',
    tooltip: 'Price acceleration over 30 days. Higher = stronger momentum.'
  },
  {
    key: 'trend_z',
    label: 'Trend',
    icon: Activity,
    color: 'indigo',
    tooltip: 'SMA/EMA consensus. Higher = stronger uptrend structure.'
  },
  {
    key: 'vola_z',
    label: 'Volatility',
    icon: AlertTriangle,
    color: 'green',
    tooltip: 'Price swing intensity (inverted). LOWER = better (less risky).',
    inverted: true
  }
  // ❌ REMOVED sentiment_z - kept separate in ComparisonSentimentCard (consistency with single ticker UI)
]

/**
 * Get emoji based on z-score (preserved for legacy, but using thumb icons now)
 */
function getEmoji(z, inverted = false) {
  if (z === null || z === undefined) return '😐'
  const value = inverted ? -z : z
  if (value >= 1.5) return '🚀'
  if (value >= 0.5) return '✅'
  if (value >= -0.5) return '😐'
  if (value >= -1.5) return '⚠️'
  return '❌'
}

/**
 * Get z-score color class
 */
function getZScoreColor(z, inverted = false) {
  if (z === null || z === undefined) return 'bg-gray-100 text-gray-700 border-gray-300'
  const value = inverted ? -z : z
  if (value >= 0.5) return 'bg-green-100 text-green-700 border-green-300'
  if (value >= -0.5) return 'bg-gray-100 text-gray-600 border-gray-300'
  return 'bg-red-100 text-red-700 border-red-300'
}

/**
 * Format z-score
 */
function formatZScore(z) {
  if (z === null || z === undefined) return 'N/A'
  return z.toFixed(2)
}

/**
 * Get performance tier label
 */
function getPerformanceTier(z, inverted = false) {
  if (z === null || z === undefined) return 'N/A'
  const value = inverted ? -z : z
  if (value >= 1.5) return 'Exceptional'
  if (value >= 0.5) return 'Above Average'
  if (value >= -0.5) return 'Average'
  if (value >= -1.5) return 'Below Average'
  return 'Weak'
}

export default function ComparisonNeuralEngineCard({ 
  tickers = [],        // Array of {ticker, momentum_z, trend_z, vola_z, sentiment_z, ...}
  className = '' 
}) {
  if (!tickers || tickers.length < 2) {
    return (
      <div className={`border border-gray-200 rounded-lg p-4 bg-gray-50 ${className}`}>
        <p className="text-sm text-gray-500 text-center">
          Neural Engine comparison requires 2+ tickers
        </p>
      </div>
    )
  }

  return (
    <div className={`border border-gray-200 rounded-lg bg-white shadow-sm ${className}`}>
      {/* Header */}
      <div className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <Trophy className="w-5 h-5 text-blue-600" />
          <span className="text-base font-semibold text-gray-900">Neural Engine Factor Comparison</span>
          <DarkTooltip content="Multi-factor z-score analysis. Each ticker compared across 3 technical factors." />
        </div>
      </div>

      {/* Factor Grid - Side-by-Side Ticker Comparison */}
      <div className="p-4 space-y-6">
        {FACTORS.map(factor => {
          // Find winner and loser for this factor
          const sortedByFactor = [...tickers].sort((a, b) => {
            const aVal = a[factor.key] || -999
            const bVal = b[factor.key] || -999
            return factor.inverted ? aVal - bVal : bVal - aVal // Inverted for volatility (lower is better)
          })
          const winner = sortedByFactor[0]
          const loser = sortedByFactor[sortedByFactor.length - 1]

          return (
            <div key={factor.key} className="border border-gray-200 rounded-lg overflow-hidden">
              {/* Factor Header */}
              <div className={`px-4 py-3 bg-${factor.color}-50 border-b border-${factor.color}-200`}>
                <div className="flex items-center gap-2">
                  <factor.icon className={`w-5 h-5 text-${factor.color}-600`} />
                  <span className="text-sm font-semibold text-gray-900">{factor.label}</span>
                  <DarkTooltip content={factor.tooltip} />
                </div>
              </div>

              {/* Side-by-Side Ticker Cards (2-4 tickers support - Dec 24, 2025) */}
              <div className={`grid divide-x divide-gray-200 ${
                tickers.length === 2 ? 'grid-cols-2' :
                tickers.length === 3 ? 'grid-cols-3' :
                'grid-cols-2 lg:grid-cols-4'
              }`}>
                {sortedByFactor.map(item => {
                  const z = item[factor.key]
                  const isWinner = item.ticker === winner.ticker && z !== null
                  const isLoser = item.ticker === loser.ticker && z !== null && tickers.length > 2

                  return (
                    <div
                      key={item.ticker}
                      className={`p-4 ${
                        isWinner ? 'bg-green-50' : isLoser ? 'bg-red-50' : 'bg-white'
                      }`}
                    >
                      {/* Ticker Logo + Name */}
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                          {/* <TickerLogo ticker={item.ticker} size="md" /> */}
                          <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center text-xs font-bold text-gray-600">
                            {item.ticker.charAt(0)}
                          </div>
                          <span className="font-semibold text-gray-900">{item.ticker}</span>
                        </div>
                        
                        {/* Thumb Icon */}
                        {isWinner && (
                          <div className="flex items-center gap-1">
                            <span className="text-green-600 text-lg">👍</span>
                            <Badge className="text-xs bg-green-600 text-white">Best</Badge>
                          </div>
                        )}
                        {isLoser && (
                          <div className="flex items-center gap-1">
                            <span className="text-red-600 text-lg">👎</span>
                            <Badge className="text-xs bg-red-600 text-white">Worst</Badge>
                          </div>
                        )}
                      </div>

                      {/* Z-Score Value */}
                      <div className="text-center mb-2">
                        <div className={`inline-block text-2xl font-bold px-3 py-2 rounded-lg border-2 ${getZScoreColor(z, factor.inverted)}`}>
                          {formatZScore(z)}
                        </div>
                      </div>

                      {/* Performance Tier */}
                      <div className="text-center">
                        <span className="text-xs text-gray-600 font-medium">
                          {getPerformanceTier(z, factor.inverted)}
                        </span>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )
        })}
      </div>

      {/* Footer: Legend */}
      <div className="px-4 pb-4 border-t border-gray-200 pt-3 bg-gray-50">
        <div className="text-xs text-gray-600 font-semibold mb-2">Z-Score Performance Tiers:</div>
        <div className="flex flex-wrap gap-3 text-xs text-gray-500">
          <span>🚀 ≥1.5 Exceptional</span>
          <span>✅ ≥0.5 Above Average</span>
          <span>😐 -0.5 to 0.5 Average</span>
          <span>⚠️ ≤-0.5 Below Average</span>
          <span>❌ ≤-1.5 Weak</span>
        </div>
      </div>
    </div>
  )
}
