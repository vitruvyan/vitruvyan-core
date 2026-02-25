/**
 * ALLOCATION UI - Investment Distribution
 * 
 * Purpose: Display investment weights and rationale for portfolio allocation.
 * Backend provides allocation_data with weights, tickers, and rationale.
 * 
 * Props:
 * - allocationData: {tickers, weights, rationale, mode} - Backend allocation data
 * - narrative: string - VEE conversational explanation
 * - veeExplanations: object - Multi-level VEE (optional)
 * - numericalPanel: array - Composite scores
 * - className: string
 */

'use client'

import { PieChart, DollarSign, AlertCircle } from 'lucide-react'
import { PieChart as RechartsPie, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts'
import VEEAccordions from '../explainability/vee/VEEAccordions'
import { BaseCard } from '../cards/CardLibrary'
import { DarkTooltip, VARETooltip } from '../explainability/tooltips/TooltipLibrary'
import { Shield, AlertTriangle } from 'lucide-react'

export default function AllocationUI({ 
  allocationData, 
  narrative, 
  veeExplanations,
  explainability,
  numericalPanel,
  className = '' 
}) {
  // Guard: Require allocation_data
  if (!allocationData || !allocationData.weights) {
    return (
      <div className={`bg-yellow-50 border border-yellow-200 p-4 rounded-lg ${className}`}>
        <p className="text-sm text-yellow-800">⚠️ No allocation data available</p>
      </div>
    )
  }

  const { tickers, weights, rationale, mode } = allocationData

  // Prepare data for pie chart
  const chartData = tickers.map((ticker) => ({
    name: ticker,
    value: weights[ticker] * 100 // Convert to percentage
  }))

  // Color palette (semantic semitransparent @ 85% for charts)
  const COLORS = [
    'rgba(59,130,246,0.85)',   // info (blue)
    'rgba(34,197,94,0.85)',    // success (green)
    'rgba(245,158,11,0.85)',   // warning (amber)
    'rgba(239,68,68,0.85)',    // danger (red)
    'rgba(168,85,247,0.85)',   // premium (purple)
    'rgba(236,72,153,0.85)',   // pink
    'rgba(6,182,212,0.85)'     // cyan
  ]

  // Custom label for pie chart
  const renderLabel = (entry) => {
    return `${entry.name} ${entry.value.toFixed(1)}%`
  }

  return (
    <div className={`space-y-4 ${className}`}>

      {/* VEE Narrative */}
      {narrative && (
        <div className="bg-[rgba(59,130,246,0.08)] p-4 rounded-lg border border-[rgba(59,130,246,0.20)]">
          <div className="text-sm text-gray-700 leading-relaxed">
            {narrative.split('\n').map((line, i) => (
              line.trim() ? <p key={i} className="mb-2">{line}</p> : <br key={i} />
            ))}
          </div>
        </div>
      )}

      {/* Allocation Mode Badge */}
      <div className="flex items-center gap-2">
        <span className="inline-flex items-center gap-1.5 text-xs px-3 py-1 rounded-full bg-[rgba(168,85,247,0.08)] text-[rgba(147,51,234,1)] border border-[rgba(168,85,247,0.20)] font-semibold uppercase">
          {mode.replace('_', ' ')}
          <DarkTooltip 
            content={mode === 'equal_weight' 
              ? "Equal Weight: Distributes capital evenly across all tickers (1/N strategy). Simple diversification approach without optimization."
              : mode === 'composite_balanced'
              ? "Composite Balanced: Weights based on composite z-scores with risk adjustment. Balances performance signals with volatility control."
              : mode === 'momentum_weighted'
              ? "Momentum Weighted: Allocates more capital to high-momentum tickers. Trend-following strategy favoring relative strength."
              : "Custom allocation strategy based on selected optimization criteria."}
            asSpan
          />
        </span>
        {mode === 'equal_weight' && (
          <span className="text-xs text-gray-500">
            (Optimization engine coming soon)
          </span>
        )}
      </div>

      {/* Allocation Pie Chart + Table */}
      <div className="grid md:grid-cols-2 gap-4">
        
        {/* Pie Chart */}
        <BaseCard variant="elevated" padding="lg">
          <div className="flex items-center gap-2 mb-4">
            <PieChart size={18} className="text-blue-600" />
            <h3 className="font-semibold text-gray-900">Allocation Distribution</h3>
          </div>
          
          <ResponsiveContainer width="100%" height={250}>
            <RechartsPie>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={renderLabel}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => `${value.toFixed(1)}%`} />
            </RechartsPie>
          </ResponsiveContainer>
        </BaseCard>

        {/* Weights Table */}
        <BaseCard variant="elevated" padding="none" className="overflow-hidden">
          <div className="bg-[rgba(59,130,246,0.05)] px-4 py-3 border-b border-gray-200">
            <h3 className="font-semibold text-gray-900 flex items-center gap-2">
              <DollarSign size={18} className="text-blue-600" />
              Investment Weights
              <DarkTooltip 
                content="Investment weight represents the percentage of capital allocated to each ticker based on the selected allocation strategy. Higher weights indicate stronger conviction or better risk-adjusted expected returns."
                asSpan
              />
            </h3>
          </div>

          <div className="divide-y divide-gray-100">
            {tickers.map((ticker, index) => {
              const weight = weights[ticker]
              const panelData = numericalPanel?.find(p => p.ticker === ticker)
              const composite = panelData?.composite_score || 0

              return (
                <div key={ticker} className="px-4 py-3 hover:bg-gray-50 transition-colors">
                  <div className="flex items-center justify-between">
                    {/* Ticker */}
                    <div className="flex items-center gap-2">
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

                    {/* Weight */}
                    <div className="text-right">
                      <div className="text-lg font-bold" style={{ color: COLORS[index % COLORS.length] }}>
                        {(weight * 100).toFixed(1)}%
                      </div>
                      {composite !== 0 && (
                        <div className="text-xs text-gray-500">
                          Score: {composite.toFixed(2)}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Weight Bar */}
                  <div className="mt-2 h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div 
                      className="h-full rounded-full transition-all"
                      style={{ 
                        width: `${weight * 100}%`,
                        backgroundColor: COLORS[index % COLORS.length]
                      }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </BaseCard>
      </div>

      {/* 🎯 Portfolio-Level VARE Risk Aggregation (Dec 24, 2025) */}
      {numericalPanel && numericalPanel.some(t => t.vare_risk_score) && (
        <div className="bg-gradient-to-br from-orange-50 to-red-50 border border-orange-200 rounded-lg p-6">
          <div className="flex items-center gap-2 mb-4">
            <Shield className="w-5 h-5 text-orange-600" />
            <h3 className="text-lg font-bold text-gray-900">Portfolio Risk Profile (VARE®)</h3>
          </div>
          
          {(() => {
            // Calculate weighted average VARE score
            const totalWeight = tickers.reduce((sum, t) => sum + weights[t], 0)
            const weightedRiskScore = tickers.reduce((sum, ticker) => {
              const tickerData = numericalPanel.find(t => t.ticker === ticker)
              const riskScore = tickerData?.vare_risk_score || 50
              return sum + (riskScore * (weights[ticker] / totalWeight))
            }, 0)
            
            const getRiskColor = (score) => {
              if (score >= 70) return { bg: 'bg-red-100', text: 'text-red-700', border: 'border-red-400', label: 'CRITICAL' }
              if (score >= 50) return { bg: 'bg-orange-100', text: 'text-orange-700', border: 'border-orange-400', label: 'HIGH' }
              if (score >= 30) return { bg: 'bg-yellow-100', text: 'text-yellow-700', border: 'border-yellow-400', label: 'MODERATE' }
              return { bg: 'bg-green-100', text: 'text-green-700', border: 'border-green-400', label: 'LOW' }
            }
            
            const riskProfile = getRiskColor(weightedRiskScore)
            
            return (
              <div className="space-y-4">
                {/* Aggregated Risk Score */}
                <div className={`${riskProfile.bg} border-2 ${riskProfile.border} rounded-lg p-4`}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-semibold text-gray-700">Portfolio Risk Score</span>
                    <VARETooltip 
                      riskScore={weightedRiskScore}
                      riskCategory={riskProfile.label}
                      marketRisk={0}
                      volatilityRisk={0}
                      liquidityRisk={0}
                      correlationRisk={0}
                    />
                  </div>
                  <div className="flex items-baseline gap-2">
                    <span className={`text-4xl font-bold ${riskProfile.text}`}>
                      {weightedRiskScore.toFixed(0)}
                    </span>
                    <span className="text-lg text-gray-500">/100</span>
                    <span className={`ml-auto text-sm font-bold ${riskProfile.text} px-3 py-1 rounded-full border ${riskProfile.border}`}>
                      {riskProfile.label}
                    </span>
                  </div>
                </div>
                
                {/* Risk Distribution by Ticker */}
                <div className="space-y-2">
                  <h4 className="text-sm font-semibold text-gray-700">Risk Contribution by Ticker</h4>
                  {tickers.map((ticker) => {
                    const tickerData = numericalPanel.find(t => t.ticker === ticker)
                    const riskScore = tickerData?.vare_risk_score || 50
                    const riskCategory = tickerData?.vare_risk_category || 'UNKNOWN'
                    const weight = weights[ticker]
                    const contribution = (riskScore * weight).toFixed(1)
                    
                    return (
                      <div key={ticker} className="flex items-center justify-between p-3 bg-white rounded-lg border border-gray-200">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-gray-900">{ticker}</span>
                          <span className="text-xs text-gray-500">({(weight * 100).toFixed(1)}%)</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-semibold text-gray-700">
                            {riskScore.toFixed(0)} × {(weight * 100).toFixed(1)}% = {contribution}
                          </span>
                          <span className={`text-xs px-2 py-1 rounded-full font-semibold ${
                            riskCategory === 'CRITICAL' ? 'bg-red-100 text-red-700' :
                            riskCategory === 'HIGH' ? 'bg-orange-100 text-orange-700' :
                            riskCategory === 'MODERATE' ? 'bg-yellow-100 text-yellow-700' :
                            'bg-green-100 text-green-700'
                          }`}>
                            {riskCategory}
                          </span>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            )
          })()}
        </div>
      )}
      
      {/* Rationale */}
      {rationale && (
        <div className="bg-[rgba(59,130,246,0.08)] border border-[rgba(59,130,246,0.20)] p-4 rounded-lg">
          <div className="flex items-start gap-2">
            <AlertCircle size={16} className="text-[rgba(37,99,235,1)]" />
            <div>
              <h4 className="text-sm font-semibold text-[rgba(30,64,175,1)] mb-1">Allocation Rationale</h4>
              <p className="text-sm text-[rgba(30,64,175,1)]">{rationale}</p>
            </div>
          </div>
        </div>
      )}

      {/* Disclaimer */}
      <div className="bg-[rgba(245,158,11,0.08)] border border-[rgba(245,158,11,0.20)] p-3 rounded-lg">
        <p className="text-xs text-[rgba(217,119,6,1)]">
          <strong>⚠️ Disclaimer:</strong> This allocation is for informational purposes only. 
          Always perform your own due diligence and consult a financial advisor before making investment decisions.
        </p>
      </div>

      {/* VEE Multi-Level Accordions (like single ticker) */}
      <VEEAccordions
        veeExplanations={veeExplanations}
        explainability={explainability}
        numericalPanel={numericalPanel}
      />

    </div>
  )
}
