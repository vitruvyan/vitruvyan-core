// response/EvidenceSectionRenderer.jsx
'use client'

import { useState } from 'react'
import { MetricCard } from '../cards/CardLibrary'
import FactorRadarChart from '../analytics/charts/FactorRadarChart'
import CandlestickChart from '../analytics/charts/CandlestickChart'
import SignalRadarChart from '../analytics/charts/SignalRadarChart'
import RiskBreakdownChart from '../analytics/charts/RiskBreakdownChart'
import { ExploreAdditionalPerspectives } from '../composites/ExploreAdditionalPerspectives'
import { AllocationWeightsTable } from './AllocationWeightsTable'
import CandidateList from './CandidateList'
import FactorComparisonTable from './FactorComparisonTable'
import ComparisonRadarChart from './ComparisonRadarChart'
import WinnerStrengthsCard from './WinnerStrengthsCard'
import { Shield, TrendingUp, TrendingDown, Minus, AlertTriangle, HelpCircle, Activity, BarChart2, MessageCircle, Target, Radar, PieChart } from 'lucide-react'

export function EvidenceSectionRenderer({ section }) {
  const { content } = section

  switch (content.type) {
    case 'metrics':
    case 'signal-drivers':  // Alias for signal drivers
      return <MetricsRenderer data={content.data} />
    case 'fundamentals':
      return <FundamentalsRenderer data={content.data} />
    case 'risk':
      return <RiskRenderer data={content.data} />
    case 'perspectives':
      return <PerspectivesRenderer data={content.data} />
    case 'table':
      return <TableRenderer data={content.data} />
    case 'text':
      return <TextRenderer data={content.data} />
    case 'radar':
      return <FactorRadarChart factors={content.data.factors} explainability={content.data.explainability} />
    case 'candlestick':
    case 'price':
    case 'chart':  // Alias for chart
      return <CandlestickChart ticker={content.data.ticker} days={content.data.days || 90} explainability={content.data.explainability} />
    case 'allocation-table':
      return <AllocationWeightsTable data={content.data} />
    case 'screening-table':
      return <CandidateList candidates={content.data} onCandidateClick={(ticker) => console.log('Explore candidate:', ticker)} />
    case 'comparison-table':
      return <FactorComparisonTable 
        factorComparison={content.data.factorComparison} 
        winnerTicker={content.data.winnerTicker} 
        loserTicker={content.data.loserTicker} 
      />
    case 'winner-strengths':
      return <WinnerStrengthsCard 
        ticker={content.data.ticker}
        strengths={content.data.strengths}
        keyDifferentiator={content.data.keyDifferentiator}
        keyDelta={content.data.keyDelta}
      />
    case 'comparison-radar':
      return <ComparisonRadarChart tickersData={content.data} />
    default:
      return <div className="text-gray-500 text-sm">Unknown content type: {content.type}</div>
  }
}

// Signal Drivers renderer with VEE tooltips
function MetricsRenderer({ data }) {
  if (!data) return null
  const [activeTooltip, setActiveTooltip] = useState(null)

  const getZScoreBadge = (value) => {
    if (value === null || value === undefined) return { label: '-', color: 'text-gray-400', bg: 'bg-gray-50' }
    if (value > 1.0) return { label: 'Strong', color: 'text-green-600', bg: 'bg-green-50' }
    if (value > 0.5) return { label: 'Positive', color: 'text-emerald-600', bg: 'bg-emerald-50' }
    if (value > -0.5) return { label: 'Neutral', color: 'text-blue-600', bg: 'bg-blue-50' }
    if (value > -1.0) return { label: 'Weak', color: 'text-orange-600', bg: 'bg-orange-50' }
    return { label: 'Very Weak', color: 'text-red-600', bg: 'bg-red-50' }
  }

  // VEE tooltip explanations per UX Constitution
  const tooltips = {
    momentum: {
      title: 'Momentum',
      icon: Activity,
      short: 'Short-term price acceleration',
      technical: 'Measures RSI (14-day), MACD histogram, and recent price velocity. High momentum (>1.0) suggests strong buying pressure; low momentum (<-1.0) indicates selling pressure or consolidation.'
    },
    trend: {
      title: 'Trend',
      icon: TrendingUp,
      short: 'Long-term directional strength',
      technical: 'Evaluates 50/200 SMA relationship, ADX strength, and price position relative to moving averages. Strong trend (>1.0) confirms sustained directional movement.'
    },
    volatility: {
      title: 'Volatility',
      icon: Activity,
      short: 'Price swing intensity',
      technical: 'Measures ATR (Average True Range) and historical volatility. High volatility (>1.0) indicates larger price swings and higher risk; low volatility (<-0.5) suggests stability but potentially limited upside.'
    },
    sentiment: {
      title: 'Sentiment',
      icon: MessageCircle,
      short: 'Market narrative consensus',
      technical: 'Aggregates news sentiment, social mentions, and analyst ratings via FinBERT NLP. Positive sentiment (>0.5) reflects bullish market narrative.'
    },
    composite: {
      title: 'Composite Score',
      icon: Target,
      short: 'Overall signal strength',
      technical: 'Weighted combination of momentum, trend, volatility, sentiment, and fundamentals. The composite score represents the Neural Engine\'s unified assessment.'
    }
  }

  const metrics = [
    { label: 'Momentum', value: data.momentum_z, key: 'momentum' },
    { label: 'Trend', value: data.trend_z, key: 'trend' },
    { label: 'Volatility', value: data.volatility_z, key: 'volatility' },
    { label: 'Sentiment', value: data.sentiment_z, key: 'sentiment' },
    { label: 'Composite', value: data.composite_score, key: 'composite' }
  ].filter(m => m.value !== null && m.value !== undefined)

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      {metrics.map(m => {
        const badge = getZScoreBadge(m.value)
        const tooltip = tooltips[m.key]
        const Icon = tooltip?.icon || HelpCircle
        const isActive = activeTooltip === m.key

        return (
          <div 
            key={m.key} 
            className={`relative bg-white border border-gray-200 rounded-xl p-4 transition-all hover:shadow-md ${badge.bg} cursor-pointer`}
            onMouseEnter={() => setActiveTooltip(m.key)}
            onMouseLeave={() => setActiveTooltip(null)}
          >
            {/* Header with icon */}
            <div className="flex items-center gap-2 mb-2">
              <Icon size={16} className="text-gray-500" />
              <span className="text-xs font-medium text-gray-600 uppercase tracking-wide">{m.label}</span>
            </div>
            
            {/* Value */}
            <div className="text-2xl font-bold mb-1">{m.value?.toFixed(2) || '-'}</div>
            
            {/* Badge */}
            <div className={`text-xs font-semibold ${badge.color}`}>{badge.label}</div>

            {/* VEE Tooltip */}
            {isActive && tooltip && (
              <div className="absolute z-20 left-0 right-0 top-full mt-2 bg-white border border-gray-200 rounded-lg shadow-lg p-3 text-left">
                <div className="text-xs font-medium text-gray-900 mb-1">{tooltip.short}</div>
                <div className="text-xs text-gray-600 leading-relaxed">{tooltip.technical}</div>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

// Fundamentals renderer per Decision Sheet #1 - Visual Health Check Style
function FundamentalsRenderer({ data }) {
  if (!data?.metrics?.length) return null
  const [activeTooltip, setActiveTooltip] = useState(null)

  const getStatusStyle = (status) => {
    if (status === 'solid') return { icon: TrendingUp, color: 'text-green-600', bg: 'bg-green-50', border: 'border-green-200' }
    if (status === 'tension') return { icon: AlertTriangle, color: 'text-orange-600', bg: 'bg-orange-50', border: 'border-orange-200' }
    return { icon: Minus, color: 'text-gray-600', bg: 'bg-gray-50', border: 'border-gray-200' }
  }

  const getMetricBar = (value) => {
    // Convert z-score to percentage (clamped -2 to +2 → 0% to 100%)
    const normalized = Math.max(-2, Math.min(2, value))
    const percent = ((normalized + 2) / 4) * 100
    
    let barColor = 'bg-gray-300'
    if (value > 1.0) barColor = 'bg-green-500'
    else if (value > 0.5) barColor = 'bg-emerald-400'
    else if (value > -0.5) barColor = 'bg-blue-400'
    else if (value > -1.0) barColor = 'bg-orange-400'
    else barColor = 'bg-red-500'
    
    return { percent, barColor }
  }

  // Cluster icons and tooltips
  const clusterMeta = {
    solidity: { 
      icon: Shield, 
      label: 'Solidity',
      tooltip: 'Financial stability: debt levels, cash flow health. Strong solidity = lower default risk.'
    },
    profitability: { 
      icon: Target, 
      label: 'Profitability',
      tooltip: 'Earnings efficiency: margins, return on capital. High profitability = sustainable business model.'
    },
    growth: { 
      icon: TrendingUp, 
      label: 'Growth',
      tooltip: 'Revenue & earnings trajectory. Strong growth = expanding market position.'
    }
  }

  // Group by cluster (UX Constitution epistemic order)
  const clusters = {
    solidity: { ...clusterMeta.solidity, metrics: [] },
    profitability: { ...clusterMeta.profitability, metrics: [] },
    growth: { ...clusterMeta.growth, metrics: [] }
  }

  data.metrics.forEach(m => {
    if (clusters[m.cluster]) {
      clusters[m.cluster].metrics.push(m)
    }
  })

  const statusStyle = getStatusStyle(data.status)
  const StatusIcon = statusStyle.icon

  return (
    <div className="space-y-5">
      {/* Status header card */}
      <div className={`flex items-center gap-3 p-3 rounded-xl ${statusStyle.bg} border ${statusStyle.border}`}>
        <StatusIcon size={20} className={statusStyle.color} />
        <div>
          <div className={`text-sm font-semibold ${statusStyle.color}`}>{data.statusLabel}</div>
          <div className="text-xs text-gray-500">Overall fundamentals assessment</div>
        </div>
      </div>

      {/* Clusters as visual cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {Object.entries(clusters).map(([key, cluster]) => {
          if (cluster.metrics.length === 0) return null
          const ClusterIcon = cluster.icon
          
          return (
            <div 
              key={key} 
              className="bg-white border border-gray-200 rounded-xl p-4 hover:shadow-md transition-shadow relative"
              onMouseEnter={() => setActiveTooltip(key)}
              onMouseLeave={() => setActiveTooltip(null)}
            >
              {/* Cluster header */}
              <div className="flex items-center gap-2 mb-3 pb-2 border-b border-gray-100">
                <ClusterIcon size={16} className="text-gray-500" />
                <span className="text-sm font-semibold text-gray-800">{cluster.label}</span>
              </div>
              
              {/* Metrics as progress bars */}
              <div className="space-y-3">
                {cluster.metrics.map(m => {
                  const bar = getMetricBar(m.value)
                  return (
                    <div key={m.key}>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-gray-600">{m.label}</span>
                        <span className="font-medium text-gray-800">{m.value?.toFixed(2)}</span>
                      </div>
                      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                        <div 
                          className={`h-full ${bar.barColor} rounded-full transition-all`}
                          style={{ width: `${bar.percent}%` }}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>

              {/* Cluster tooltip */}
              {activeTooltip === key && (
                <div className="absolute z-20 left-0 right-0 top-full mt-2 bg-white border border-gray-200 rounded-lg shadow-lg p-3">
                  <div className="text-xs text-gray-600 leading-relaxed">{cluster.tooltip}</div>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

// Risk/VARE renderer
function RiskRenderer({ data }) {
  if (!data) return null

  const getCategoryColor = (category) => {
    const colors = {
      low: 'text-green-600 bg-green-50 border-green-200',
      medium: 'text-yellow-600 bg-yellow-50 border-yellow-200',
      high: 'text-orange-600 bg-orange-50 border-orange-200',
      critical: 'text-red-600 bg-red-50 border-red-200'
    }
    return colors[category?.toLowerCase()] || colors.medium
  }

  // Risk dimension metadata with tooltips
  const riskMeta = {
    market: {
      label: 'Market Risk',
      icon: TrendingDown,
      tooltip: 'Measures how much this stock moves with the overall market (beta). Higher values mean greater sensitivity to market swings — when markets fall, high market-risk stocks typically fall harder.'
    },
    volatility: {
      label: 'Volatility',
      icon: Activity,
      tooltip: 'Reflects daily price swing intensity. High volatility creates both opportunity and danger — prices can move sharply in either direction, requiring tighter risk management.'
    },
    liquidity: {
      label: 'Liquidity',
      icon: BarChart2,
      tooltip: 'Indicates how easily you can enter or exit positions. Low liquidity can mean wider spreads, price slippage, and difficulty selling during market stress.'
    },
    correlation: {
      label: 'Correlation',
      icon: Target,
      tooltip: 'Shows how this stock moves relative to your portfolio. High correlation reduces diversification benefit — if this sector drops, correlated holdings amplify losses.'
    }
  }

  const dimensions = [
    { key: 'market', value: data.dimensions?.market },
    { key: 'volatility', value: data.dimensions?.volatility },
    { key: 'liquidity', value: data.dimensions?.liquidity },
    { key: 'correlation', value: data.dimensions?.correlation }
  ].filter(d => d.value !== undefined && d.value !== null)

  const [activeRiskTooltip, setActiveRiskTooltip] = useState(null)

  const getRiskLevel = (value) => {
    if (value > 70) return { label: 'High', color: 'text-red-600' }
    if (value > 40) return { label: 'Moderate', color: 'text-amber-600' }
    return { label: 'Low', color: 'text-green-600' }
  }

  return (
    <div className="space-y-4">
      {/* Risk category badge */}
      <div className="flex items-center gap-3">
        <Shield size={20} className="text-gray-600" />
        <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm border ${getCategoryColor(data.category)}`}>
          Risk: {data.category || 'Unknown'}
        </div>
        {data.score !== undefined && (
          <span className="text-sm text-gray-500">Score: {data.score.toFixed(1)}/100</span>
        )}
      </div>

      {/* Risk dimensions with tooltips */}
      {dimensions.length > 0 ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          {dimensions.map(d => {
            const meta = riskMeta[d.key]
            const Icon = meta.icon
            const level = getRiskLevel(d.value)
            const isActive = activeRiskTooltip === d.key
            
            return (
              <div 
                key={d.key} 
                className="relative bg-white border border-gray-200 rounded-lg p-3 cursor-pointer hover:shadow-md transition-all"
                onMouseEnter={() => setActiveRiskTooltip(d.key)}
                onMouseLeave={() => setActiveRiskTooltip(null)}
              >
                <div className="flex items-center gap-1.5 mb-1">
                  <Icon size={12} className="text-gray-400" />
                  <span className="text-xs text-gray-500">{meta.label}</span>
                  <HelpCircle size={10} className="text-gray-300" />
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-lg font-semibold">{d.value?.toFixed(0) || '-'}</span>
                  <span className={`text-xs font-medium ${level.color}`}>{level.label}</span>
                </div>
                
                {/* Tooltip */}
                {isActive && (
                  <div className="absolute z-20 left-0 right-0 top-full mt-2 bg-white border border-gray-200 rounded-lg shadow-lg p-3 text-left min-w-[200px]">
                    <div className="text-xs text-gray-700 leading-relaxed">{meta.tooltip}</div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      ) : (
        <div className="text-sm text-gray-500 italic">
          Multi-dimensional risk breakdown not available for this ticker.
        </div>
      )}

      {/* Explanation */}
      {data.explanation && (
        <p className="text-sm text-gray-600 italic">{data.explanation}</p>
      )}
    </div>
  )
}

function TableRenderer({ data }) {
  if (!data?.metrics?.length) return null

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b">
            <th className="text-left py-2 font-medium">Ticker</th>
            <th className="text-right py-2 font-medium">Momentum</th>
            <th className="text-right py-2 font-medium">Trend</th>
            <th className="text-right py-2 font-medium">Volatility</th>
            <th className="text-right py-2 font-medium">Composite</th>
          </tr>
        </thead>
        <tbody>
          {data.metrics.map(row => (
            <tr key={row.ticker} className={`border-b ${row.ticker === data.winner ? 'bg-green-50' : ''}`}>
              <td className="py-2 font-medium">{row.ticker}</td>
              <td className="text-right py-2">{row.momentum_z?.toFixed(2) || '-'}</td>
              <td className="text-right py-2">{row.trend_z?.toFixed(2) || '-'}</td>
              <td className="text-right py-2">{row.volatility_z?.toFixed(2) || '-'}</td>
              <td className="text-right py-2 font-medium">{row.composite_score?.toFixed(2) || '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function TextRenderer({ data }) {
  if (!data) return null
  return <p className="text-sm text-gray-700 leading-relaxed">{data}</p>
}

/**
 * PerspectivesRenderer - Renders ExploreAdditionalPerspectives composite
 * 
 * ARCHITECTURE:
 * - Adapter defines WHAT perspectives (configuration strings)
 * - Renderer provides HOW (actual React components)
 * - Components are REUSABLE across adapters (single, comparison, allocation)
 * 
 * REAL CHARTS (not stubs):
 * - SignalRadarChart: 4-axis radar for momentum/trend/volatility/sentiment
 * - RiskBreakdownChart: Donut chart for VARE 4-dimensional risk
 */
function PerspectivesRenderer({ data }) {
  if (!data?.perspectives?.length) return null
  
  const { perspectives, numerical } = data

  // Map componentType strings to actual chart components
  // These are REAL charts from /analytics/charts, not stubs
  const componentMap = {
    'FactorRadarChart': () => {
      // Use SignalRadarChart for signal drivers (momentum, trend, volatility, sentiment)
      const signals = {
        momentum_z: numerical?.momentum_z,
        trend_z: numerical?.trend_z,
        volatility_z: numerical?.volatility_z,
        sentiment_z: numerical?.sentiment_z
      }
      
      // Guard: need at least one signal
      const hasSignals = Object.values(signals).some(v => v !== null && v !== undefined)
      if (!hasSignals) {
        return <div className="text-sm text-gray-500 text-center py-4">No signal data available</div>
      }
      
      return (
        <SignalRadarChart 
          signals={signals}
          showLegend={true}
          showTooltips={true}
          height={260}
        />
      )
    },
    'RiskBreakdownChart': () => {
      // Use RiskBreakdownChart for VARE 4-dimensional risk analysis
      const hasRiskData = numerical?.vare_risk_score !== undefined
      
      if (!hasRiskData) {
        return <div className="text-sm text-gray-500 text-center py-4">No risk data available</div>
      }
      
      const risk = {
        vare_risk_score: numerical.vare_risk_score,
        vare_risk_category: numerical.vare_risk_category || 'MEDIUM',
        vare_market_risk: numerical.vare_market_risk || 0,
        vare_volatility_risk: numerical.vare_volatility_risk || 0,
        vare_liquidity_risk: numerical.vare_liquidity_risk || 0,
        vare_correlation_risk: numerical.vare_correlation_risk || 0,
        vare_explanation: numerical.vare_explanation
      }
      
      return (
        <RiskBreakdownChart 
          risk={risk}
          explainability={{
            simple: 'Multi-dimensional risk profile based on VARE analysis',
            technical: 'Vitruvyan Adaptive Risk Engine (VARE) evaluates market, volatility, liquidity, and correlation risks'
          }}
        />
      )
    }
  }

  // Build items array with actual components
  const items = perspectives
    .filter(p => componentMap[p.componentType])
    .map(p => ({
      id: p.id,
      label: p.label,
      description: p.description,
      component: componentMap[p.componentType]()
    }))

  // Guard: don't render if no valid perspectives
  if (items.length === 0) return null

  return (
    <ExploreAdditionalPerspectives 
      items={items}
      maxVisible={3}
    />
  )
}

// NOTE: RiskDimensionsChart stub removed - now using real RiskBreakdownChart from /analytics/charts