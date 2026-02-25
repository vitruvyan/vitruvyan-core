/**
 * Z-SCORE CARD MULTI-TICKER COMPONENT
 * Extended variant of ZScoreCard for comparison/multi-ticker analysis
 * Shows ALL tickers inside a single card (like SingleTickerUI design)
 * 
 * @component ZScoreCardMulti
 * @created Dec 14, 2025
 * @based_on ZScoreCard.jsx (single ticker variant)
 * @features
 *   - Same visual design as SingleTickerUI (colors, layout, spacing)
 *   - Multiple tickers displayed inline within card
 *   - Winner/loser badges (👍/👎)
 *   - VEE tooltip integration (same library as ZScoreCard)
 *   - Automatic color coding based on z-score thresholds
 * 
 * @usage ComparisonNodeUI only (NOT for single ticker analysis)
 */

'use client'
import { VeeTooltip } from '@/components/explainability/tooltips/TooltipLibrary'
import { tokens } from '../theme/tokens'

/**
 * Z-score to color class mapping (from ZScoreCard)
 */
const getZScoreColor = (z) => {
  if (z === null || z === undefined) return tokens.colors.zScore.null
  if (z > 1.5) return tokens.colors.zScore.exceptional
  if (z > 1.0) return tokens.colors.zScore.strong
  if (z > 0.5) return tokens.colors.zScore.aboveAverage
  if (z > -0.5) return tokens.colors.zScore.average
  if (z > -1.0) return tokens.colors.zScore.belowAverage
  return tokens.colors.zScore.poor
}

/**
 * Z-score to emoji mapping (from ZScoreCard)
 */
const getZScoreEmoji = (z) => {
  if (z === null || z === undefined) return '—'
  if (z > 1.5) return '🚀'
  if (z > 1.0) return '✅'
  if (z > 0.5) return '👍'
  if (z > -0.5) return '😐'
  if (z > -1.0) return '⚠️'
  return '❌'
}

/**
 * Format z-score with + sign for positive values (from ZScoreCard)
 */
const formatZScore = (z) => {
  if (z === null || z === undefined) return 'N/A'
  return z >= 0 ? `+${z.toFixed(2)}` : z.toFixed(2)
}

/**
 * Get performance tier label (from ZScoreCard)
 */
const getPerformanceTier = (z) => {
  if (z === null || z === undefined) return null
  if (z > 1.0) return 'Top quartile'
  if (z > 0.5) return 'Above average'
  if (z > -0.5) return 'Average'
  if (z > -1.0) return 'Below average'
  return 'Bottom quartile'
}

/**
 * Calculate average z-score across tickers (for card main value)
 */
const getAverageZScore = (tickers, factorKey) => {
  const validScores = tickers
    .map(t => t[factorKey])
    .filter(z => z !== null && z !== undefined)
  
  if (validScores.length === 0) return null
  return validScores.reduce((sum, z) => sum + z, 0) / validScores.length
}

export default function ZScoreCardMulti({ 
  label,           // Factor name (e.g., "Momentum", "Trend")
  icon: Icon,
  tickers,         // Array of {ticker, [factorKey]: z_score}
  factorKey,       // Factor key to extract (e.g., 'momentum_z', 'trend_z')
  inverted = false, // For volatility (lower is better)
  veeSimple,       // VEE simple explanation (optional, can be generic)
  veeTechnical,    // VEE technical explanation (optional, can be generic)
  className = ''
}) {
  // Calculate average z-score for card display
  const avgZScore = getAverageZScore(tickers, factorKey)
  const colorClass = getZScoreColor(avgZScore)
  const emoji = getZScoreEmoji(avgZScore)
  const tier = getPerformanceTier(avgZScore)

  // Sort tickers by factor value (inverted for volatility)
  const sortedTickers = [...tickers].sort((a, b) => {
    const aVal = a[factorKey] ?? -999
    const bVal = b[factorKey] ?? -999
    return inverted ? aVal - bVal : bVal - aVal
  })
  
  const winner = sortedTickers[0]
  const loser = sortedTickers[sortedTickers.length - 1]

  // Build VEE tooltip content (same format as ZScoreCard)
  const tooltipContent = veeSimple && veeTechnical ? (
    <div>
      <p className="text-sm font-bold text-gray-900 mb-2">{veeSimple}</p>
      <p className="text-xs text-gray-700 leading-relaxed whitespace-pre-line">
        {veeTechnical}
      </p>
      <div className="mt-3 pt-3 border-t border-gray-200">
        <p className="text-xs text-gray-500">
          Average Z-Score: <span className="font-semibold text-vitruvyan-accent">{formatZScore(avgZScore)}</span>
        </p>
      </div>
    </div>
  ) : (
    <div>
      <p className="text-sm font-bold text-gray-900 mb-2">{label} Comparison</p>
      <p className="text-xs text-gray-700">
        Average z-score across {tickers.length} tickers: {formatZScore(avgZScore)}
      </p>
    </div>
  )

  return (
    <VeeTooltip content={tooltipContent}>
      <div className={`rounded-lg border-2 p-2 transition-all hover:shadow-md cursor-pointer ${colorClass} ${className}`}>
        {/* Header (same as ZScoreCard) */}
        <div className="flex items-start justify-between mb-1">
          {Icon && <Icon className="w-3 h-3" />}
          <span className="text-base">{emoji}</span>
        </div>
        
        {/* Label + Average Z-Score (same layout as ZScoreCard) */}
        <div className="text-[10px] font-medium mb-0.5">{label}</div>
        <div className="text-sm font-bold">{formatZScore(avgZScore)}</div>
        
        {/* Performance Tier */}
        {tier && (
          <div className="text-[10px] mt-0.5 opacity-75">{tier}</div>
        )}
        
        {/* Ticker Breakdown (NEW: inline list) */}
        <div className="mt-2 pt-2 border-t border-current border-opacity-20">
          <div className="flex flex-wrap gap-1 text-[9px]">
            {sortedTickers.map(item => {
              const z = item[factorKey]
              const isWinner = item.ticker === winner.ticker && z !== null && z !== undefined
              const isLoser = item.ticker === loser.ticker && z !== null && z !== undefined && tickers.length > 2
              
              return (
                <span 
                  key={item.ticker}
                  className={`inline-flex items-center gap-0.5 px-1 py-0.5 rounded ${
                    isWinner ? 'font-bold' : ''
                  }`}
                >
                  {item.ticker} {formatZScore(z)}
                  {isWinner && ' 👍'}
                  {isLoser && ' 👎'}
                </span>
              )
            })}
          </div>
        </div>
      </div>
    </VeeTooltip>
  )
}
