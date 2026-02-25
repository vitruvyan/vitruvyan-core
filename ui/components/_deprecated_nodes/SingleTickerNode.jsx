/**
 * SINGLE TICKER NODE - Complete Single Ticker Analysis Page
 * 
 * ⚠️ NEW: Dec 19, 2025 - Architectural Refactoring (Pure Router Pattern)
 * 
 * Moved from: conversation/SingleTickerUI.jsx
 * Purpose: Uniform architecture with other conversation nodes
 * 
 * Architecture:
 * - ComposeNodeUI (router) → delegates to SingleTickerNode (specialized page)
 * - Analogous to: ComparisonNode, ScreeningNode, PortfolioNode, AllocationNode
 * - All conversation UX pages live in components/nodes/ for consistency
 * 
 * Displays full single-ticker analysis with:
 * - VEE conversational narrative (inline rendering, NOT via ComposeNodeUI)
 * - Intent detection card with verdict pill
 * - Market sentiment analysis
 * - Neural Engine ranking table + FundamentalsPanel
 * - Candlestick chart (90-day)
 * - Market Intelligence accordion (deep-dive VEE levels)
 * 
 * Triggered by: conversation_type === "single"
 * 
 * Props:
 * - finalState: Complete backend state with all data
 *   - narrative: string
 *   - vee_explanations: object
 *   - explainability: object
 *   - numerical_panel: array
 *   - tickers: array
 *   - intent: string
 *   - final_verdict: object
 *   - gauge: object
 * - activeHorizon: Currently selected horizon ("short", "mid", "long")
 * - onHorizonChange: Function to change horizon
 * - horizonData: Neural Engine data for all 3 horizons
 * - isLoadingHorizons: Boolean for loading state
 */

'use client'

import { useState, useMemo } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import IntentNodeUI from '@/components/nodes/IntentNodeUI'
import SentimentNodeUI from '@/components/nodes/SentimentNodeUI'
import NeuralEngineUI from '@/components/nodes/NeuralEngineUI'
import CandlestickChart from '@/components/analytics/charts/CandlestickChart'
import { BaseCard } from '@/components/cards/CardLibrary'

// Helper function to render text with **bold** as <strong>
function renderTextWithBold(text) {
  if (!text) return text
  
  const parts = text.split('**')
  return parts.map((part, index) => {
    if (index % 2 === 1) {
      return <strong key={index}>{part}</strong>
    }
    return part
  })
}

export default function SingleTickerNode({
  finalState,
  activeHorizon,
  onHorizonChange,
  horizonData,
  isLoadingHorizons
}) {
  const ticker = finalState.tickers?.[0]
  const [expandedTicker, setExpandedTicker] = useState(null)
  
  if (!ticker) {
    return null
  }

  const hasCandlestickData = finalState.explainability?.detailed?.ranking?.stocks?.[0]

  // VEE Narrative Logic (copied from ComposeNodeUI to avoid infinite loop)
  const displayNarrative = useMemo(() => {
    // Priority 1: Use backend narrative
    if (finalState.narrative && finalState.narrative.trim()) {
      return finalState.narrative
    }
    
    // Priority 2: Use veeExplanations.conversational
    const firstTicker = finalState.vee_explanations ? Object.keys(finalState.vee_explanations)[0] : null
    if (firstTicker && finalState.vee_explanations[firstTicker]?.conversational) {
      return finalState.vee_explanations[firstTicker].conversational
    }
    
    return null
  }, [finalState.narrative, finalState.vee_explanations])

  // Helper: Parse markdown-style narrative sections
  const renderNarrative = (text) => {
    if (!text) return null
    
    const lines = text.split('\n')
    return lines.map((line, index) => {
      // Headers (###)
      if (line.startsWith('###')) {
        return (
          <h3 key={index} className="text-lg font-semibold text-gray-900 mt-4 mb-2">
            {line.replace(/^###\s*/, '')}
          </h3>
        )
      }
      // Bold (**text**)
      if (line.includes('**')) {
        const parts = line.split(/\*\*(.*?)\*\*/)
        return (
          <p key={index} className="text-gray-700 mb-2">
            {parts.map((part, i) => 
              i % 2 === 1 ? <strong key={i}>{part}</strong> : part
            )}
          </p>
        )
      }
      // Lists (- item)
      if (line.startsWith('- ')) {
        return (
          <li key={index} className="text-gray-700 ml-4">
            {line.replace(/^-\s*/, '')}
          </li>
        )
      }
      // Regular paragraph
      if (line.trim()) {
        return (
          <p key={index} className="text-gray-700 mb-2">
            {line}
          </p>
        )
      }
      return <br key={index} />
    })
  }

  // Use summary as main conversational response
  const mainResponse = finalState.vee_explanations ? 
    Object.values(finalState.vee_explanations)[0]?.summary || displayNarrative : 
    displayNarrative

  return (
    <div className="space-y-4">
      {/* VEE Narrative - Main Response (Inline rendering, no ComposeNodeUI to avoid loop) */}
      {mainResponse && (
        <div className="bg-white p-6 rounded-lg">
          <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-4 rounded-lg border border-blue-100">
            <div className="text-sm text-gray-700 leading-relaxed">
              {renderNarrative(mainResponse)}
            </div>
          </div>
        </div>
      )}

      {/* Candlestick Chart */}
      {hasCandlestickData && (
        <div className="bg-slate-50 p-6 rounded-lg">
          <CandlestickChart
            ticker={ticker}
            days={90}
            explainability={finalState.explainability}
          />
        </div>
      )}

      {/* Intent Detection + Verdict Pill */}
      {finalState.intent && finalState.intent !== "unknown" && (
        <div className="bg-white p-6 rounded-lg">
          <IntentNodeUI
            intent={finalState.intent}
            horizon={finalState.horizon}
            route={finalState.route}
            finalVerdict={finalState.final_verdict}
            activeHorizon={activeHorizon}
            onHorizonChange={onHorizonChange}
            horizonData={horizonData}
            isLoadingHorizons={isLoadingHorizons}
          />
        </div>
      )}

      {/* Market Sentiment */}
      {finalState.numerical_panel && finalState.numerical_panel.length > 0 && (
        <div className="bg-slate-50 p-6 rounded-lg">
          <SentimentNodeUI
            numericalPanel={finalState.numerical_panel}
            horizonData={horizonData}
            activeHorizon={activeHorizon}
          />
        </div>
      )}

      {/* Neural Engine Ranking */}
      {finalState.numerical_panel && finalState.numerical_panel.length > 0 && (
        <div className="bg-white p-6 rounded-lg">
          <NeuralEngineUI
            numericalPanel={finalState.numerical_panel}
            finalVerdict={finalState.final_verdict}
            gauge={finalState.gauge}
            horizonData={horizonData}
            activeHorizon={activeHorizon}
            explainability={finalState.explainability}
          />
        </div>
      )}

      {/* VEE Multi-Level Explanations - Market Intelligence Section */}
      {finalState.vee_explanations && Object.keys(finalState.vee_explanations).length > 0 && (
        <div className="space-y-4 mt-6" id="market-intelligence-vee">
          {/* Market Intelligence Accordion (Parent) */}
          <div className="border border-gray-300 rounded-lg overflow-hidden bg-white shadow-sm">
            <button
              onClick={() => setExpandedTicker(expandedTicker === 'market-intelligence' ? null : 'market-intelligence')}
              className="w-full flex items-center justify-between p-4 bg-gradient-to-r from-blue-50 to-indigo-50 hover:from-blue-100 hover:to-indigo-100 transition-colors"
            >
              <div className="text-left">
                <div className="font-semibold text-gray-900">📊 Market Intelligence</div>
                <div className="text-xs text-gray-600">Multi-level VEE® Analysis</div>
              </div>
              {expandedTicker === 'market-intelligence' ? (
                <ChevronUp size={20} className="text-gray-600" />
              ) : (
                <ChevronDown size={20} className="text-gray-600" />
              )}
            </button>

            {/* Expanded: VEE Levels (Children Accordions) */}
            {expandedTicker === 'market-intelligence' && (
              <div className="p-4 space-y-3 bg-gray-50">
                {Object.entries(finalState.vee_explanations).map(([tickerSymbol, vee]) => (
                  <div key={tickerSymbol} className="space-y-2">
                    {/* Ticker Title with Logo */}
                    <div className="flex items-center gap-2 mb-2">
                      <img 
                        src={`https://logo.clearbit.com/${tickerSymbol.toLowerCase()}.com`}
                        alt={`${tickerSymbol} logo`}
                        className="w-6 h-6 rounded"
                        onError={(e) => {
                          e.target.onerror = null
                          e.target.src = `https://storage.googleapis.com/iex/api/logos/${tickerSymbol}.png`
                        }}
                      />
                      <span className="font-bold text-gray-900">{tickerSymbol}</span>
                    </div>

                    {/* Detailed Accordion */}
                    {vee.detailed && (
                      <details className="border border-gray-200 rounded-lg overflow-hidden bg-white">
                        <summary className="cursor-pointer p-3 bg-green-50 hover:bg-green-100 font-medium text-sm text-gray-900">
                          📖 Complete Analysis
                        </summary>
                        <div className="p-4 space-y-4">
                          <div className="space-y-4">
                            {/* Key Metrics Grid */}
                            <div>
                              <h4 className="text-xs font-semibold text-gray-600 uppercase mb-3">Key Metrics</h4>
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                                {(() => {
                                  const detailedText = vee.detailed
                                  const compositeMatch = detailedText.match(/composite[_ ]score[: ]+([\d.]+)/i)
                                  const rankMatch = detailedText.match(/rank[: ]+(\d+)\/(\d+)/i)
                                  const momentumMatch = detailedText.match(/momentum[: ]+([\d.]+)/i)
                                  const trendMatch = detailedText.match(/trend[: ]+([\d.]+)/i)
                                  
                                  return (
                                    <>
                                      {compositeMatch && (
                                        <div className="bg-blue-50 border border-blue-200 p-3 rounded-lg">
                                          <div className="text-xs text-gray-600 mb-1">Composite Score</div>
                                          <div className="text-lg font-bold text-blue-900">{parseFloat(compositeMatch[1]).toFixed(4)}</div>
                                        </div>
                                      )}
                                      {rankMatch && (
                                        <div className="bg-purple-50 border border-purple-200 p-3 rounded-lg">
                                          <div className="text-xs text-gray-600 mb-1">Market Rank</div>
                                          <div className="text-lg font-bold text-purple-900">{rankMatch[1]} / {rankMatch[2]}</div>
                                        </div>
                                      )}
                                      {momentumMatch && (
                                        <div className="bg-green-50 border border-green-200 p-3 rounded-lg">
                                          <div className="text-xs text-gray-600 mb-1">Momentum</div>
                                          <div className="text-lg font-bold text-green-900">{parseFloat(momentumMatch[1]).toFixed(2)}</div>
                                        </div>
                                      )}
                                      {trendMatch && (
                                        <div className="bg-orange-50 border border-orange-200 p-3 rounded-lg">
                                          <div className="text-xs text-gray-600 mb-1">Trend</div>
                                          <div className="text-lg font-bold text-orange-900">{parseFloat(trendMatch[1]).toFixed(2)}</div>
                                        </div>
                                      )}
                                    </>
                                  )
                                })()}
                              </div>
                            </div>
                            
                            {/* Price Information */}
                            {(() => {
                              const priceData = finalState.numerical_panel?.find(p => p.ticker === tickerSymbol)
                              const currentPrice = priceData?.current_price
                              
                              if (!currentPrice) return null
                              
                              return (
                                <div>
                                  <h4 className="text-xs font-semibold text-gray-600 uppercase mb-3">Price Information</h4>
                                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                                    <div className="bg-gray-50 border border-gray-200 p-3 rounded-lg">
                                      <div className="text-xs text-gray-600 mb-1">Current Price</div>
                                      <div className="text-xl font-bold text-gray-900">${currentPrice.toFixed(2)}</div>
                                    </div>
                                    <div className="bg-green-50 border border-green-200 p-3 rounded-lg">
                                      <div className="text-xs text-gray-600 mb-1">Entry Point (Est.)</div>
                                      <div className="text-xl font-bold text-green-900">${(currentPrice * 0.98).toFixed(2)}</div>
                                      <div className="text-xs text-gray-500 mt-1">-2% from current</div>
                                    </div>
                                    <div className="bg-red-50 border border-red-200 p-3 rounded-lg">
                                      <div className="text-xs text-gray-600 mb-1">Stop Loss (Est.)</div>
                                      <div className="text-xl font-bold text-red-900">${(currentPrice * 0.95).toFixed(2)}</div>
                                      <div className="text-xs text-gray-500 mt-1">-5% from current</div>
                                    </div>
                                  </div>
                                  <div className="bg-yellow-50 border border-yellow-200 p-3 rounded-lg mt-3">
                                    <p className="text-xs text-yellow-800">
                                      <strong>⚠️ Disclaimer:</strong> Entry/exit prices are estimates based on technical analysis. Always perform your own due diligence and risk assessment before making trading decisions.
                                    </p>
                                  </div>
                                </div>
                              )
                            })()}
                            
                            {/* Full Analysis Text */}
                            <div>
                              <h4 className="text-xs font-semibold text-gray-600 uppercase mb-3">Complete Analysis</h4>
                              <BaseCard variant="default" padding="lg" className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                                {renderTextWithBold(vee.detailed)}
                              </BaseCard>
                            </div>
                          </div>
                        </div>
                      </details>
                    )}

                    {/* Technical Accordion */}
                    {vee.technical && (
                      <details className="border border-gray-200 rounded-lg overflow-hidden bg-white">
                        <summary className="cursor-pointer p-3 bg-purple-50 hover:bg-purple-100 font-medium text-sm text-gray-900">
                          🔧 Technical
                        </summary>
                        <div className="p-3 text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                          {renderTextWithBold(vee.technical)}
                        </div>
                      </details>
                    )}

                    {/* Contextualized Accordion */}
                    {vee.contextualized && (
                      <details className="border border-gray-200 rounded-lg overflow-hidden bg-white">
                        <summary className="cursor-pointer p-3 bg-yellow-50 hover:bg-yellow-100 font-medium text-sm text-gray-900">
                          🎯 Contextualized
                        </summary>
                        <div className="p-3 text-sm text-gray-700 leading-relaxed">
                          {renderTextWithBold(vee.contextualized)}
                        </div>
                      </details>
                    )}

                    {/* Advanced Details Accordion */}
                    {finalState.explainability?.detailed && (
                      <details className="border border-gray-200 rounded-lg overflow-hidden bg-white">
                        <summary className="cursor-pointer p-3 bg-gray-50 hover:bg-gray-100 font-medium text-sm text-gray-900">
                          ⚙️ Advanced Details
                        </summary>
                        <div className="p-3 text-sm text-gray-700 leading-relaxed space-y-2">
                          <div className="flex justify-between">
                            <span className="text-gray-600">Profile:</span>
                            <span className="font-semibold">{finalState.explainability.detailed.profile}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Universe Size:</span>
                            <span className="font-semibold">{finalState.explainability.detailed.universe_size}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Top K:</span>
                            <span className="font-semibold">{finalState.explainability.detailed.top_k}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">As Of:</span>
                            <span className="font-semibold">{finalState.explainability.detailed.asof}</span>
                          </div>
                          {finalState.explainability.detailed.notes?.risk_disclaimer && (
                            <div className="mt-3 pt-3 border-t border-gray-200 text-xs italic text-gray-500">
                              ⚠️ {finalState.explainability.detailed.notes.risk_disclaimer}
                            </div>
                          )}
                        </div>
                      </details>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
