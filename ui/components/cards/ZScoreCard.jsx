/**
 * Z-SCORE CARD COMPONENT
 * Display z-score metrics with automatic color coding + VEE tooltips
 * Supports BOTH single-ticker and multi-ticker comparison modes
 * 
 * @component ZScoreCard
 * @created Dec 11, 2025
 * @updated Dec 14, 2025 - Added comparison mode support (NO logo, ticker only)
 * @migration Replaces FundamentalCard + ComparisonNeuralEngineCard
 * @features
 *   - Automatic color coding based on z-score thresholds
 *   - VEE tooltip integration (simple + technical explanations)
 *   - Emoji indicators (🚀 ✅ 👍 😐 ⚠️ ❌)
 *   - Performance tier labels (Top quartile, Above average, etc.)
 *   - COMPARISON MODE: Grid layout matching SingleTickerUI (4 cards per row)
 * 
 * @modes
 *   - single: Default single-ticker display (existing behavior)
 *   - comparison: Compact 4-column grid (NO logos, ticker text only)
 */

'use client'
import { ThumbsUp, ThumbsDown } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { VeeTooltip } from '@/components/explainability/tooltips/TooltipLibrary'
import { tokens } from '../theme/tokens'

/**
 * Z-score to color class mapping
 * Based on FundamentalsPanel.jsx existing logic
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
 * Z-score to emoji mapping
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
 * Format z-score with + sign for positive values
 */
const formatZScore = (z) => {
  if (z === null || z === undefined) return 'N/A'
  return z >= 0 ? `+${z.toFixed(2)}` : z.toFixed(2)
}

/**
 * Get performance tier label
 */
const getPerformanceTier = (z) => {
  if (z === null || z === undefined) return null
  if (z > 1.0) return 'Top quartile'
  if (z > 0.5) return 'Above average'
  if (z > -0.5) return 'Average'
  if (z > -1.0) return 'Below average'
  return 'Bottom quartile'
}

export default function ZScoreCard({ 
  // SINGLE MODE props
  label,           // Factor name (e.g., "Momentum", "Trend")
  value,           // z-score number (single ticker mode)
  icon: Icon,
  veeSimple,       // VEE simple explanation
  veeTechnical,    // VEE technical explanation
  
  // COMPARISON MODE props (NEW - Dec 14, 2025)
  mode = 'single', // 'single' | 'comparison'
  tickers,         // Array of {ticker, [factorKey]: z_score} (comparison mode only)
  factorKey,       // Factor key to extract (e.g., 'momentum_z', 'trend_z')
  inverted = false, // For volatility (lower is better)
  
  className = ''
}) {
  
  // ========================================
  // COMPARISON MODE: Multi-ticker layout
  // ========================================
  if (mode === 'comparison' && tickers && factorKey) {
    // Sort tickers by factor value (inverted for volatility)
    const sortedTickers = [...tickers].sort((a, b) => {
      const aVal = a[factorKey] ?? -999
      const bVal = b[factorKey] ?? -999
      return inverted ? aVal - bVal : bVal - aVal
    })
    
    const winner = sortedTickers[0]
    const loser = sortedTickers[sortedTickers.length - 1]
    
    return (
      <div className={`rounded-lg border-2 p-2 transition-all ${className}`}>
        {/* Compact Header */}
        <div className="flex items-start justify-between mb-2">
          {Icon && <Icon className="w-3 h-3" />}
          <span className="text-[10px] font-medium">{label}</span>
        </div>
        
        {/* Ticker Grid (4 columns like SingleTickerUI) */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-1">
          {sortedTickers.map((item) => {
            const z = item[factorKey]
            const isWinner = item.ticker === winner.ticker && z !== null && z !== undefined
            const isLoser = item.ticker === loser.ticker && z !== null && z !== undefined && tickers.length > 2
            
            const colorClass = getZScoreColor(z)
            const emoji = getZScoreEmoji(z)
            const tier = getPerformanceTier(z)
            
            return (
              <div
                key={item.ticker}
                className={`rounded border p-1.5 text-center ${colorClass}`}
              >
                {/* Ticker Name Only (NO logo) */}
                <div className="flex items-center justify-center gap-1 mb-1">
                  <span className="text-[10px] font-bold">{item.ticker}</span>
                  {isWinner && <span className="text-xs">👍</span>}
                  {isLoser && <span className="text-xs">👎</span>}
                </div>
                
                {/* Z-Score + Emoji */}
                <div className="flex items-center justify-center gap-1 mb-1">
                  <span className="text-base">{emoji}</span>
                  <span className="text-sm font-bold">{formatZScore(z)}</span>
                </div>
                
                {/* Performance Tier */}
                {tier && (
                  <div className="text-[9px] opacity-75 truncate">{tier}</div>
                )}
              </div>
            )
          })}
        </div>
      </div>
    )
  }
  
  // ========================================
  // SINGLE MODE: Original single-ticker card
  // ========================================
  const colorClass = getZScoreColor(value)
  const emoji = getZScoreEmoji(value)
  const tier = getPerformanceTier(value)

  // Build VEE tooltip content
  const tooltipContent = (
    <div>
      <p className="text-sm font-bold text-gray-900 mb-2">{veeSimple}</p>
      <p className="text-xs text-gray-700 leading-relaxed whitespace-pre-line">
        {veeTechnical}
      </p>
      <div className="mt-3 pt-3 border-t border-gray-200">
        <p className="text-xs text-gray-500">
          Current Z-Score: <span className="font-semibold text-vitruvyan-accent">{formatZScore(value)}</span>
        </p>
      </div>
    </div>
  )

  return (
    <VeeTooltip content={tooltipContent}>
      <div className={`rounded-lg border-2 p-2 transition-all hover:shadow-md cursor-pointer ${colorClass} ${className}`}>
        <div className="flex items-start justify-between mb-1">
          {Icon && <Icon className="w-3 h-3" />}
          <span className="text-base">{emoji}</span>
        </div>
        <div className="text-[10px] font-medium mb-0.5">{label}</div>
        <div className="text-sm font-bold">{formatZScore(value)}</div>
        {tier && (
          <div className="text-[10px] mt-0.5 opacity-75">{tier}</div>
        )}
      </div>
    </VeeTooltip>
  )
}
