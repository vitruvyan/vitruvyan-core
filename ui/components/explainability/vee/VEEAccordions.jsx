/**
 * VEE ACCORDIONS - Reusable Multi-Level VEE Display
 * 
 * Extracted from ComposeNodeUI single ticker template.
 * Shows 4 levels of VEE explanations:
 * - Summary (📊)
 * - Technical (🔧)
 * - Detailed Analysis (📖) with metric cards
 * - Contextualized (🎯)
 * 
 * Plus Advanced Details (⚙️) from explainability object.
 * 
 * Usage:
 *   <VEEAccordions 
 *     veeExplanations={finalState.vee_explanations}
 *     explainability={finalState.explainability}
 *     numericalPanel={finalState.numerical_panel}
 *   />
 */

'use client'

import { useState } from 'react'
import { BookOpen, ChevronDown, ChevronUp } from 'lucide-react'

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

export default function VEEAccordions({ 
  veeExplanations, 
  explainability, 
  numericalPanel,
  className = '' 
}) {
  const [expandedTicker, setExpandedTicker] = useState(null)

  // Guard: No VEE data
  if (!veeExplanations || Object.keys(veeExplanations).length === 0) {
    return null
  }

  const tickers = Object.keys(veeExplanations)

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Market Intelligence Header */}
      <div className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
        <BookOpen size={16} className="text-blue-600" />
        <span className="font-semibold">📊 Market Intelligence</span>
        <span className="text-xs text-gray-400 ml-1">Multi-level VEE® Analysis</span>
      </div>

      {/* VEE Accordions per Ticker */}
      {tickers.map((ticker) => {
        const vee = veeExplanations[ticker]
        const isExpanded = expandedTicker === ticker

        return (
          <div key={ticker} className="border border-gray-200 rounded-lg bg-white shadow-sm">
            {/* Ticker Header (collapsible) */}
            <button
              onClick={() => setExpandedTicker(isExpanded ? null : ticker)}
              className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-bold text-sm">
                  {ticker.substring(0, 2)}
                </div>
                <div className="text-left">
                  <div className="font-semibold text-gray-900">{ticker}</div>
                  <div className="text-xs text-gray-500">
                    {vee.summary ? 'VEE Analysis Available' : 'No analysis'}
                  </div>
                </div>
              </div>
              {isExpanded ? (
                <ChevronUp className="w-5 h-5 text-gray-400" />
              ) : (
                <ChevronDown className="w-5 h-5 text-gray-400" />
              )}
            </button>

            {/* VEE Levels (expanded) */}
            {isExpanded && (
              <div className="p-4 pt-0 space-y-3 border-t border-gray-100">
                {/* Summary Accordion */}
                {vee.summary && (
                  <details className="border border-gray-200 rounded-lg overflow-hidden bg-white">
                    <summary className="cursor-pointer p-3 bg-blue-50 hover:bg-blue-100 font-medium text-sm text-gray-900">
                      📊 Summary
                    </summary>
                    <div className="p-3 text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                      {renderTextWithBold(vee.summary)}
                    </div>
                  </details>
                )}

                {/* Technical Accordion */}
                {vee.technical && (
                  <details className="border border-gray-200 rounded-lg overflow-hidden bg-white">
                    <summary className="cursor-pointer p-3 bg-indigo-50 hover:bg-indigo-100 font-medium text-sm text-gray-900">
                      🔧 Technical
                    </summary>
                    <div className="p-3 text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                      {renderTextWithBold(vee.technical)}
                    </div>
                  </details>
                )}

                {/* Detailed Analysis Accordion - WITH METRIC CARDS */}
                {vee.detailed && (
                  <details className="border border-gray-200 rounded-lg overflow-hidden bg-white">
                    <summary className="cursor-pointer p-3 bg-green-50 hover:bg-green-100 font-medium text-sm text-gray-900">
                      📖 Detailed Analysis
                    </summary>
                    <div className="p-4 space-y-4">
                      {(() => {
                        const detailedText = vee.detailed
                        
                        // Extract key metrics using regex
                        const compositeMatch = detailedText.match(/composite[_ ]score[: ]+([\d.]+)/i)
                        const rankMatch = detailedText.match(/rank[: ]+(\d+)\/(\d+)/i)
                        const momentumMatch = detailedText.match(/momentum[: ]+([\d.]+)/i)
                        const trendMatch = detailedText.match(/trend[: ]+([\d.]+)/i)
                        const volatilityMatch = detailedText.match(/volatility[: ]+([\d.]+)/i)
                        const sentimentMatch = detailedText.match(/sentiment[: ]+([\d.-]+)/i)
                        
                        // Get price from numericalPanel
                        const priceData = numericalPanel?.find(p => p.ticker === ticker)
                        const currentPrice = priceData?.current_price
                        
                        return (
                          <div className="space-y-4">
                            {/* Key Metrics Grid */}
                            <div>
                              <h4 className="text-xs font-semibold text-gray-600 uppercase mb-3">Key Metrics</h4>
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
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
                              </div>
                            </div>
                            
                            {/* Price Information */}
                            {currentPrice && (
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
                            )}
                            
                            {/* Full Analysis Text */}
                            <div>
                              <h4 className="text-xs font-semibold text-gray-600 uppercase mb-3">Complete Analysis</h4>
                              <div className="bg-white border border-gray-200 p-4 rounded-lg text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                                {renderTextWithBold(detailedText)}
                              </div>
                            </div>
                          </div>
                        )
                      })()}
                    </div>
                  </details>
                )}

                {/* Contextualized Accordion */}
                {vee.contextualized && (
                  <details className="border border-gray-200 rounded-lg overflow-hidden bg-white">
                    <summary className="cursor-pointer p-3 bg-yellow-50 hover:bg-yellow-100 font-medium text-sm text-gray-900">
                      🎯 Contextualized
                    </summary>
                    <div className="p-3 text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                      {renderTextWithBold(vee.contextualized)}
                    </div>
                  </details>
                )}

                {/* Advanced Details Accordion - Metadata */}
                {explainability?.detailed && (
                  <details className="border border-gray-200 rounded-lg overflow-hidden bg-white">
                    <summary className="cursor-pointer p-3 bg-gray-50 hover:bg-gray-100 font-medium text-sm text-gray-900">
                      ⚙️ Advanced Details
                    </summary>
                    <div className="p-3 text-sm text-gray-700 leading-relaxed space-y-2">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Profile:</span>
                        <span className="font-semibold">{explainability.detailed.profile}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Universe Size:</span>
                        <span className="font-semibold">{explainability.detailed.universe_size}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Top K:</span>
                        <span className="font-semibold">{explainability.detailed.top_k}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">As Of:</span>
                        <span className="font-semibold">{explainability.detailed.asof}</span>
                      </div>
                      {explainability.detailed.notes?.risk_disclaimer && (
                        <div className="mt-3 pt-3 border-t border-gray-200 text-xs italic text-gray-500">
                          ⚠️ {explainability.detailed.notes.risk_disclaimer}
                        </div>
                      )}
                    </div>
                  </details>
                )}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
