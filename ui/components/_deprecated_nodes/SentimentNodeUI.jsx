/**
 * SENTIMENT NODE UI
 * 
 * Displays sentiment analysis from sentiment_node with expandable sources.
 * 
 * Backend Node: sentiment_node.py
 * State Keys: state.numerical_panel[].sentiment_z, sentiment_label, sentiment_avg
 * 
 * Props:
 * - numericalPanel: NumericalPanelItem[] - Array with sentiment data
 * - horizonData: object - Data for all 3 horizons from Neural Engine
 * - activeHorizon: string - Currently selected horizon
 * - className?: string - Optional Tailwind classes
 */

'use client'

import { Megaphone } from 'lucide-react'
import { formatSentiment, formatZScore, getSentimentColor, getSentimentEmoji } from '@/lib/utils/formatters'
import { MetricCard } from '../cards/CardLibrary'
import { SentimentTooltip } from '../explainability/tooltips/TooltipLibrary'

export default function SentimentNodeUI({ numericalPanel, horizonData, activeHorizon, className = '' }) {
  
  // 🔥 Get real sentiment data from horizonData if available
  const getRealSentimentData = () => {
    if (!horizonData || !activeHorizon) return numericalPanel

    const currentHorizonData = horizonData[activeHorizon]
    if (!currentHorizonData?.ranking) return numericalPanel

    // Extract sentiment data from Neural Engine response
    const stocks = currentHorizonData.ranking.stocks || []
    if (stocks.length === 0) return numericalPanel

    // Map to numericalPanel format
    return stocks.map(stock => ({
      ticker: stock.ticker,
      sentiment_z: stock.factors?.sentiment_z || null,
      sentiment_label: stock.sentiment_label || null,
      sentiment_avg: stock.sentiment_avg || null
    }))
  }

  const sentimentData = getRealSentimentData()

  // Guard: Don't render if no sentiment data
  if (!sentimentData || sentimentData.length === 0) {
    return null
  }

  // Filter items with sentiment data
  const itemsWithSentiment = sentimentData.filter(
    (item) => item.sentiment_z !== null || item.sentiment_label
  )

  if (itemsWithSentiment.length === 0) {
    return null
  }

  return (
    <div className={`space-y-2 ${className}`}>
      {/* Header */}
      <div className="flex items-center gap-2 text-sm text-gray-600">
        <Megaphone size={16} className="text-vitruvyan-accent" />
        <span className="font-semibold">Market Sentiment Analysis</span>
      </div>

      {/* Sentiment Items */}
      <div className="flex flex-col gap-2">
        {itemsWithSentiment.map((item, index) => (
          <div
            key={`${item.ticker}-${index}`}
            className="flex items-center justify-between p-3 rounded-lg border border-gray-200 bg-white"
          >
            {/* Ticker with Logo */}
            <div className="flex items-center gap-3">
              {/* Yahoo Finance Logo */}
              <img 
                src={`https://logo.clearbit.com/${item.ticker.toLowerCase()}.com`}
                alt={`${item.ticker} logo`}
                className="w-8 h-8 rounded"
                onError={(e) => {
                  // Fallback to Yahoo Finance icon API
                  e.target.onerror = null
                  e.target.src = `https://storage.googleapis.com/iex/api/logos/${item.ticker}.png`
                }}
              />
              <span className="font-semibold text-gray-900">{item.ticker}</span>
              
              {/* Sentiment Label with Emoji */}
              {item.sentiment_label && (
                <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium ${getSentimentColor(item.sentiment_label)}`}>
                  <span>{getSentimentEmoji(item.sentiment_label)}</span>
                  <span className="capitalize">{item.sentiment_label}</span>
                </span>
              )}
            </div>

            {/* 🎯 Sentiment Metrics with MetricCard (Dec 24, 2025) */}
            <div className="flex items-center gap-4 text-sm">
              {/* Z-Score with SentimentTooltip */}
              {item.sentiment_z !== null && item.sentiment_z !== undefined && (
                <MetricCard
                  label="Sentiment Z"
                  value={formatZScore(item.sentiment_z)}
                  color={item.sentiment_z > 0 ? 'green' : item.sentiment_z < 0 ? 'red' : 'gray'}
                  tooltip={<SentimentTooltip value={item.sentiment_z} ticker={item.ticker} />}
                  compact
                />
              )}
              
              {/* LEGACY: Fallback if MetricCard not showing */}
              {false && item.sentiment_z !== null && (
                <div className="text-right group relative">
                  <div className="text-xs text-gray-500">Z-Score</div>
                  <div className={`font-mono font-medium ${
                    item.sentiment_z > 0 ? 'text-green-600' : 
                    item.sentiment_z < 0 ? 'text-red-600' : 
                    'text-gray-600'
                  }`}>
                    {formatZScore(item.sentiment_z)}
                  </div>
                  {/* Tooltip */}
                  <div className="absolute hidden group-hover:block bottom-full right-0 mb-2 w-64 p-2 bg-gray-900 text-white text-xs rounded shadow-lg z-50">
                    <strong>Z-Score:</strong> Measures how unusual this sentiment is compared to other tickers. 
                    Above +1.5 is unusually positive, below -1.5 is unusually negative.
                    <div className="absolute top-full right-4 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></div>
                  </div>
                </div>
              )}

              {/* Average Score with Tooltip */}
              {item.sentiment_avg !== null && item.sentiment_avg !== undefined && (
                <div className="text-right group relative">
                  <div className="text-xs text-gray-500">Score</div>
                  <div className={`font-medium ${
                    item.sentiment_avg > 0 ? 'text-green-600' : 
                    item.sentiment_avg < 0 ? 'text-red-600' : 
                    'text-gray-600'
                  }`}>
                    {formatSentiment(item.sentiment_avg)}
                  </div>
                  {/* Tooltip */}
                  <div className="absolute hidden group-hover:block bottom-full right-0 mb-2 w-64 p-2 bg-gray-900 text-white text-xs rounded shadow-lg z-50">
                    <strong>Score:</strong> Raw sentiment score from -1 (very negative) to +1 (very positive). 
                    Based on FinBERT analysis of news and social media.
                    <div className="absolute top-full right-4 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></div>
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Minimalist Source Note */}
      <div className="flex items-center gap-2 p-2 text-xs text-gray-500 italic">
        <Megaphone size={12} className="text-gray-400" />
        <span>FinBERT analysis • Sources: Google News & Reddit</span>
      </div>

      {/* Note for single ticker */}
      {itemsWithSentiment.length === 1 && itemsWithSentiment[0].sentiment_z === null && (
        <p className="text-xs text-gray-500 italic">
          ℹ️ Z-score requires 2+ tickers for statistical comparison
        </p>
      )}
    </div>
  )
}
