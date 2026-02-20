/**
 * TOOLTIP LIBRARY - Unified Explainability System
 * 
 * Purpose: Centralized tooltip components extracted from production single-ticker UX
 * Supports 3 tooltip styles with consistent VEE-inspired explanations
 * 
 * TOOLTIP STYLES:
 * 1. VEE-STYLE (white bg, border, arrow) - Rich factor explanations (momentum, trend, volatility)
 * 2. DARK-STYLE (gray-900 bg) - Simple metric info (InfoTooltip pattern)
 * 3. COMPOSITE-STYLE (white bg, verdict-specific) - Composite score + percentile + strategy
 * 
 * GLOBAL TOGGLE:
 * - useTooltips() hook provides tooltipsEnabled state (localStorage persistence)
 * - TooltipToggle component for user control (power users can disable)
 * 
 * Design Principles:
 * - Extracted from NeuralEngineUI.jsx (proven, production-tested)
 * - VEE structure: context → interpretation → action
 * - Percentile calculation: ~50 + z * 15 (statistical standard)
 * - Factor-specific intelligence (momentum RSI, trend MA, volatility ATR)
 * 
 * Usage:
 *   import { ZScoreTooltip, CompositeScoreTooltip, FactorDeltaTooltip } from '@/components/tooltips/TooltipLibrary'
 *   import { useTooltips } from '@/contexts/TooltipContext'
 *   
 *   const { tooltipsEnabled } = useTooltips()
 *   {tooltipsEnabled && <ZScoreTooltip factor="momentum" value={-0.86} ticker="MCD" />}
 * 
 * Created: Dec 10, 2025
 * Refactored: Dec 10, 2025 (extracted from NeuralEngineUI.jsx)
 */

'use client'

import { HelpCircle } from 'lucide-react'
import { useTooltips } from '@/contexts/TooltipContext'

// ============================================================
// UTILITIES
// ============================================================

const formatZScore = (z) => {
  if (z === null || z === undefined) return 'N/A'
  return z.toFixed(2)
}

const getPercentile = (z) => {
  return Math.round(50 + z * 15) // Standard statistical mapping
}

// ============================================================
// STYLE 1: VEE-STYLE TOOLTIP (White bg, border, arrow)
// Used for: Factor z-scores (momentum, trend, volatility, sentiment)
// ============================================================

export function VeeTooltip({ children, content }) {
  const { tooltipsEnabled } = useTooltips()
  
  if (!tooltipsEnabled) return children
  
  return (
    <div className="group relative cursor-help">
      {children}
      <div className="absolute hidden group-hover:block bottom-full left-1/2 transform -translate-x-1/2 mb-2 w-80 p-4 bg-white border border-gray-300 rounded-lg shadow-xl z-[999] pointer-events-none">
        {content}
        {/* Arrow */}
        <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-8 border-r-8 border-t-8 border-transparent border-t-white" style={{filter: 'drop-shadow(0 2px 2px rgba(0,0,0,0.1))'}}></div>
      </div>
    </div>
  )
}

// ============================================================
// VEE CHART TOOLTIP (Migrated from vee/VeeTooltip.jsx - Dec 30, 2025)
// Purpose: VEE explainability for chart elements (Recharts compatibility)
// ============================================================

export function VeeChartTooltip({ active, payload, label, simple, technical }) {
  if (!active || !payload || payload.length === 0) return null

  // Ensure technical is a string
  const technicalText = technical
    ? (typeof technical === 'string'
        ? technical
        : typeof technical === 'object'
          ? JSON.stringify(technical)
          : String(technical))
    : ''

  // Parse technical explanation into bullet points (if contains newlines or bullets)
  const technicalPoints = technicalText
    ? technicalText.split(/\n|•|-/).filter(p => p.trim()).slice(0, 2)
    : []

  return (
    <div className="bg-white border border-gray-300 rounded-lg shadow-lg p-3 max-w-xs">
      {/* Label */}
      {label && (
        <p className="text-xs font-semibold text-gray-700 mb-2">
          {label}
        </p>
      )}

      {/* VEE Simple (bold, primary) */}
      {simple && (
        <p className="text-sm font-bold text-gray-900 mb-2">
          {simple}
        </p>
      )}

      {/* VEE Technical (bullet points) */}
      {technicalPoints.length > 0 && (
        <ul className="text-xs text-gray-600 space-y-1">
          {technicalPoints.map((point, idx) => (
            <li key={idx} className="flex items-start gap-1">
              <span className="text-vitruvyan-accent mt-0.5">•</span>
              <span>{point.trim()}</span>
            </li>
          ))}
        </ul>
      )}

      {/* Chart value (if available) */}
      {payload[0]?.value !== undefined && (
        <p className="text-xs text-gray-500 mt-2 pt-2 border-t border-gray-200">
          Value: <span className="font-semibold">{payload[0].value.toFixed(2)}</span>
        </p>
      )}
    </div>
  )
}

// ============================================================
// STYLE 2: DARK-STYLE TOOLTIP (Gray-900 bg, simple)
// Used for: Simple metric info, InfoTooltip pattern
// ============================================================

export function DarkTooltip({ content, className = '', asSpan = false }) {
  const { tooltipsEnabled } = useTooltips()
  
  // Use span when inside button parent (prevents nested button error)
  const TriggerElement = asSpan ? 'span' : 'button'
  
  return (
    <div className="group relative inline-block">
      <TriggerElement
        className={`text-gray-400 hover:text-gray-600 transition-colors ${className}`}
        aria-label="More information"
        type={asSpan ? undefined : "button"}
      >
        <HelpCircle size={14} />
      </TriggerElement>
      
      {tooltipsEnabled && (
        <div className="absolute hidden group-hover:block z-[999] w-64 p-3 bg-gray-900 text-white text-xs rounded-lg shadow-xl bottom-full left-1/2 transform -translate-x-1/2 mb-2 pointer-events-none">
          <div className="leading-relaxed">{content}</div>
          {/* Arrow */}
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 -mt-1">
            <div className="border-8 border-transparent border-t-gray-900"></div>
          </div>
        </div>
      )}
    </div>
  )
}

// ============================================================
// STYLE 3: COMPOSITE-STYLE TOOLTIP (White bg, verdict badges)
// Used for: Composite score explanations with verdict
// ============================================================

export function CompositeTooltip({ children, content }) {
  const { tooltipsEnabled } = useTooltips()
  
  if (!tooltipsEnabled) return children
  
  return (
    <div className="group relative">
      {children}
      <div className="absolute hidden group-hover:block bottom-full right-0 mb-2 w-64 p-3 bg-gray-900 text-white text-xs rounded shadow-lg z-[999] pointer-events-none">
        {content}
        <div className="absolute top-full right-4 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></div>
      </div>
    </div>
  )
}

// ============================================================
// Z-SCORE TOOLTIPS (Extracted from NeuralEngineUI.jsx)
// ============================================================

export function MomentumTooltip({ value, ticker }) {
  const percentile = getPercentile(value)
  const performance = value >= 0.5 ? 'Above average' : value < -0.5 ? 'Below average' : 'Average'
  
  const content = (
    <>
      <strong className="block mb-2 text-sm font-bold text-gray-900">
        Momentum: {performance} performance
      </strong>
      <p className="text-xs text-gray-700 leading-relaxed mb-2">
        {value >= 0.5 
          ? `Momentum z-score ${formatZScore(value)} signals significant price acceleration (~${percentile}th percentile). The stock shows relative strength vs market with buyers in control. This technical signal suggests uptrend continuation in the short term (30 days). Ideal for momentum-based and breakout trading strategies.`
          : value < -0.5
          ? `Momentum z-score ${formatZScore(value)} reveals relative weakness (~${percentile}th percentile). Price is losing strength vs peers, signaling selling pressure. This technical dynamic may precede broader corrections. Caution for long positions, opportunity for contrarian strategies if valuations attractive.`
          : `Momentum z-score ${formatZScore(value)} is neutral (~${percentile}th percentile). Price moves in line with market average, no clear directional signals. Consolidation or indecision phase. Wait for technical or fundamental catalysts before directional positioning.`}
      </p>
      <div className="text-xs text-gray-500 border-t border-gray-200 pt-2">
        Current Z-Score: <span className="font-semibold text-vitruvyan-accent">{formatZScore(value)}</span>
      </div>
    </>
  )
  
  return <VeeTooltip content={content}>{ticker && <span>{ticker}</span>}</VeeTooltip>
}

export function TrendTooltip({ value, ticker }) {
  const percentile = getPercentile(value)
  const performance = value >= 0.5 ? 'Above average' : value < -0.5 ? 'Below average' : 'Average'
  
  const content = (
    <>
      <strong className="block mb-2 text-sm font-bold text-gray-900">
        Trend: {performance} performance
      </strong>
      <p className="text-xs text-gray-700 leading-relaxed mb-2">
        {value >= 0.5 
          ? `Trend z-score ${formatZScore(value)} confirms a consolidated structural uptrend (~${percentile}th percentile). Price stays above key moving averages (SMA 20/50/200), signaling long-term strength. This technical setup favors trend-following and position trading strategies. Trend persistence suggests both technical and fundamental support.`
          : value < -0.5
          ? `Trend z-score ${formatZScore(value)} reveals a structural downtrend (~${percentile}th percentile). Price is under pressure vs long-term moving averages. This technical signal requires caution: avoid aggressive long positions, consider protections (stop-loss, put options). Trend reversal needs significant catalysts.`
          : `Trend z-score ${formatZScore(value)} is neutral (~${percentile}th percentile). Price oscillates around moving averages without clear direction. Range-bound or transition phase. Recommended strategy: wait for directional breakout or focus on other factors (fundamentals, sentiment).`}
      </p>
      <div className="text-xs text-gray-500 border-t border-gray-200 pt-2">
        Current Z-Score: <span className="font-semibold text-vitruvyan-accent">{formatZScore(value)}</span>
      </div>
    </>
  )
  
  return <VeeTooltip content={content}>{ticker && <span>{ticker}</span>}</VeeTooltip>
}

export function VolatilityTooltip({ value, ticker }) {
  const percentile = getPercentile(value)
  const riskLevel = value <= -0.5 ? 'Low' : value <= 0.5 ? 'Moderate' : 'High'
  
  const content = (
    <>
      <strong className="block mb-2 text-sm font-bold text-gray-900">
        Volatility: {riskLevel} risk
      </strong>
      <p className="text-xs text-gray-700 leading-relaxed mb-2">
        {value <= -0.5
          ? `Volatility z-score ${formatZScore(value)} indicates remarkable stability (~${percentile}th percentile for calmness). Price movements are contained and predictable. Low volatility attracts conservative investors, but may signal lack of catalysts. Risk: sudden volatility spikes can occur. Strategy: suitable for core positions, lower stop-loss urgency.`
          : value > 0.5
          ? `Volatility z-score ${formatZScore(value)} signals elevated risk (~${percentile}th percentile). Price swings are amplified vs peers. High volatility = higher potential returns but greater downside. Requires active risk management: tighter stops, position sizing, options hedging. Opportunities for swing traders and tactical plays.`
          : `Volatility z-score ${formatZScore(value)} is average (~${percentile}th percentile). Standard price fluctuation in line with market. Neither excessive calm nor panic. Balanced risk profile suitable for most strategies. Monitor for changes in macro conditions or company-specific news.`}
      </p>
      <div className="text-xs text-gray-500 border-t border-gray-200 pt-2">
        Current Z-Score: <span className="font-semibold text-vitruvyan-accent">{formatZScore(value)}</span>
      </div>
    </>
  )
  
  return <VeeTooltip content={content}>{ticker && <span>{ticker}</span>}</VeeTooltip>
}

export function SentimentTooltip({ value, ticker }) {
  const percentile = getPercentile(value)
  const sentiment = value >= 0.5 ? 'Positive' : value < -0.5 ? 'Negative' : 'Neutral'
  
  const content = (
    <>
      <strong className="block mb-2 text-sm font-bold text-gray-900">
        Sentiment: {sentiment}
      </strong>
      <p className="text-xs text-gray-700 leading-relaxed mb-2">
        {value >= 0.5
          ? `Sentiment z-score ${formatZScore(value)} reflects strong bullish consensus (~${percentile}th percentile). Media, analysts, and social sentiment align positively. This narrative support can fuel price momentum short-term. Caution: excessive optimism may precede profit-taking. Strategy: ride the wave but set trailing stops.`
          : value < -0.5
          ? `Sentiment z-score ${formatZScore(value)} shows bearish narrative dominance (~${percentile}th percentile). Negative news flow and analyst downgrades weigh on perception. Contrarian opportunity if fundamentals strong: capitulation selling may offer entry. Risk: sentiment can worsen before reversal. Wait for technical stabilization.`
          : `Sentiment z-score ${formatZScore(value)} is balanced (~${percentile}th percentile). No extreme optimism or pessimism. Market consensus is neutral, waiting for catalysts. Strategy: focus on other factors (technicals, fundamentals). Sentiment shifts can occur rapidly with earnings or macro news.`}
      </p>
      <div className="text-xs text-gray-500 border-t border-gray-200 pt-2">
        Current Z-Score: <span className="font-semibold text-vitruvyan-accent">{formatZScore(value)}</span>
      </div>
    </>
  )
  
  return <VeeTooltip content={content}>{ticker && <span>{ticker}</span>}</VeeTooltip>
}

// ============================================================
// COMPOSITE SCORE TOOLTIP (Extracted from NeuralEngineUI.jsx verdict badges)
// ============================================================

export function CompositeScoreTooltip({ value, label, ticker }) {
  const formatScore = (score) => {
    if (score === null || score === undefined) return 'N/A'
    return `${(score * 100).toFixed(1)}%`
  }
  
  const getVerdictExplanation = (lbl) => {
    const explanations = {
      'Buy': 'Strong positive momentum across all factors. This stock shows bullish signals and potential upside.',
      'Strong Buy': 'Exceptional strength across all metrics. Very high conviction bullish signal with strong momentum and trend alignment.',
      'Hold': 'Mixed signals or neutral positioning. Current price reflects fair value. Consider waiting for clearer directional signals before acting.',
      'Sell': 'Negative momentum and weak trend. Risk outweighs potential reward. Consider reducing exposure or exiting position.',
      'Strong Sell': 'Severe weakness across multiple factors. High conviction bearish signal. Strong recommendation to exit or avoid this position.'
    }
    return explanations[lbl] || 'Composite score reflects overall technical positioning.'
  }
  
  const content = (
    <>
      <strong className="block mb-1">{label} Signal</strong>
      <p className="leading-relaxed">
        {getVerdictExplanation(label)}
      </p>
      <div className="mt-2 pt-2 border-t border-gray-700">
        <span className="text-gray-400">Composite Score: </span>
        <span className="font-semibold">{formatScore(value)}</span>
      </div>
    </>
  )
  
  return <CompositeTooltip content={content}>{ticker && <span>{ticker}</span>}</CompositeTooltip>
}

// ============================================================
// COMPARISON-SPECIFIC TOOLTIPS
// ============================================================

export function FactorDeltaTooltip({ factor, delta, winner, loser }) {
  const factorNames = {
    momentum_z: 'Momentum',
    trend_z: 'Trend',
    vola_z: 'Volatility',
    sentiment_z: 'Sentiment',
    fundamentals_z: 'Fundamentals'
  }
  
  const factorName = factorNames[factor] || factor
  const absDelta = Math.abs(delta)
  
  const interpretation = absDelta > 1.0 ? 'significantly stronger' : 
                        absDelta > 0.5 ? 'moderately better' : 
                        'slightly ahead'
  
  const content = `${factorName} difference: ${formatZScore(delta)}. ${winner} has ${interpretation} ${factorName.toLowerCase()} than ${loser}. Gap represents ${absDelta > 1.0 ? 'strong' : 'moderate'} competitive advantage on this factor.`
  
  return <DarkTooltip content={content} />
}

export function RankingTooltip({ ticker, rank, totalTickers, compositeScore }) {
  const percentile = ((totalTickers - rank + 1) / totalTickers * 100).toFixed(0)
  
  const content = `${ticker} ranks #${rank} of ${totalTickers} (top ${percentile}%). Composite score ${formatZScore(compositeScore)} reflects ${rank === 1 ? 'winner' : rank <= totalTickers / 2 ? 'above average' : 'below average'} overall performance across all factors.`
  
  return <DarkTooltip content={content} />
}

export function DispersionTooltip({ range, rangePct }) {
  const interpretation = rangePct > 40 ? 
    'Significant performance gap. Clear winner/loser separation.' :
    rangePct > 20 ?
    'Moderate variance. Some differences exist but overlap on factors.' :
    'Low variance. Similar performance patterns across tickers.'
  
  const content = `Score dispersion: ${formatZScore(range)} (${rangePct.toFixed(1)}%). ${interpretation} ${rangePct > 40 ? 'Suitable for pair trading or selective allocation.' : 'Consider broader diversification.'}`
  
  return <DarkTooltip content={content} />
}

// ============================================================
// FUNDAMENTALS TOOLTIP (Simple dark-style)
// ============================================================

export function FundamentalsTooltip({ metric, value, ticker }) {
  const metricNames = {
    revenue_growth_yoy_z: 'Revenue Growth YoY',
    eps_growth_yoy_z: 'EPS Growth YoY',
    net_margin_z: 'Net Margin',
    debt_to_equity_z: 'Debt-to-Equity',
    free_cash_flow_z: 'Free Cash Flow',
    dividend_yield_z: 'Dividend Yield'
  }
  
  const metricName = metricNames[metric] || metric
  const percentile = getPercentile(value)
  
  const assessment = value > 0.5 ? 'Strong' : value < -0.5 ? 'Weak' : 'Average'
  
  const content = `${ticker} ${metricName}: ${formatZScore(value)} (~${percentile}th percentile). ${assessment} fundamental positioning vs peers on this metric.`
  
  return <DarkTooltip content={content} />
}

// ============================================================
// MULTI-FACTOR CHART TOOLTIP (Radar/Spider Chart)
// ============================================================

export function MultiFactorChartTooltip() {
  const { tooltipsEnabled } = useTooltips()
  
  if (!tooltipsEnabled) return null
  
  const content = (
    <div className="text-xs space-y-2">
      <div className="font-semibold text-sm mb-2">How to Read Multi-Factor Analysis</div>
      
      <div className="space-y-1.5">
        <div>
          <strong className="text-blue-400">Value:</strong>
          <span className="text-gray-300 ml-1">P/E and P/B ratios - measures valuation attractiveness</span>
        </div>
        
        <div>
          <strong className="text-green-400">Growth:</strong>
          <span className="text-gray-300 ml-1">Earnings expansion - revenue and EPS growth trajectory</span>
        </div>
        
        <div>
          <strong className="text-purple-400">Quality:</strong>
          <span className="text-gray-300 ml-1">Profitability metrics - margins, ROE, cash flow quality</span>
        </div>
        
        <div>
          <strong className="text-orange-400">Momentum:</strong>
          <span className="text-gray-300 ml-1">Price momentum - short-term technical strength (RSI, price change)</span>
        </div>
        
        <div>
          <strong className="text-red-400">Size:</strong>
          <span className="text-gray-300 ml-1">Market capitalization - company scale and liquidity</span>
        </div>
        
        <div>
          <strong className="text-yellow-400">MTF (Multi-Timeframe):</strong>
          <span className="text-gray-300 ml-1">Consistency across horizons - alignment between short/mid/long term</span>
        </div>
      </div>
      
      <div className="border-t border-gray-700 pt-2 mt-2">
        <div className="text-gray-400 leading-relaxed">
          <strong>Larger area = stronger performance.</strong> Look for balanced profiles (pentagon shape) or clear strengths (spikes in specific factors).
        </div>
      </div>
    </div>
  )
  
  return <DarkTooltip content={content} />
}

// ============================================================
// RISK ANALYSIS TOOLTIP (Correlation/Volatility/Liquidity)
// ============================================================

export function RiskAnalysisTooltip({ riskType, value, ticker }) {
  const { tooltipsEnabled } = useTooltips()
  
  if (!tooltipsEnabled) return null
  
  const getRiskExplanation = () => {
    switch (riskType) {
      case 'market':
        return {
          title: 'Market Risk',
          description: `Beta-based systematic risk (${value}/100). Measures how this stock moves relative to market. >50 = above-average market sensitivity.`,
          interpretation: value > 60 ? 'High market exposure. Stock amplifies market moves.' : 
                         value > 40 ? 'Average market correlation. Moves in line with indices.' :
                         'Low market sensitivity. More independent price action.'
        }
      case 'volatility':
        return {
          title: 'Volatility Risk',
          description: `ATR-based price fluctuation (${value}/100). Higher values = larger price swings.`,
          interpretation: value > 60 ? 'High volatility. Wide stop-losses required, higher options premium.' :
                         value > 40 ? 'Moderate volatility. Standard risk management sufficient.' :
                         'Low volatility. Stable price action, suitable for conservative portfolios.'
        }
      case 'liquidity':
        return {
          title: 'Liquidity Risk',
          description: `Trading volume and spread analysis (${value}/100). Measures ease of entering/exiting positions.`,
          interpretation: value > 60 ? 'Liquidity concerns. Wide bid-ask spreads, potential slippage on large orders.' :
                         value > 40 ? 'Average liquidity. Normal execution for retail-sized orders.' :
                         'High liquidity. Tight spreads, minimal slippage, easy execution.'
        }
      case 'correlation':
        return {
          title: 'Correlation Risk',
          description: `Portfolio correlation (${value}/100). Shows how this position relates to your overall portfolio. High correlation = reduced diversification benefits.`,
          interpretation: value > 60 ? 'High correlation risk. If this sector crashes, high-correlation portfolio amplifies losses. Consider diversification.' :
                         value > 40 ? 'Moderate correlation. Some overlap with existing holdings but acceptable.' :
                         'Low correlation. Adds genuine diversification to portfolio. Reduces overall risk.'
        }
      default:
        return {
          title: 'Risk Metric',
          description: `Risk score: ${value}/100`,
          interpretation: 'Risk measure relative to portfolio and market.'
        }
    }
  }
  
  const risk = getRiskExplanation()
  
  const content = (
    <div className="text-xs space-y-2">
      <div className="font-semibold text-sm mb-2">{risk.title}</div>
      
      <div className="text-gray-300 leading-relaxed">
        {risk.description}
      </div>
      
      <div className="border-t border-gray-700 pt-2">
        <strong className="text-amber-400">Assessment:</strong>
        <div className="text-gray-300 mt-1 leading-relaxed">
          {risk.interpretation}
        </div>
      </div>
      
      {riskType === 'correlation' && value > 60 && (
        <div className="bg-red-900/30 border border-red-700 rounded p-2 mt-2">
          <div className="text-red-300 text-xs leading-relaxed">
            ⚠️ <strong>Diversification Alert:</strong> This position is highly correlated with your portfolio. Sector-wide downturn could amplify losses.
          </div>
        </div>
      )}
    </div>
  )
  
  return <DarkTooltip content={content} />
}

// ============================================================
// RISK LEVEL BADGE TOOLTIP (Overall Risk Score)
// ============================================================

export function RiskLevelTooltip({ level, score }) {
  const { tooltipsEnabled } = useTooltips()
  
  if (!tooltipsEnabled) return null
  
  const getLevelExplanation = (lvl) => {
    const levels = {
      'LOW': {
        description: 'Conservative risk profile. Suitable for risk-averse investors.',
        factors: 'Low volatility, high liquidity, stable fundamentals.',
        strategy: 'Core portfolio holding. Suitable for long-term buy-and-hold.'
      },
      'MODERATE': {
        description: 'Balanced risk/reward profile. Mainstream investment.',
        factors: 'Average volatility, adequate liquidity, mixed technical signals.',
        strategy: 'Suitable for diversified portfolios. Monitor key levels and catalysts.'
      },
      'HIGH': {
        description: 'Elevated risk. Requires active management.',
        factors: 'High volatility, potential liquidity concerns, or strong momentum.',
        strategy: 'Use tighter stops, position sizing, and hedging strategies. Not suitable for conservative accounts.'
      },
      'VERY HIGH': {
        description: 'Speculative risk. Only for aggressive traders.',
        factors: 'Extreme volatility, high correlation risk, or technical instability.',
        strategy: 'Tactical trades only. Use options for defined risk. Avoid in retirement accounts.'
      }
    }
    return levels[lvl] || levels['MODERATE']
  }
  
  const explanation = getLevelExplanation(level)
  
  const content = (
    <div className="text-xs space-y-2">
      <div className="font-semibold text-sm mb-2">Overall Risk: {level} ({score}/100)</div>
      
      <div className="text-gray-300 leading-relaxed">
        {explanation.description}
      </div>
      
      <div className="border-t border-gray-700 pt-2">
        <strong className="text-blue-400">Key Factors:</strong>
        <div className="text-gray-300 mt-1 leading-relaxed">
          {explanation.factors}
        </div>
      </div>
      
      <div className="border-t border-gray-700 pt-2">
        <strong className="text-amber-400">Recommended Strategy:</strong>
        <div className="text-gray-300 mt-1 leading-relaxed">
          {explanation.strategy}
        </div>
      </div>
    </div>
  )
  
  return <DarkTooltip content={content} />
}

// ============================================================
// VARE RISK TOOLTIP & BADGE (Dec 23, 2025)
// Purpose: Comprehensive multi-dimensional risk disclosure
// ============================================================

export function VARETooltip({ riskScore, riskCategory, marketRisk, volatilityRisk, liquidityRisk, correlationRisk, compositeOriginal, compositeAdjusted, ticker }) {
  const { tooltipsEnabled } = useTooltips()
  
  if (!tooltipsEnabled || !riskScore) return null
  
  const adjustmentPct = compositeOriginal && compositeAdjusted 
    ? (((compositeAdjusted - compositeOriginal) / compositeOriginal) * 100).toFixed(1)
    : null

  const getCategoryColor = (category) => {
    const colors = {
      'low': 'text-green-700',
      'medium': 'text-yellow-700',
      'high': 'text-orange-700',
      'critical': 'text-red-700'
    }
    return colors[category] || 'text-gray-700'
  }

  const getCategoryLabel = (category) => {
    const labels = {
      'low': 'Low Risk',
      'medium': 'Medium Risk',
      'high': 'High Risk',
      'critical': 'CRITICAL RISK'
    }
    return labels[category] || 'Unknown Risk'
  }

  const getPositionSizingGuidance = (score) => {
    if (score >= 80) return 'Max 2% portfolio (critical risk)'
    if (score >= 60) return 'Max 5% portfolio (high risk)'
    if (score >= 40) return 'Max 10% portfolio (medium risk)'
    return 'Up to 15% portfolio (low risk)'
  }

  const getStopLossGuidance = (volRisk) => {
    if (!volRisk) return 'Standard -5% stop-loss'
    if (volRisk >= 90) return 'Wide stop-loss -15% or more (extreme volatility)'
    if (volRisk >= 70) return 'Wide stop-loss -10% to -12% (high volatility)'
    if (volRisk >= 50) return 'Standard stop-loss -7% to -10%'
    return 'Standard stop-loss -5%'
  }

  const content = (
    <>
      <strong className={`block mb-2 text-sm font-bold ${getCategoryColor(riskCategory)}`}>
        VARE® Risk Analysis: {getCategoryLabel(riskCategory)} ({riskScore}/100)
      </strong>
      
      <p className="text-xs text-gray-700 leading-relaxed mb-3">
        <strong>Multi-Dimensional Risk Assessment:</strong> VARE® (Vitruvyan Adaptive Risk Engine) evaluates {ticker} across 4 risk dimensions.
        {riskCategory === 'critical' && ' 🚨 CRITICAL RISK requires extreme caution.'}
        {riskCategory === 'high' && ' ⚠️ HIGH RISK requires reduced sizing.'}
        {riskCategory === 'medium' && ' ⚡ MEDIUM RISK allows standard strategies.'}
        {riskCategory === 'low' && ' ✅ LOW RISK supports larger positions.'}
      </p>

      <div className="space-y-2 mb-3 text-xs">
        <div className="grid grid-cols-2 gap-2">
          <div>
            <strong>Market Risk:</strong> {marketRisk || 'N/A'}
            <div className="text-gray-600 text-[10px]">Beta vs benchmark</div>
          </div>
          <div>
            <strong>Volatility Risk:</strong> {volatilityRisk || 'N/A'}
            <div className="text-gray-600 text-[10px]">Intraday swings</div>
          </div>
          <div>
            <strong>Liquidity Risk:</strong> {liquidityRisk || 'N/A'}
            <div className="text-gray-600 text-[10px]">Volume stability</div>
          </div>
          <div>
            <strong>Correlation Risk:</strong> {correlationRisk || 'N/A'}
            <div className="text-gray-600 text-[10px]">Systematic exposure</div>
          </div>
        </div>
      </div>

      {adjustmentPct && (
        <div className="bg-gray-100 rounded p-2 mb-3 text-xs">
          <strong>Composite Adjustment:</strong><br/>
          Original: {compositeOriginal?.toFixed(2)} → Adjusted: {compositeAdjusted?.toFixed(2)} 
          <span className={`ml-1 font-bold ${parseFloat(adjustmentPct) < 0 ? 'text-red-600' : 'text-green-600'}`}>
            ({adjustmentPct > 0 ? '+' : ''}{adjustmentPct}%)
          </span>
        </div>
      )}

      <div className="border-t border-gray-200 pt-2 space-y-1 text-xs">
        <div><strong>Position Sizing:</strong> {getPositionSizingGuidance(riskScore)}</div>
        <div><strong>Stop-Loss:</strong> {getStopLossGuidance(volatilityRisk)}</div>
      </div>
    </>
  )

  return <VeeTooltip content={content}><div /></VeeTooltip>
}

export function VAREBadge({ riskScore, riskCategory, size = 'md', showLabel = true }) {
  if (!riskScore || !riskCategory) return null

  const sizeClasses = {
    'sm': 'text-[10px] px-2 py-0.5',
    'md': 'text-xs px-3 py-1',
    'lg': 'text-sm px-4 py-1.5'
  }

  const colorClasses = {
    'low': 'bg-green-100 text-green-800 border-green-300',
    'medium': 'bg-yellow-100 text-yellow-800 border-yellow-300',
    'high': 'bg-orange-100 text-orange-800 border-orange-300',
    'critical': 'bg-red-100 text-red-800 border-red-300'
  }

  const icons = {
    'low': '✅',
    'medium': '⚡',
    'high': '⚠️',
    'critical': '🚨'
  }

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border font-medium ${sizeClasses[size]} ${colorClasses[riskCategory]}`}>
      <span>{icons[riskCategory]}</span>
      {showLabel && <span>Risk: {riskScore}</span>}
    </span>
  )
}

// ============================================================
// VWRE ATTRIBUTION TOOLTIP (Dec 23, 2025)
// Purpose: Factor contribution explainability
// ============================================================

export function VWRETooltip({ attribution, ticker, primaryDriver, rankExplanation, factorContributions, factorPercentages }) {
  const { tooltipsEnabled } = useTooltips()
  
  if (!tooltipsEnabled) return null

  // ✅ FLEXIBLE INPUT: Accept either attribution object OR individual props
  const driver = primaryDriver || attribution?.primary_driver
  const explanation = rankExplanation || attribution?.rank_explanation
  const contributions = factorContributions || attribution?.factor_contributions
  const percentages = factorPercentages || attribution?.factor_percentages
  const secondaryDrivers = attribution?.secondary_drivers

  // Guard: If no data at all, don't render tooltip
  if (!driver && !explanation) {
    return <div className="inline-block" />
  }

  const content = (
    <>
      <strong className="block mb-2 text-sm font-bold text-vitruvyan-accent">
        Attribution Analysis (VWRE®)
      </strong>
      
      <p className="text-xs text-gray-700 leading-relaxed mb-3">
        <strong>Rank Explanation:</strong> {explanation || `${ticker} ranking driven by ${driver}.`}
      </p>

      <div className="space-y-2 mb-3 text-xs">
        <div>
          <strong className="text-vitruvyan-primary">Primary Driver:</strong> {driver} 
          {percentages && percentages[driver] && (
            <span className="ml-1 text-gray-600">
              ({percentages[driver]?.toFixed(1)}% weight)
            </span>
          )}
        </div>
        
        {secondaryDrivers && secondaryDrivers.length > 0 && (
          <div>
            <strong>Secondary:</strong> {secondaryDrivers.join(', ')}
          </div>
        )}
      </div>

      {percentages && (
        <div className="bg-gray-100 rounded p-2 text-xs">
          <strong className="block mb-1">Factor Contributions:</strong>
          <div className="space-y-1">
            {Object.entries(factor_percentages)
              .sort(([, a], [, b]) => b - a)
              .slice(0, 5)
              .map(([factor, pct]) => (
                <div key={factor} className="flex justify-between">
                  <span className="capitalize">{factor.replace('_z', '')}:</span>
                  <span className="font-semibold">{pct.toFixed(1)}%</span>
                </div>
              ))}
          </div>
        </div>
      )}
    </>
  )

  return <VeeTooltip content={content}><div /></VeeTooltip>
}

// ============================================================
// TOOLTIP TOGGLE (Integrated from TooltipToggle.jsx)
// ============================================================

export function TooltipToggle() {
  const { tooltipsEnabled, toggleTooltips } = useTooltips()

  return (
    <button
      onClick={toggleTooltips}
      className={`
        inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium
        transition-all duration-200 border-2
        ${tooltipsEnabled 
          ? 'bg-vitruvyan-primary text-white border-vitruvyan-primary hover:bg-vitruvyan-primary-dark' 
          : 'bg-gray-100 text-gray-600 border-gray-300 hover:bg-gray-200'
        }
      `}
      title={tooltipsEnabled ? 'Disable explainability tooltips' : 'Enable explainability tooltips'}
    >
      {tooltipsEnabled ? (
        <>
          <HelpCircle className="w-3.5 h-3.5" />
          <span>Tooltips ON</span>
        </>
      ) : (
        <>
          <HelpCircle className="w-3.5 h-3.5 opacity-50" />
          <span>Tooltips OFF</span>
        </>
      )}
    </button>
  )
}

// ============================================================
// EXPORTS
// ============================================================

export default {
  // Base components
  VeeTooltip,
  VeeChartTooltip,
  DarkTooltip,
  CompositeTooltip,
  
  // Factor z-score tooltips (VEE-style, extracted from NeuralEngineUI)
  MomentumTooltip,
  TrendTooltip,
  VolatilityTooltip,
  SentimentTooltip,
  
  // Composite & verdict tooltips
  CompositeScoreTooltip,
  
  // Comparison tooltips
  FactorDeltaTooltip,
  RankingTooltip,
  DispersionTooltip,
  
  // Fundamentals tooltips
  FundamentalsTooltip,
  
  // Chart tooltips (Multi-Factor & Risk Analysis)
  MultiFactorChartTooltip,
  RiskAnalysisTooltip,
  RiskLevelTooltip,
  
  // VARE Risk tooltips (Dec 23, 2025)
  VARETooltip,
  VAREBadge,
  
  // VWRE Attribution tooltips (Dec 23, 2025)
  VWRETooltip,
  
  // Toggle control
  TooltipToggle
}
