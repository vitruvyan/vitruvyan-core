/**
 * PortfolioBanner Component
 * 
 * Expandable portfolio bubble with 2 states:
 * STATE 1 (Compact): Preview (Total Value, Risk, Top 3 holdings)
 * STATE 2 (Expanded): 2-column layout
 *   - LEFT: Performance chart + 6 mini cards (Total Value, Risk, Holding, P&L, Diversification, Risk Score)
 *   - RIGHT: Preview content preserved
 * 
 * Buttons:
 * - "Show Portfolio" → expands to STATE 2
 * - "Show Full Portfolio" → opens /portfolio page (new tab)
 * 
 * Props:
 * - isOpen: boolean
 * - onClose: function
 * - portfolioData: object
 * - loading: boolean
 * - error: string | null
 * - currentTicker: string | null
 * - onTickerClick: function
 * 
 * Created: January 20, 2026
 * Updated: January 24, 2026 (Gradual expansion UX - Task 24-25 Day 2)
 */

'use client'

import { useEffect, useRef, useState } from 'react'
import PortfolioBannerHeader from './PortfolioBannerHeader'
import PortfolioBannerHoldings from './PortfolioBannerHoldings'
import PortfolioBannerMetrics from './PortfolioBannerMetrics'
import PerformanceChart from '../chat/artifacts/PerformanceChart'
import { adaptPortfolioBanner, highlightTicker } from '../adapters/portfolioBannerAdapter'
import { Loader2, TrendingUp, DollarSign, AlertCircle, PieChart, Shield, ExternalLink } from 'lucide-react'

export default function PortfolioBanner({
  isOpen = false,
  onClose,
  portfolioData,
  loading = false,
  error = null,
  currentTicker = null,
  onTickerClick
}) {
  const [isExpanded, setIsExpanded] = useState(false)
  const bannerRef = useRef(null)

  console.log('[PortfolioBanner] Render:', {
    isOpen,
    loading,
    error,
    hasPortfolioData: !!portfolioData,
    holdingsCount: portfolioData?.holdings?.length || 0
  })

  // Adapt and highlight data
  const adaptedData = portfolioData 
    ? highlightTicker(adaptPortfolioBanner(portfolioData), currentTicker)
    : null

  console.log('[PortfolioBanner] adaptedData:', {
    hasAdaptedData: !!adaptedData,
    holdingsCount: adaptedData?.holdings?.length || 0,
    totalValue: adaptedData?.totalValue || 0
  })

  // Click outside to close
  useEffect(() => {
    if (!isOpen) return

    const handleClickOutside = (e) => {
      if (bannerRef.current && !bannerRef.current.contains(e.target)) {
        onClose()
        setIsExpanded(false)
      }
    }

    // Add listener after a small delay to avoid immediate close
    const timeoutId = setTimeout(() => {
      document.addEventListener('mousedown', handleClickOutside)
    }, 100)

    return () => {
      clearTimeout(timeoutId)
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen, onClose])
  
  // Reset expanded state when banner closes
  useEffect(() => {
    if (!isOpen) {
      setIsExpanded(false)
    }
  }, [isOpen])

  // Don't render if not open
  if (!isOpen) return null

  return (
    <div
      ref={bannerRef}
      className={`w-full bg-blue-50/90 border-b border-blue-200 shadow-lg mb-4 transition-all duration-300 ${
        isExpanded ? 'max-w-7xl' : 'max-w-full'
      }`}
      style={{
        backdropFilter: 'blur(8px)',
        WebkitBackdropFilter: 'blur(8px)'
      }}
    >
      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 size={32} className="text-emerald-600 animate-spin" />
          <span className="ml-3 text-gray-600">Loading portfolio...</span>
        </div>
      )}

      {/* Error State */}
      {error && !loading && (
        <div className="px-6 py-8 border-b border-gray-200">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-sm text-red-700 font-medium">⚠️ Error loading portfolio</p>
            <p className="text-xs text-red-600 mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Empty Portfolio State (Feb 9, 2026 - Fix for empty holdings) */}
      {!loading && !error && adaptedData && adaptedData.holdings.length === 0 && (
        <div className="px-6 py-8">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-center">
            <div className="mb-4">
              <PieChart className="w-12 h-12 text-blue-400 mx-auto" />
            </div>
            <h3 className="text-lg font-semibold text-gray-800 mb-2">
              No Positions Yet
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              Your portfolio is empty. Start trading to see your positions and performance here.
            </p>
            <div className="bg-white border border-blue-100 rounded-lg p-4 text-left">
              <p className="text-xs text-gray-500 mb-2">💰 Available Cash</p>
              <p className="text-2xl font-bold text-emerald-600">
                ${adaptedData.totalValue?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}
              </p>
            </div>
            <button
              onClick={onClose}
              className="mt-4 w-full px-4 py-2 bg-gray-900 hover:bg-black text-white text-sm font-medium rounded-lg transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      )}

      {/* Content - Compact or Expanded (only if holdings exist) */}
      {!loading && !error && adaptedData && adaptedData.holdings.length > 0 && (
        <>
          {!isExpanded ? (
            /* STATE 1: Compact Preview */
            <>
              <PortfolioBannerHeader
                totalValue={adaptedData.totalValue}
                pnlPercent={adaptedData.pnlPercent}
                alertsCount={adaptedData.alertsCount}
                onClose={onClose}
              />
              <PortfolioBannerHoldings
                holdings={adaptedData.holdings}
                onTickerClick={onTickerClick}
              />
              <PortfolioBannerMetrics
                pnlAbsolute={adaptedData.pnlAbsolute}
                pnlPercent={adaptedData.pnlPercent}
                riskScore={adaptedData.riskScore}
                diversificationScore={adaptedData.diversificationScore}
                sectorsCount={adaptedData.sectorsCount}
              />
              
              {/* Show Portfolio Button */}
              <div className="px-6 py-3 border-t border-blue-100">
                <button
                  onClick={() => setIsExpanded(true)}
                  className="w-full bg-gray-900 hover:bg-black text-white font-medium py-2.5 px-4 rounded-lg transition-all duration-200 shadow-sm hover:shadow-md flex items-center justify-center gap-2"
                >
                  <TrendingUp className="w-4 h-4" />
                  <span>Show Portfolio</span>
                </button>
              </div>
            </>
          ) : (
            /* STATE 2: Expanded - Two Column Layout */
            <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 p-6">
              {/* LEFT COLUMN (60%) */}
              <div className="lg:col-span-3 space-y-4">
                {/* Performance Chart */}
                <PerformanceChart 
                  portfolioValue={adaptedData.totalValue}
                  data={null}
                />
                
                {/* 6 Mini Cards (2 rows × 3 cols) */}
                <div className="grid grid-cols-3 gap-3">
                  {/* Card 1: Total Value */}
                  <MiniCard
                    icon={<DollarSign className="w-5 h-5 text-emerald-600" />}
                    label="Total Value"
                    value={`$${adaptedData.totalValue.toLocaleString()}`}
                    subtext={`${adaptedData.pnlPercent >= 0 ? '+' : ''}${adaptedData.pnlPercent.toFixed(2)}% today`}
                    colorClass="bg-gradient-to-br from-emerald-50 to-cyan-50 border-emerald-200"
                  />
                  
                  {/* Card 2: Risk Score */}
                  <MiniCard
                    icon={<AlertCircle className="w-5 h-5 text-blue-600" />}
                    label="Risk Score"
                    value={`${adaptedData.riskScore}/10`}
                    subtext={adaptedData.riskScore < 4 ? 'Conservative' : adaptedData.riskScore < 7 ? 'Moderate' : 'Aggressive'}
                    colorClass="bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200"
                  />
                  
                  {/* Card 3: Top Holding */}
                  <MiniCard
                    icon={<PieChart className="w-5 h-5 text-purple-600" />}
                    label="Top Holding"
                    value={`${adaptedData.holdings[0]?.weight?.toFixed(1) || 0}%`}
                    subtext={adaptedData.holdings[0]?.ticker || 'N/A'}
                    colorClass="bg-gradient-to-br from-purple-50 to-pink-50 border-purple-200"
                  />
                  
                  {/* Card 4: P&L */}
                  <MiniCard
                    icon={<TrendingUp className="w-5 h-5 text-green-600" />}
                    label="P&L"
                    value={`${adaptedData.pnlAbsolute >= 0 ? '+' : ''}$${Math.abs(adaptedData.pnlAbsolute).toLocaleString()}`}
                    subtext={`${adaptedData.pnlPercent >= 0 ? '+' : ''}${adaptedData.pnlPercent.toFixed(2)}%`}
                    colorClass={adaptedData.pnlAbsolute >= 0 ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}
                  />
                  
                  {/* Card 5: Diversification */}
                  <MiniCard
                    icon={<Shield className="w-5 h-5 text-indigo-600" />}
                    label="Diversification"
                    value={`${adaptedData.diversificationScore}/10`}
                    subtext={`${adaptedData.sectorsCount} sectors`}
                    colorClass="bg-gradient-to-br from-indigo-50 to-purple-50 border-indigo-200"
                  />
                  
                  {/* Card 6: Risk Status (duplicate but different color) */}
                  <MiniCard
                    icon={<AlertCircle className="w-5 h-5 text-orange-600" />}
                    label="Risk Status"
                    value={adaptedData.riskScore < 4 ? 'LOW' : adaptedData.riskScore < 7 ? 'MEDIUM' : 'HIGH'}
                    subtext={`${adaptedData.riskScore.toFixed(1)}/10`}
                    colorClass={
                      adaptedData.riskScore < 4 
                        ? 'bg-green-50 border-green-200' 
                        : adaptedData.riskScore < 7 
                        ? 'bg-yellow-50 border-yellow-200' 
                        : 'bg-orange-50 border-orange-200'
                    }
                  />
                </div>
              </div>
              
              {/* RIGHT COLUMN (40%) - Preserved Preview */}
              <div className="lg:col-span-2 space-y-4">
                <div className="bg-white border border-gray-200 rounded-lg p-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Portfolio Overview</h3>
                  
                  <div className="space-y-4">
                    {/* Total Value */}
                    <div>
                      <p className="text-sm text-gray-600">Total Value</p>
                      <p className="text-2xl font-bold text-gray-900">
                        ${adaptedData.totalValue.toLocaleString()}
                      </p>
                      <p className={`text-sm font-medium ${adaptedData.pnlPercent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {adaptedData.pnlPercent >= 0 ? '+' : ''}{adaptedData.pnlPercent.toFixed(2)}% today
                      </p>
                    </div>
                    
                    {/* Risk Score */}
                    <div>
                      <p className="text-sm text-gray-600">Risk Score</p>
                      <p className="text-xl font-bold text-gray-900">
                        {adaptedData.riskScore}/10
                      </p>
                    </div>
                    
                    {/* Top 3 Holdings */}
                    <div>
                      <p className="text-sm text-gray-600 mb-2">Top 3 Holdings</p>
                      <div className="space-y-2">
                        {adaptedData.holdings.slice(0, 3).map((holding, idx) => (
                          <div key={idx} className="flex items-center justify-between text-sm">
                            <span className="font-medium text-gray-900">{holding.ticker}</span>
                            <span className="text-gray-600">{holding.weight?.toFixed(1)}%</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
                
                {/* Close Button */}
                <button
                  onClick={() => {
                    setIsExpanded(false)
                    onClose()
                  }}
                  className="w-full px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm font-medium rounded-lg transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          )}
          
          {/* Show Full Portfolio Button (only in expanded state) */}
          {isExpanded && (
            <div className="px-6 pb-4">
              <a
                href="/portfolio"
                target="_blank"
                rel="noopener noreferrer"
                className="w-full bg-gray-900 hover:bg-black text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 shadow-md hover:shadow-lg flex items-center justify-center gap-2"
              >
                <span>Show Full Portfolio</span>
                <ExternalLink className="w-5 h-5" />
              </a>
            </div>
          )}
        </>
      )}
    </div>
  )
}

/* Mini Card Component for Expanded State */
function MiniCard({ icon, label, value, subtext, colorClass }) {
  return (
    <div className={`${colorClass} border rounded-lg p-3 text-center`}>
      <div className="flex justify-center mb-2">{icon}</div>
      <p className="text-xs text-gray-600 mb-1">{label}</p>
      <p className="text-lg font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-600">{subtext}</p>
    </div>
  )
}
