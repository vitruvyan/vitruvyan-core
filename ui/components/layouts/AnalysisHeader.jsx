/**
 * ANALYSIS HEADER COMPONENT
 * 
 * Common header for all analysis types showing:
 * - Ticker pills (clickable for single ticker analysis)
 * - Blockchain badge (always visible)
 * - Analysis type indicator
 * 
 * Created: Dec 20, 2025
 * Updated: Dec 21, 2025 - Added useTickerNames hook for PostgreSQL fallback
 */

'use client'

import { TrendingUp, BarChart3, Shield } from 'lucide-react'
import { Badge } from '../ui/badge'
import BlockchainLedgerBadge from '../blockchain/BlockchainLedgerBadge'
import useTickerNames from '@/hooks/useTickerNames'

/**
 * Get company full name from ticker data
 */
function getCompanyName(tickerData) {
  // Priority: company_name > name > ticker fallback
  return tickerData?.company_name || tickerData?.name || tickerData?.ticker || tickerData
}

export default function AnalysisHeader({
  tickers = [], // Array of ticker strings OR ticker objects {ticker, company_name}
  tickerData = {}, // Map: ticker -> {ticker, company_name, ...}
  analysisType = 'comparison', // 'comparison' | 'single' | 'portfolio' | 'screening'
  onTickerClick = null, // Callback: (ticker) => void (navigate to single ticker analysis)
  blockchainTxHash = null,
  blockchainBatchId = null,
  blockchainNetwork = 'nile',
  className = ''
}) {
  
  // Normalize tickers to array of strings
  const tickerStrings = tickers.map(t => typeof t === 'string' ? t : t.ticker)
  
  // 🎯 Fetch company names from PostgreSQL if not provided (Dec 21, 2025)
  const { tickerNames: pgTickerNames, loading } = useTickerNames(tickerStrings)
  
  // Merge tickerData with PostgreSQL data (tickerData priority)
  const enhancedTickerData = {}
  tickerStrings.forEach(ticker => {
    enhancedTickerData[ticker] = {
      ticker,
      company_name: tickerData[ticker]?.company_name || pgTickerNames[ticker] || ticker
    }
  })
  
  // Analysis type labels
  const analysisLabels = {
    comparison: 'Comparing',
    single: 'Analyzing',
    portfolio: 'Portfolio Analysis',
    screening: 'Screening'
  }

  return (
    <div className={`flex flex-col md:flex-row md:items-center md:justify-between gap-4 p-4 bg-gray-50 border-b border-gray-200 ${className}`}>
      {/* Left: Ticker Pills */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-gray-600" />
          <span className="text-sm font-medium text-gray-700">
            {analysisLabels[analysisType] || 'Analyzing'}:
          </span>
        </div>
        
        <div className="flex items-center gap-2 flex-wrap">
          {tickerStrings.map((ticker, index) => {
            const data = enhancedTickerData[ticker]
            const companyName = getCompanyName(data)
            // Pills are always clickable if onTickerClick is provided
            const isClickable = onTickerClick !== null
            
            return (
              <div key={ticker} className="flex items-center gap-2">
                <button
                  onClick={() => isClickable && onTickerClick(ticker)}
                  disabled={!isClickable}
                  className={`
                    flex items-center gap-2 px-4 py-2 rounded-lg border 
                    bg-gray-900 text-white text-sm font-medium
                    transition-all duration-200
                    ${isClickable ? 'hover:bg-gray-700 cursor-pointer hover:shadow-lg hover:scale-105 active:scale-95' : 'cursor-default'}
                  `}
                  title={isClickable ? `Click to analyze ${ticker} individually` : companyName}
                >
                  <span className="font-bold">{ticker}</span>
                  {companyName && companyName !== ticker && (
                    <>
                      <span className="text-gray-400">•</span>
                      <span className="text-gray-300 text-xs max-w-[200px] truncate">
                        {companyName}
                      </span>
                    </>
                  )}
                </button>
                {index < tickerStrings.length - 1 && (
                  <span className="text-gray-400 text-xs"></span>
                )}
              </div>
            )
          })}
        </div>
        
        {tickerStrings.length > 1 && (
          <Badge variant="outline" className="text-xs">
            {tickerStrings.length} tickers
          </Badge>
        )}
      </div>

      {/* Right: Blockchain Badge (always visible) */}
      <div className="flex items-center gap-3">
        <BlockchainLedgerBadge 
          txHash={blockchainTxHash}
          batchId={blockchainBatchId}
          network={blockchainNetwork}
          variant="compact"
        />
      </div>
    </div>
  )
}
