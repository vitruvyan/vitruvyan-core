/**
 * VARE PANEL - Multi-Dimensional Risk Assessment Display
 * 
 * Purpose: Dedicated panel for VARE (Vitruvyan Adaptive Risk Engine) output
 * Shows 4-dimensional risk analysis with professional UX
 * 
 * Used in: NeuralEngineUI, ComparisonNodeUI, ScreeningNodeUI, AllocationUI
 * 
 * Props:
 * - riskData: object with VARE fields (vare_risk_score, vare_risk_category, 4 dimensions)
 * - compositeOriginal: original composite score (pre-adjustment)
 * - compositeAdjusted: adjusted composite score (post-VARE penalty)
 * - ticker: string (for attribution context)
 * - className?: string
 * 
 * Created: Dec 23, 2025
 */

'use client'

import { Shield, AlertTriangle, TrendingDown, Activity, BarChart3 } from 'lucide-react'
import { MetricCard } from '../../cards/CardLibrary'
import { VARETooltip, VAREBadge, DarkTooltip } from '../../explainability/tooltips/TooltipLibrary'

export default function RiskPanel({ riskData, compositeOriginal, compositeAdjusted, ticker, className = '' }) {
  // Validation: return null if no VARE data
  if (!riskData || !riskData.vare_risk_score || !riskData.vare_risk_category) {
    return null
  }

  const {
    vare_risk_score,
    vare_risk_category,
    vare_confidence,
    market_risk,
    volatility_risk,
    liquidity_risk,
    correlation_risk
  } = riskData

  // Calculate adjustment percentage
  const adjustmentPct = compositeOriginal && compositeAdjusted 
    ? (((compositeAdjusted - compositeOriginal) / compositeOriginal) * 100).toFixed(1)
    : null

  // Color coding by risk category
  const getCategoryStyles = (category) => {
    const styles = {
      'low': {
        bg: 'bg-green-50',
        border: 'border-green-200',
        text: 'text-green-800',
        icon: Shield,
        label: 'Low Risk'
      },
      'medium': {
        bg: 'bg-yellow-50',
        border: 'border-yellow-200',
        text: 'text-yellow-800',
        icon: Activity,
        label: 'Medium Risk'
      },
      'high': {
        bg: 'bg-orange-50',
        border: 'border-orange-200',
        text: 'text-orange-800',
        icon: AlertTriangle,
        label: 'High Risk'
      },
      'critical': {
        bg: 'bg-red-50',
        border: 'border-red-200',
        text: 'text-red-800',
        icon: AlertTriangle,
        label: 'CRITICAL RISK'
      }
    }
    return styles[category] || styles['medium']
  }

  const categoryStyles = getCategoryStyles(vare_risk_category)
  const RiskIcon = categoryStyles.icon

  // Risk dimension color (0-100 scale, higher = more risk)
  const getDimensionColor = (value) => {
    if (value >= 80) return 'text-red-700'
    if (value >= 60) return 'text-orange-700'
    if (value >= 40) return 'text-yellow-700'
    return 'text-green-700'
  }

  return (
    <div className={`border-2 rounded-lg p-4 ${categoryStyles.bg} ${categoryStyles.border} ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <RiskIcon className={`w-5 h-5 ${categoryStyles.text}`} />
          <h3 className={`text-sm font-bold ${categoryStyles.text}`}>
            VARE® Risk Assessment
          </h3>
          <DarkTooltip 
            content="VARE (Vitruvyan Adaptive Risk Engine) provides multi-dimensional systematic risk analysis across market, volatility, liquidity, and correlation dimensions. Risk score 0-100, where higher = more risk."
            asSpan
          />
        </div>
        <VAREBadge 
          riskScore={vare_risk_score} 
          riskCategory={vare_risk_category} 
          size="md"
        />
      </div>

      {/* Main Risk Score */}
      <div className="grid grid-cols-2 gap-3 mb-3">
        <div className={`p-3 rounded-lg border-2 ${categoryStyles.border} bg-white`}>
          <div className="text-xs text-gray-600 mb-1">Risk Score</div>
          <div className={`text-2xl font-bold ${categoryStyles.text}`}>
            {vare_risk_score}/100
          </div>
          <div className="text-[10px] text-gray-500 mt-1">
            {categoryStyles.label}
          </div>
        </div>

        {adjustmentPct && (
          <div className="p-3 rounded-lg border-2 border-gray-200 bg-white">
            <div className="text-xs text-gray-600 mb-1">Composite Adjustment</div>
            <div className={`text-2xl font-bold ${parseFloat(adjustmentPct) < 0 ? 'text-red-700' : 'text-green-700'}`}>
              {adjustmentPct > 0 ? '+' : ''}{adjustmentPct}%
            </div>
            <div className="text-[10px] text-gray-500 mt-1">
              {compositeOriginal?.toFixed(2)} → {compositeAdjusted?.toFixed(2)}
            </div>
          </div>
        )}
      </div>

      {/* 4 Risk Dimensions Grid */}
      <div className="grid grid-cols-2 gap-2 mb-3">
        <MetricCard
          label="Market Risk"
          value={market_risk || 'N/A'}
          color={market_risk >= 60 ? 'red' : market_risk >= 40 ? 'yellow' : 'green'}
          icon={TrendingDown}
          tooltip={
            <DarkTooltip 
              content={`Market Risk (${market_risk}): Beta vs benchmark (SPY). Measures systematic exposure to market movements. High beta = amplified volatility during market swings. Values >70 = high correlation, requires hedging.`}
              asSpan
            />
          }
        />
        
        <MetricCard
          label="Volatility Risk"
          value={volatility_risk || 'N/A'}
          color={volatility_risk >= 60 ? 'red' : volatility_risk >= 40 ? 'yellow' : 'green'}
          icon={Activity}
          tooltip={
            <DarkTooltip 
              content={`Volatility Risk (${volatility_risk}): Intraday price swings measured via ATR (Average True Range). High volatility = unpredictable moves, requires wide stop-losses. Values >80 = extreme volatility (top 20 percentile).`}
              asSpan
            />
          }
        />
        
        <MetricCard
          label="Liquidity Risk"
          value={liquidity_risk || 'N/A'}
          color={liquidity_risk >= 60 ? 'red' : liquidity_risk >= 40 ? 'yellow' : 'green'}
          icon={BarChart3}
          tooltip={
            <DarkTooltip 
              content={`Liquidity Risk (${liquidity_risk}): Volume stability and bid-ask spread analysis. High liquidity risk = execution issues (slippage, gaps). Values >70 = unstable volume, avoid large positions.`}
              asSpan
            />
          }
        />
        
        <MetricCard
          label="Correlation Risk"
          value={correlation_risk || 'N/A'}
          color={correlation_risk >= 60 ? 'red' : correlation_risk >= 40 ? 'yellow' : 'green'}
          icon={Shield}
          tooltip={
            <DarkTooltip 
              content={`Correlation Risk (${correlation_risk}): Systematic dependencies with sector/market baskets. High correlation = moves with crowd (meme stocks, sector rotation). Values >80 = high contagion risk.`}
              asSpan
            />
          }
        />
      </div>

      {/* Confidence Indicator */}
      {vare_confidence && (
        <div className="flex items-center justify-between text-xs text-gray-600 border-t border-gray-300 pt-2">
          <span>Confidence: {(vare_confidence * 100).toFixed(0)}%</span>
          <span className="text-gray-400">Multi-dimensional risk assessment</span>
        </div>
      )}

      {/* Detailed Tooltip Trigger */}
      <div className="mt-3">
        <VARETooltip
          riskScore={vare_risk_score}
          riskCategory={vare_risk_category}
          marketRisk={market_risk}
          volatilityRisk={volatility_risk}
          liquidityRisk={liquidity_risk}
          correlationRisk={correlation_risk}
          compositeOriginal={compositeOriginal}
          compositeAdjusted={compositeAdjusted}
          ticker={ticker}
        />
        <button 
          type="button"
          className="w-full text-xs text-center py-2 rounded border border-gray-300 hover:bg-gray-100 transition-colors"
        >
          📊 View Full Risk Analysis & Strategy Guidance
        </button>
      </div>
    </div>
  )
}
