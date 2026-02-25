/**
 * PortfolioBannerHoldings Component
 * 
 * Row 2 of Portfolio Banner: Holdings cards with ticker, weight, P&L
 * Auto-highlights currently analyzed ticker in chat
 * 
 * Props:
 * - holdings: array of { ticker, companyName, weight, pnl, pnlPercent, isHighlighted }
 * - onTickerClick: function (navigate to single ticker analysis)
 * 
 * Created: January 20, 2026
 */

'use client'

import { TrendingUp, TrendingDown, Sparkles } from 'lucide-react'

export default function PortfolioBannerHoldings({ holdings = [], onTickerClick }) {
  if (holdings.length === 0) {
    return (
      <div className="px-6 py-4 border-b border-gray-200">
        <p className="text-sm text-gray-500 text-center">No holdings found</p>
      </div>
    )
  }

  return (
    <div className="px-6 py-3 border-b border-gray-200 overflow-x-auto">
      <div className="flex gap-2 min-w-max">
        {holdings.map((holding) => {
          const isProfitable = holding.pnlPercent >= 0
          const isSignificantGain = holding.pnlPercent > 5
          const pnlColor = isProfitable ? 'text-green-600' : 'text-red-600'
          const pnlBg = isProfitable ? 'bg-green-50' : 'bg-red-50'

          return (
            <button
              key={holding.ticker}
              onClick={() => onTickerClick && onTickerClick(holding.ticker)}
              className={`
                group relative px-4 py-2.5 rounded-lg border transition-all
                hover:shadow-md hover:scale-105
                ${holding.isHighlighted 
                  ? 'bg-yellow-100 border-yellow-400 shadow-lg scale-105' 
                  : 'bg-white border-gray-200 hover:border-emerald-300'
                }
              `}
            >
              <div className="flex flex-col gap-1">
                {/* Ticker + Sparkles if significant gain */}
                <div className="flex items-center gap-1.5">
                  <span className="text-sm font-bold text-gray-900">
                    {holding.ticker}
                  </span>
                  {isSignificantGain && (
                    <Sparkles size={12} className="text-yellow-500" />
                  )}
                </div>

                {/* Weight % */}
                <div className="text-xs font-medium text-gray-600">
                  {holding.weight.toFixed(1)}% weight
                </div>

                {/* P&L Badge */}
                <div className={`flex items-center gap-1 px-2 py-0.5 rounded ${pnlBg}`}>
                  {isProfitable ? (
                    <TrendingUp size={10} className={pnlColor} />
                  ) : (
                    <TrendingDown size={10} className={pnlColor} />
                  )}
                  <span className={`text-xs font-medium ${pnlColor}`}>
                    {isProfitable ? '+' : ''}{holding.pnlPercent.toFixed(1)}%
                  </span>
                </div>
              </div>

              {/* Highlight indicator */}
              {holding.isHighlighted && (
                <div className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-yellow-500 rounded-full animate-pulse" />
              )}
            </button>
          )
        })}
      </div>
    </div>
  )
}
