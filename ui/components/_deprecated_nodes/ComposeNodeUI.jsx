/**
 * COMPOSE NODE UI - MULTI-CONVERSATION ROUTER
 * 
 * ⚠️ UPDATED (Dec 1, 2025 - Multi-Conversation UX):
 * Now acts as intelligent router based on backend conversation_type.
 * Backend is single source of truth for conversation classification.
 * 
 * Routes:
 * - 'screening' → ScreeningNodeUI (2-4 tickers ranking)
 * - 'portfolio' → PortfolioNodeUI (5+ tickers portfolio analysis)
 * - 'allocation' → AllocationUI (investment distribution)
 * - 'comparison' → ComparisonNodeUI (side-by-side comparison)
 * - 'single'/'default' → SingleTickerUI (existing VEE display logic)
 * 
 * Backend Node: compose_node.py → detect_conversation_type()
 * State Keys: state.conversation_type, state.screening_data, state.portfolio_data, etc.
 * 
 * Props:
 * - conversationType?: string - Backend-detected conversation type (default: 'single')
 * - screeningData?: object - Ranking data for screening mode
 * - portfolioData?: object - Portfolio holdings and metrics
 * - allocationData?: object - Investment weights and rationale
 * - comparisonMatrix?: array - Side-by-side comparison data
 * - narrative: string - Main conversational explanation
 * - veeExplanations?: Record<string, VEELevels> - Multi-level VEE
 * - explainability?: object - Detailed explainability data
 * - numericalPanel?: Array - Composite scores and sentiment data
 * - showAccordions?: boolean - Show multi-level VEE accordions (default: false)
 * - className?: string - Optional Tailwind classes
 */

'use client'

import { useState, useMemo } from 'react'
import { FileText, ChevronDown, ChevronUp, TrendingUp, AlertCircle, ExternalLink } from 'lucide-react'
import { hasVEEData } from '@/lib/utils/nodeGuards'

// Import specialized UI components
import ScreeningNodeUI from './ScreeningNodeUI'
import AllocationUI from './AllocationUI'
import ComparisonNodeUI from './ComparisonNodeUI'
import PortfolioNodeUI from './PortfolioNodeUI'
import SingleTickerNode from './SingleTickerNode'
import FundamentalsPanel from '../analytics/panels/FundamentalsPanel'
import { BaseCard } from '../cards/CardLibrary'

// Helper function to render text with **bold** as <strong>
function renderTextWithBold(text) {
  if (!text) return text
  
  // Split by ** and alternate between normal and bold
  const parts = text.split('**')
  return parts.map((part, index) => {
    // Odd indices are bold (between ** markers)
    if (index % 2 === 1) {
      return <strong key={index}>{part}</strong>
    }
    return part
  })
}

export default function ComposeNodeUI({ 
  conversationType = 'single',
  screeningData,
  portfolioData,
  allocationData,
  comparisonMatrix,
  narrative, 
  veeExplanations, 
  explainability, 
  numericalPanel,
  showAccordions = false,
  className = '' 
}) {
  // 🔵 PHASE 1: Force comparison mode for 2+ tickers (Dec 19, 2025)
  // Override conversationType prop if multiple tickers detected
  const numTickers = numericalPanel?.length || (veeExplanations ? Object.keys(veeExplanations).length : 0)
  const isMultiTicker = numTickers >= 2
  const hasSpecializedData = screeningData || portfolioData || allocationData
  
  let effectiveConversationType = conversationType
  
  // Override to 'comparison' if:
  // - 2+ tickers detected
  // - No specialized data (screening/portfolio/allocation)
  if (isMultiTicker && !hasSpecializedData) {
    effectiveConversationType = 'comparison'
    // [DEV] log removed
  }
  
  // [DEV] log removed

  // 🎯 ROUTER: Delegate to specialized UI based on conversation_type
  switch(effectiveConversationType) {
    case 'screening':
      return (
        <ScreeningNodeUI 
          screeningData={screeningData}
          narrative={narrative}
          veeExplanations={veeExplanations}
          explainability={explainability}
          numericalPanel={numericalPanel}
          className={className}
        />
      )
    
    case 'portfolio':
      return (
        <PortfolioNodeUI 
          portfolioData={portfolioData}
          narrative={narrative}
          veeExplanations={veeExplanations}
          explainability={explainability}
          numericalPanel={numericalPanel}
          className={className}
        />
      )
    
    case 'allocation':
      return (
        <AllocationUI 
          allocationData={allocationData}
          narrative={narrative}
          veeExplanations={veeExplanations}
          explainability={explainability}
          numericalPanel={numericalPanel}
          className={className}
        />
      )
    
    case 'comparison':
      return (
        <ComparisonNodeUI 
          comparisonMatrix={comparisonMatrix}
          narrative={narrative}
          veeExplanations={veeExplanations}
          explainability={explainability}
          numericalPanel={numericalPanel}
          className={className}
        />
      )
    
    case 'single':
      // ⚠️ DELEGATION TO SingleTickerNode (Dec 19, 2025 - Step 2/5)
      // Inline logic below is FALLBACK only (will be removed in Step 3)
      return (
        <SingleTickerNode
          finalState={{
            narrative,
            vee_explanations: veeExplanations,
            explainability,
            numerical_panel: numericalPanel,
            tickers: explainability?.detailed?.ranking?.stocks?.map(s => s.ticker) || [],
            intent: explainability?.detailed?.intent || 'unknown',
            final_verdict: explainability?.detailed?.final_verdict || null,
            gauge: explainability?.detailed?.gauge || null
          }}
          activeHorizon="short"
          onHorizonChange={() => {}}
          horizonData={{}}
          isLoadingHorizons={false}
        />
      )
    
    default:
      // 🎨 FALLBACK: Inline logic for backward compatibility (temporary)
      break
  }

  // ========================================
  // 🎨 SINGLE TICKER UI (Existing Logic - Unchanged)
  // ========================================

  const [expandedTicker, setExpandedTicker] = useState(null)
  const [showTechnical, setShowTechnical] = useState(false)

  // Guard: Don't render if no content at all
  if (!narrative && !veeExplanations && !numericalPanel) {
    return null
  }

  // ✅ STABLE NARRATIVE: Backend provides complete data (VEEEngine + ConversationalLLM)
  // No useEffect, no API calls, no loops - pure presentational component
  const displayNarrative = useMemo(() => {
    // Priority 1: Use backend narrative
    if (narrative && narrative.trim()) {
      // [DEV] console.log("[ComposeNodeUI] ✅ Using backend narrative")
      return narrative
    }
    
    // Priority 2: Use veeExplanations.conversational
    const firstTicker = veeExplanations ? Object.keys(veeExplanations)[0] : null
    if (firstTicker && veeExplanations[firstTicker]?.conversational) {
      // [DEV] console.log("[ComposeNodeUI] ✅ Using veeExplanations.conversational:", firstTicker)
      return veeExplanations[firstTicker].conversational
    }
    
    // Priority 3: Fallback message (backend should always provide narrative)
    console.warn("[ComposeNodeUI] ⚠️ No narrative available from backend")
    return null
  }, [narrative, veeExplanations])

  // Note: isMultiTicker, numTickers already declared in override logic above (line ~76)
  // Detect portfolio context
  const isPortfolio = explainability?.detailed?.portfolio_metrics !== undefined
  
  // Helper: Parse markdown-style links in text
  const renderWithLinks = (text) => {
    if (!text || typeof text !== 'string') return text
    
    const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/g
    const parts = []
    let lastIndex = 0
    let match
    
    while ((match = linkRegex.exec(text)) !== null) {
      if (match.index > lastIndex) {
        parts.push(text.substring(lastIndex, match.index))
      }
      parts.push(
        <a 
          key={match.index} 
          href={match[2]} 
          className="text-blue-600 hover:text-blue-800 underline font-medium"
          onClick={(e) => {
            if (match[2].startsWith('#')) {
              e.preventDefault()
              document.querySelector(match[2])?.scrollIntoView({ behavior: 'smooth' })
            }
          }}
        >
          {match[1]}
        </a>
      )
      lastIndex = linkRegex.lastIndex
    }
    
    if (lastIndex < text.length) {
      parts.push(text.substring(lastIndex))
    }
    
    return parts.length > 0 ? parts : text
  }

  // Parse markdown-style narrative sections
  const renderNarrative = (text) => {
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
  const mainResponse = veeExplanations ? 
    Object.values(veeExplanations)[0]?.summary || displayNarrative : 
    displayNarrative

  return (
    <div className={`space-y-4 ${className}`}>

      {/* Main Response - Summary level (conversational) */}
      {mainResponse && (
        <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-4 rounded-lg border border-blue-100">
          <div className="text-sm text-gray-700 leading-relaxed">
            {renderNarrative(mainResponse)}
          </div>
        </div>
      )}

      {/* Removed duplicate Fundamentals Panel - now only in Market Intelligence after Neural Engine */}

      {/* Portfolio-Specific Metrics (if available) */}
      {isPortfolio && explainability?.detailed?.portfolio_metrics && (
        <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
          <div className="flex items-center gap-2 mb-3">
            <AlertCircle size={16} className="text-purple-600" />
            <span className="text-sm font-semibold text-purple-900">Portfolio Insights</span>
          </div>
          <div className="grid grid-cols-2 gap-3 text-sm">
            {explainability.detailed.portfolio_metrics.total_value && (
              <div>
                <span className="text-gray-600">Total Value:</span>
                <strong className="ml-2 text-gray-900">
                  ${explainability.detailed.portfolio_metrics.total_value.toLocaleString()}
                </strong>
              </div>
            )}
            {explainability.detailed.portfolio_metrics.diversification_score && (
              <div>
                <span className="text-gray-600">Diversification:</span>
                <strong className="ml-2 text-gray-900">
                  {(explainability.detailed.portfolio_metrics.diversification_score * 100).toFixed(0)}%
                </strong>
              </div>
            )}
          </div>
        </div>
      )}

      {/* VEE Multi-Level Explanations - Market Intelligence Section */}
      {showAccordions && veeExplanations && Object.keys(veeExplanations).length > 0 && (
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
                {Object.entries(veeExplanations).map(([ticker, vee]) => (
                  <div key={ticker} className="space-y-2">
                    {/* Ticker Title with Logo */}
                    <div className="flex items-center gap-2 mb-2">
                      <img 
                        src={`https://logo.clearbit.com/${ticker.toLowerCase()}.com`}
                        alt={`${ticker} logo`}
                        className="w-6 h-6 rounded"
                        onError={(e) => {
                          e.target.onerror = null
                          e.target.src = `https://storage.googleapis.com/iex/api/logos/${ticker}.png`
                        }}
                      />
                      <span className="font-bold text-gray-900">{ticker}</span>
                    </div>

                    {/* Detailed Accordion - PROFESSIONAL FORMAT (Level 2: Analisi Operativa) */}
                    {vee.detailed && (
                      <details className="border border-gray-200 rounded-lg overflow-hidden bg-white">
                        <summary className="cursor-pointer p-3 bg-green-50 hover:bg-green-100 font-medium text-sm text-gray-900">
                          📖 Complete Analysis
                        </summary>
                        <div className="p-4 space-y-4">
                          {/* Parse structured data from detailed text */}
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
                                  <BaseCard variant="default" padding="lg" className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                                    {renderTextWithBold(detailedText)}
                                  </BaseCard>
                                </div>
                              </div>
                            )
                          })()}
                        </div>
                      </details>
                    )}

                    {/* Technical Accordion (Level 3: Approfondimento Tecnico) */}
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

                    {/* 📊 Fundamentals Panel (NEW: Dec 7, 2025) - After Neural Engine */}
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
                ))}
              </div>
            )}
          </div>
        </div>
      )}

    </div>
  )
}
