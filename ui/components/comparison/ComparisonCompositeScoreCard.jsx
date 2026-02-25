/**
 * COMPARISON COMPOSITE SCORE CARD
 * 
 * Uses ZScoreCardMulti library for consistent design with Neural Engine cards
 * Shows overall winner with composite percentile ranking
 * 
 * @component ComparisonCompositeScoreCard
 * @created Dec 14, 2025
 * @updated Dec 14, 2025 - Refactored to use ZScoreCardMulti library
 * @usage Comparison node only (NOT for single ticker analysis)
 * 
 * Features:
 * - Same visual design as ZScoreCardMulti (4 cards per row)
 * - Percentile ranking display (0-100%)
 * - Winner/loser indicators (👍/👎)
 * - VEE tooltip integration
 * - Color-coded based on composite score
 */

'use client'

import { Trophy } from 'lucide-react'
import { ZScoreCardMulti } from '../cards/CardLibrary'

export default function ComparisonCompositeScoreCard({ 
  tickers = [],        // Array of {ticker, composite_score, ...} objects
  className = '' 
}) {
  if (!tickers || tickers.length < 2) {
    return null
  }

  // ZScoreCardMulti expects factorKey to be a z-score field
  // composite_score is 0-1 percentile, convert to pseudo z-score for color coding
  const tickersWithPseudoZ = tickers.map(t => ({
    ...t,
    composite_z: t.composite_score ? (t.composite_score - 0.5) * 2 : 0 // Map 0-1 to -1 to +1
  }))

  return (
    <ZScoreCardMulti
      label="Composite Score"
      icon={Trophy}
      tickers={tickersWithPseudoZ}
      factorKey="composite_z"
      inverted={false}
      veeSimple="Overall performance ranking across all factors"
      veeTechnical="Composite score combines momentum, trend, volatility, sentiment, and fundamentals into a single percentile ranking. Values >0.7 are top performers, <0.4 are underperformers."
      className={className}
    />
  )
}
