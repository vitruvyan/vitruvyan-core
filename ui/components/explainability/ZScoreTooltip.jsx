'use client'

import { useState } from 'react'
import { Info } from 'lucide-react'

/**
 * Z-SCORE TOOLTIP
 * 
 * Interactive tooltip for Neural Engine z-scores.
 * Shows plain language explanation of what the z-score means.
 * 
 * Props:
 * - value: z-score value (number)
 * - metric: metric name ("momentum", "trend", "volatility", "sentiment")
 * - enabled: whether tooltips are globally enabled
 */

export default function ZScoreTooltip({ value, metric, enabled = true }) {
  const [isVisible, setIsVisible] = useState(false)

  if (!enabled) return null

  // Generate plain language explanation
  const getExplanation = () => {
    const absValue = Math.abs(value)
    const direction = value > 0 ? 'above' : 'below'
    const sentiment = value > 0 ? 'positive' : 'negative'
    
    const metricExplanations = {
      momentum: {
        high: `Strong upward momentum. This stock has ${absValue.toFixed(2)} standard deviations MORE momentum than the market average. Buyers are in control.`,
        low: `Weak momentum. This stock has ${absValue.toFixed(2)} standard deviations LESS momentum than the market average. Sellers are dominating.`,
        neutral: 'Neutral momentum. This stock is moving in line with the market average. Wait-and-see approach recommended.'
      },
      trend: {
        high: `Strong uptrend. This stock is ${absValue.toFixed(2)} standard deviations ABOVE the average trend. Price is consistently moving up.`,
        low: `Weak downtrend. This stock is ${absValue.toFixed(2)} standard deviations BELOW the average trend. Price is consistently moving down.`,
        neutral: 'Neutral trend. This stock is moving sideways, neither up nor down compared to the market.'
      },
      volatility: {
        high: `Low volatility. This stock is ${absValue.toFixed(2)} standard deviations LESS volatile than the market average. More stable and predictable.`,
        low: `High volatility. This stock is ${absValue.toFixed(2)} standard deviations MORE volatile than the market average. Expect larger price swings.`,
        neutral: 'Average volatility. This stock has normal price fluctuations compared to the market.'
      },
      sentiment: {
        high: `Positive sentiment. Reddit and news sources are ${absValue.toFixed(2)} standard deviations MORE positive than the average ticker. Social buzz is optimistic.`,
        low: `Negative sentiment. Reddit and news sources are ${absValue.toFixed(2)} standard deviations MORE negative than the average ticker. Social buzz is pessimistic.`,
        neutral: 'Neutral sentiment. Social media and news sentiment is average compared to other stocks.'
      }
    }

    const category = absValue > 0.5 ? (value > 0 ? 'high' : 'low') : 'neutral'
    return metricExplanations[metric]?.[category] || `Z-score: ${value.toFixed(2)}`
  }

  // Color based on value
  const getColor = () => {
    if (Math.abs(value) < 0.3) return 'text-gray-600'
    return value > 0 ? 'text-green-600' : 'text-red-600'
  }

  return (
    <div className="relative inline-block">
      <button
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        className={`ml-1 inline-flex items-center justify-center w-4 h-4 rounded-full hover:bg-gray-100 transition-colors ${getColor()}`}
      >
        <Info className="w-3 h-3" />
      </button>

      {isVisible && (
        <div className="absolute z-50 left-0 top-6 w-64 bg-white border border-gray-300 rounded-lg shadow-xl p-3 animate-in fade-in slide-in-from-top-1 duration-200">
          {/* Title */}
          <div className="flex items-center gap-2 mb-2">
            <Info className={`w-4 h-4 ${getColor()}`} />
            <span className="text-xs font-semibold text-gray-700 uppercase tracking-wide">
              {metric} Z-Score
            </span>
          </div>

          {/* Value */}
          <div className="text-lg font-bold mb-2 ${getColor()}">
            {value > 0 ? '+' : ''}{value.toFixed(2)} σ
          </div>

          {/* Explanation */}
          <p className="text-xs text-gray-700 leading-relaxed">
            {getExplanation()}
          </p>

          {/* Footer note */}
          <div className="mt-2 pt-2 border-t border-gray-200">
            <p className="text-[10px] text-gray-500 italic">
              Z-scores compare this stock to {metric === 'sentiment' ? '519 tickers' : 'the market universe'}. 
              Values beyond ±1.0 are significant.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
