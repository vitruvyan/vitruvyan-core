/**
 * TICKER RESOLVER UI
 * 
 * Displays extracted tickers from ticker_resolver_node.
 * Fetches company names from PostgreSQL via useTickerNames hook
 * 
 * Backend Node: ticker_resolver_node.py
 * State Keys: state.tickers (array of strings)
 * 
 * Props:
 * - tickers: string[] - Array of ticker symbols from backend
 * - onTickerClick?: (ticker: string) => void - Callback when ticker is clicked (for disambiguation)
 * - isAmbiguous?: boolean - If true, shows clickable pills for user to select
 * - className?: string - Optional Tailwind classes
 */

'use client'

import { TrendingUp, MousePointer } from 'lucide-react'
import useTickerNames from '@/hooks/useTickerNames'

export default function TickerResolverUI({ 
  tickers, 
  onTickerClick, 
  isAmbiguous = false, 
  className = '' 
}) {
  // Fetch company names from PostgreSQL
  const { tickerNames, loading } = useTickerNames(tickers)
  
  // Guard: Don't render if no tickers
  if (!tickers || !Array.isArray(tickers) || tickers.length === 0) {
    return null
  }

  const handleTickerClick = (ticker) => {
    if (isAmbiguous && onTickerClick) {
      onTickerClick(ticker)
    }
  }

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      {/* Label */}
      <div className="flex items-center gap-2 text-sm text-gray-600">
        <TrendingUp size={16} className="text-vitruvyan-accent" />
        <span className="font-medium">
          {isAmbiguous ? 'Select ticker:' : 'Analyzing:'}
        </span>
      </div>

      {/* Ticker Badges with Company Names */}
      <div className="flex flex-wrap gap-2">
        {tickers.map((ticker, index) => (
          <button
            key={`${ticker}-${index}`}
            onClick={() => handleTickerClick(ticker)}
            disabled={!isAmbiguous}
            className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm transition-all
              ${isAmbiguous 
                ? 'bg-orange-500 text-white hover:bg-orange-600 cursor-pointer shadow-sm hover:shadow-md transform hover:scale-105' 
                : 'bg-vitruvyan-accent text-white cursor-default'
              }`}
          >
            <span className="font-semibold">{ticker}</span>
            {tickerNames[ticker] && (
              <span className="font-normal opacity-90">• {tickerNames[ticker]}</span>
            )}
            {isAmbiguous && <MousePointer size={12} className="ml-1" />}
          </button>
        ))}
      </div>

      {/* Count or Hint */}
      {tickers.length > 1 && (
        <span className="text-xs text-gray-500">
          {isAmbiguous 
            ? '👆 Click to analyze' 
            : `(${tickers.length} tickers)`
          }
        </span>
      )}
    </div>
  )
}
