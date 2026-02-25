"use client"

import { TrendingUp } from "lucide-react"

// Pills display component - READ-ONLY confirmed tickers
export default function TickerPills({ confirmedTickers, onRemoveTicker }) {
  if (confirmedTickers.length === 0) return null

  return (
    <div className="absolute bottom-full left-0 right-0 mb-2 flex flex-wrap gap-2 px-2">
      {confirmedTickers.map((ticker) => (
        <span
          key={ticker}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-vitruvyan-accent text-white rounded-full text-xs font-semibold shadow-md transition-all hover:shadow-lg"
        >
          <TrendingUp size={12} />
          {ticker}
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation()
              onRemoveTicker(ticker)
            }}
            className="ml-0.5 hover:bg-white/20 rounded-full p-0.5 transition-colors"
            aria-label={`Remove ${ticker}`}
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </span>
      ))}
    </div>
  )
}