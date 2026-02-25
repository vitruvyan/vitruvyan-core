/**
 * COMPARISON SENTIMENT CARD
 * 
 * Side-by-side sentiment comparison for 2+ tickers
 * Shows which ticker has better sentiment with visual indicators
 * 
 * @component ComparisonSentimentCard
 * @created Dec 14, 2025
 * @usage Comparison node only (NOT for single ticker analysis)
 * 
 * Features:
 * - Visual winner/loser indicators
 * - Color-coded badges (green=positive, red=negative, gray=neutral)
 * - Delta calculation between top and bottom
 * - Emoji sentiment indicators
 * - Logo fallback with fixed dimensions
 */

'use client'

import { TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { DarkTooltip, SentimentTooltip } from '../explainability/tooltips/TooltipLibrary'
// import { TickerLogo } from '../images/TickerLogo'

/**
 * Get sentiment emoji based on z-score
 */
function getSentimentEmoji(z) {
  if (z === null || z === undefined) return '😐'
  if (z >= 0.5) return '😊' // Positive
  if (z >= 0) return '🙂' // Slightly positive
  if (z >= -0.5) return '😐' // Neutral
  return '😞' // Negative
}

/**
 * Get sentiment label
 */
function getSentimentLabel(z) {
  if (z === null || z === undefined) return 'N/A'
  if (z >= 0.5) return 'Positive'
  if (z >= 0) return 'Slightly Positive'
  if (z >= -0.5) return 'Neutral'
  return 'Negative'
}

/**
 * Get sentiment badge color
 */
function getSentimentColor(z) {
  if (z === null || z === undefined) return 'bg-[rgba(115,115,115,0.05)] text-[rgba(82,82,82,1)] border-[rgba(115,115,115,0.15)]'
  if (z >= 0.5) return 'bg-[rgba(34,197,94,0.08)] text-[rgba(22,163,74,1)] border-[rgba(34,197,94,0.20)]'
  if (z >= 0) return 'bg-[rgba(34,197,94,0.05)] text-[rgba(22,163,74,1)] border-[rgba(34,197,94,0.15)]'
  if (z >= -0.5) return 'bg-[rgba(115,115,115,0.05)] text-[rgba(82,82,82,1)] border-[rgba(115,115,115,0.15)]'
  return 'bg-[rgba(239,68,68,0.08)] text-[rgba(220,38,38,1)] border-[rgba(239,68,68,0.20)]'
}

/**
 * Format z-score with sign
 */
function formatZScore(z) {
  if (z === null || z === undefined) return 'N/A'
  return z >= 0 ? `+${z.toFixed(2)}` : z.toFixed(2)
}

export default function ComparisonSentimentCard({ 
  tickers = [],        // Array of {ticker, sentiment_z, ...} objects from numericalPanel
  className = '' 
}) {
  if (!tickers || tickers.length < 2) {
    return (
      <div className={`border border-gray-200 rounded-lg p-4 bg-gray-50 ${className}`}>
        <p className="text-sm text-gray-500 text-center">
          Sentiment comparison requires 2+ tickers
        </p>
      </div>
    )
  }

  // Sort by sentiment_z (descending)
  const sortedTickers = [...tickers].sort((a, b) => 
    (b.sentiment_z || -999) - (a.sentiment_z || -999)
  )

  const winner = sortedTickers[0]
  const loser = sortedTickers[sortedTickers.length - 1]
  const delta = (winner.sentiment_z || 0) - (loser.sentiment_z || 0)
  const isTied = Math.abs(delta) <= 0.15  // Threshold for "tied" sentiment (negligible difference)

  return (
    <div className={`border border-gray-200 rounded-lg bg-white shadow-sm ${className}`}>
      {/* Header */}
      <div className="p-3 bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-gray-900">📊 Market Sentiment Comparison</span>
            <DarkTooltip content="FinBERT analysis of financial news + social media (Reddit, Google News). Higher z-score = more positive sentiment." />
          </div>
          {isTied ? (
            <Badge className="text-xs bg-gray-100 text-gray-700 border-gray-300">
              Tied - Similar Sentiment
            </Badge>
          ) : delta > 0.2 && (
            <Badge className="text-xs bg-purple-100 text-purple-700 border-purple-300">
              Δ {formatZScore(delta)}
            </Badge>
          )}
        </div>
      </div>

      {/* Comparison Grid */}
      <div className="p-4 space-y-3">
        {sortedTickers.map((item, index) => {
          const isWinner = index === 0 && !isTied && delta > 0.2
          const isLoser = index === sortedTickers.length - 1 && !isTied && delta > 0.2
          const z = item.sentiment_z

          return (
            <div
              key={item.ticker}
              className={`flex items-center justify-between p-3 rounded-lg border-2 transition-all ${
                isWinner
                  ? 'bg-[rgba(34,197,94,0.08)] border-[rgba(34,197,94,0.20)] shadow-sm'
                  : isLoser
                  ? 'bg-[rgba(239,68,68,0.08)] border-[rgba(239,68,68,0.20)]'
                  : 'bg-[rgba(115,115,115,0.05)] border-[rgba(115,115,115,0.15)]'
              }`}
            >
              {/* Left: Logo + Ticker */}
              <div className="flex items-center gap-3">
                {/* <TickerLogo ticker={item.ticker} size="md" /> */}
                <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center text-xs font-bold text-gray-600">
                  {item.ticker.charAt(0)}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-gray-900">{item.ticker}</span>
                    {isWinner && <Badge className="text-xs bg-[rgba(34,197,94,0.12)] text-[rgba(22,163,74,1)] border border-[rgba(34,197,94,0.25)] font-medium">Winner</Badge>}
                  </div>
                  <div className="text-xs text-gray-500">
                    {getSentimentLabel(z)}
                  </div>
                </div>
              </div>

              {/* Right: Emoji + Z-Score + Trend */}
              <div className="flex items-center gap-3">
                <span className="text-2xl">{getSentimentEmoji(z)}</span>
                <div className="text-right">
                  <SentimentTooltip value={z} ticker={item.ticker}>
                    <div className={`text-sm font-mono font-bold ${getSentimentColor(z)} px-2 py-1 rounded border cursor-help transition-all hover:shadow-sm`}>
                      {formatZScore(z)}
                    </div>
                  </SentimentTooltip>
                  <div className="text-xs text-gray-500 mt-1">
                    z-score
                  </div>
                </div>
                {isWinner && (
                  <TrendingUp className="w-5 h-5 text-green-600" />
                )}
                {isLoser && delta > 0.2 && (
                  <TrendingDown className="w-5 h-5 text-red-600" />
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Footer: FinBERT Attribution */}
      <div className="px-4 pb-3 text-xs text-gray-500 italic">
        FinBERT analysis • Sources: Google News & Reddit
      </div>
    </div>
  )
}
