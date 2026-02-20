'use client'

import { User, Activity, X, Circle } from 'lucide-react'
import { VitruvyanResponseRenderer } from '../response/VitruvyanResponseRenderer'
import { adaptFinalState } from '../adapters'
import AnalysisHeader from '../layouts/AnalysisHeader'
import PortfolioBanner from '../portfolio/PortfolioBanner'
import { adaptPortfolioBanner, highlightTicker } from '../adapters/portfolioBannerAdapter'
import { Loader2 } from 'lucide-react'
import { ThinkingSteps } from './ThinkingSteps'

const MESSAGE_STYLES = {
  user: "bg-gray-100 border border-gray-200 text-gray-900",
  ai: "bg-emerald-50 border border-emerald-100 text-gray-900",
  processing: "bg-blue-50 border border-blue-200 text-gray-900",
  error: "bg-red-50 border border-red-200 text-gray-900"
}

export function ChatMessage({ 
  message, 
  onFollowUpClick, 
  onTickerClick, 
  onOpenPortfolio,
  isPortfolioOpen,
  portfolioData,
  portfolioLoading,
  portfolioError,
  onClosePortfolio,
  onPortfolioTickerClick,
  currentAnalyzedTicker,
  isLastUserMessage,
  onOrderExecuted, // Trading order callback (Feb 1, 2026)
  onViewPortfolio // Portfolio navigation callback (Feb 4, 2026)
}) {
  const { sender, text, finalState, isComplete, error, detectedTickers, isStreaming, thinkingSteps } = message
  
  const isUser = sender === 'user'
  const isProcessing = !isComplete && !error
  const bubbleClass = error ? MESSAGE_STYLES.error : isProcessing ? MESSAGE_STYLES.processing : MESSAGE_STYLES[sender]
  
  // Adapt portfolio data
  const adaptedPortfolioData = portfolioData 
    ? highlightTicker(adaptPortfolioBanner(portfolioData), currentAnalyzedTicker)
    : null
  
  // Show portfolio in last user message when open
  const showPortfolio = isUser && isLastUserMessage && isPortfolioOpen
  
  // 🎯 Trading props extraction (Feb 1, 2026)
  // Extract ticker, currentPrice, userHolding from finalState
  const ticker = finalState?.tickers?.[0] || null
  const numericalPanel = finalState?.numerical_panel || []
  const tickerData = ticker ? numericalPanel.find(t => t.ticker === ticker) : null
  const currentPrice = tickerData?.current_price || tickerData?.price || 0
  
  // Find user holding in portfolio (if available)
  const userHolding = ticker && adaptedPortfolioData?.holdings 
    ? adaptedPortfolioData.holdings.find(h => h.ticker === ticker)
    : null
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`${showPortfolio ? 'max-w-[95%]' : 'max-w-[85%]'} rounded-2xl p-4 ${bubbleClass} transition-all duration-300`}>
        {/* Avatar with Portfolio Trigger */}
        <div className="flex items-center gap-2 mb-2">
          {isUser ? (
            <button
              onClick={onOpenPortfolio}
              className="group relative p-0.5 rounded-full hover:bg-emerald-100 transition-colors"
              title="Open Portfolio"
            >
              <User size={16} className="text-gray-500 group-hover:text-emerald-600 transition-colors" />
              <span className="absolute -bottom-6 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity text-xs whitespace-nowrap bg-gray-900 text-white px-2 py-1 rounded">
                Portfolio
              </span>
            </button>
          ) : (
            <div className="relative w-4 h-4">
              <Circle size={16} className="text-emerald-600 absolute inset-0" strokeWidth={2} />
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-1 h-1 bg-emerald-600 rounded-full"></div>
              </div>
            </div>
          )}
          <span className="text-xs font-medium text-gray-500">
            {isUser ? 'You' : 'Leonardo'}
          </span>
        </div>
        
        {/* Content */}
        {isUser ? (
          <>
            <p className="text-sm">{text}</p>
            
            {/* Portfolio Banner with "Show Full Portfolio" button */}
            {showPortfolio && (
              <div className="mt-4 pt-4 border-t border-gray-300">
                <PortfolioBanner
                  isOpen={true}
                  onClose={onClosePortfolio}
                  portfolioData={portfolioData}
                  loading={portfolioLoading}
                  error={portfolioError}
                  currentTicker={currentAnalyzedTicker}
                  onTickerClick={onPortfolioTickerClick}
                />
              </div>
            )}
          </>
        ) : finalState ? (
          <div>
            {/* Analysis Header (for ticker analyses) */}
            {finalState.tickers?.length > 0 && (
              <AnalysisHeader 
                tickers={finalState.tickers}
                analysisType={finalState.tickers.length === 1 ? 'single' : 'comparison'}
                onTickerClick={onTickerClick}
              />
            )}
            
            {/* Response */}
            <VitruvyanResponseRenderer 
              response={adaptFinalState(finalState)}
              onFollowUpClick={onFollowUpClick}
              ticker={ticker}
              currentPrice={currentPrice}
              userHolding={userHolding}
              onOrderExecuted={onOrderExecuted}
              onViewPortfolio={onViewPortfolio}
            />
          </div>
        ) : isStreaming || thinkingSteps?.length > 0 ? (
          <div>
            {/* Show thinking steps during streaming */}
            <ThinkingSteps steps={thinkingSteps || []} isStreaming={isStreaming} />
            {!isStreaming && thinkingSteps?.length === 0 && (
              <p className="text-sm text-gray-500 animate-pulse">Analyzing...</p>
            )}
          </div>
        ) : (
          <p className="text-sm">{text}</p>
        )}
      </div>
    </div>
  )
}