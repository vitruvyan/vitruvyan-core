/**
 * VARE RISK BREAKDOWN CHART
 * 
 * Displays 4 risk components as donut chart.
 * 
 * Data Source: finalState.detailed.ranking.stocks[0].risk
 * 
 * Risk Components:
 * - Market Risk (systematic risk)
 * - Volatility Risk (price fluctuation)
 * - Liquidity Risk (trading volume)
 * - Correlation Risk (portfolio concentration)
 */

'use client'

import { useState } from 'react'
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts'
import { AlertTriangle } from 'lucide-react'
import VeeLayer from '@/components/explainability/vee/VeeLayer'
import { VeeChartTooltip } from '@/components/explainability/tooltips/TooltipLibrary'
import TabPanel from '@/components/ui/TabPanel'

const RISK_COLORS = {
  market: '#ef4444',      // red-500
  volatility: '#f59e0b',  // amber-500
  liquidity: '#10b981',   // green-500
  correlation: '#8b5cf6', // purple-500
}

export default function RiskBreakdownChart({ risk, explainability, className = '' }) {
  // Guard: Don't render if no risk data
  if (!risk) return null

  const data = [
    { name: 'Market Risk', value: risk.vare_market_risk, color: RISK_COLORS.market },
    { name: 'Volatility Risk', value: risk.vare_volatility_risk, color: RISK_COLORS.volatility },
    { name: 'Liquidity Risk', value: risk.vare_liquidity_risk, color: RISK_COLORS.liquidity },
    { name: 'Correlation Risk', value: risk.vare_correlation_risk, color: RISK_COLORS.correlation },
  ]

  // Check if we have valid data to display
  const hasValidData = data.some(d => d.value !== null && d.value !== undefined)
  
  if (!hasValidData) {
    return (
      <div className={`bg-gray-50 border border-gray-200 rounded-lg p-6 ${className}`}>
        <div className="flex items-center gap-2 text-gray-600 mb-2">
          <AlertTriangle size={16} />
          <span className="font-medium">Risk Analysis</span>
        </div>
        <p className="text-sm text-gray-500">
          Detailed risk breakdown is not available for this ticker. 
          The overall risk score ({risk.vare_risk_score?.toFixed(1) || 'N/A'}) and category ({risk.vare_risk_category || 'Unknown'}) are shown above.
        </p>
      </div>
    )
  }

  // Risk category badge color (semitransparent palette)
  const getCategoryColor = (category) => {
    const colors = {
      LOW: 'text-[rgba(22,163,74,1)] bg-[rgba(34,197,94,0.08)] border-[rgba(34,197,94,0.20)]',
      MEDIUM: 'text-[rgba(217,119,6,1)] bg-[rgba(245,158,11,0.08)] border-[rgba(245,158,11,0.20)]',
      HIGH: 'text-[rgba(220,38,38,1)] bg-[rgba(239,68,68,0.08)] border-[rgba(239,68,68,0.20)]',
    }
    return colors[category] || colors.MEDIUM
  }

  const tabs = [
    {
      label: 'Chart',
      content: (
        <VeeLayer explainability={explainability} chartType="risk">
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={90}
                paddingAngle={2}
                dataKey="value"
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip 
                content={<CustomVeeTooltip />}
              />
            </PieChart>
          </ResponsiveContainer>

          {/* Risk Breakdown List */}
          <div className="mt-4 space-y-2">
            {data.map((item) => (
              <div key={item.name} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <div 
                    className="w-3 h-3 rounded-full" 
                    style={{ backgroundColor: item.color }}
                  />
                  <span className="text-gray-700">{item.name}</span>
                </div>
                <span className="font-semibold text-gray-900">{item.value.toFixed(1)}</span>
              </div>
            ))}
          </div>

          {/* VARE Explanation */}
          {risk.vare_explanation && (
            <p className="mt-3 text-xs text-gray-600 italic border-t border-gray-100 pt-3">
              {risk.vare_explanation}
            </p>
          )}
        </VeeLayer>
      )
    },
    {
      label: 'How to Read',
      content: (
        <div className="p-6 bg-amber-50 rounded-lg min-h-[250px]">
          <h3 className="font-bold mb-4 flex items-center gap-2 text-gray-900">
            ⚠️ Understanding Risk Analysis
          </h3>
          <ul className="space-y-3 text-sm text-gray-700">
            <li className="flex items-start gap-2">
              <span className="text-amber-600 font-bold">•</span>
              <div>
                <strong>Higher values</strong> indicate greater risk exposure in that specific dimension
              </div>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-amber-600 font-bold">•</span>
              <div>
                <strong>Market Risk</strong> (red): Sensitivity to systematic market movements
              </div>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-amber-600 font-bold">•</span>
              <div>
                <strong>Volatility Risk</strong> (amber): Price fluctuation intensity and unpredictability
              </div>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-amber-600 font-bold">•</span>
              <div>
                <strong>Liquidity Risk</strong> (green): Ease of entering/exiting positions without price impact
              </div>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-amber-600 font-bold">•</span>
              <div>
                <strong>Correlation Risk</strong> (purple): Portfolio concentration and diversification level
              </div>
            </li>
          </ul>
          
          <div className="mt-4 pt-4 border-t border-amber-200">
            <p className="text-xs text-gray-600 italic">
              💡 Tip: Balanced risk profile shows similar slice sizes, while concentrated exposure reveals larger individual segments
            </p>
          </div>
        </div>
      )
    }
  ]

  return (
    <div className={`bg-white rounded-lg border border-gray-200 p-4 ${className}`}>
      {/* Header with Risk Score */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-900">Risk Analysis</h3>
        <div className={`flex items-center gap-2 px-3 py-1 rounded-lg border ${getCategoryColor(risk.vare_risk_category)}`}>
          <AlertTriangle size={14} />
          <span className="text-xs font-semibold">
            {risk.vare_risk_category} ({risk.vare_risk_score?.toFixed(0)}/100)
          </span>
        </div>
      </div>

      <TabPanel tabs={tabs} defaultTab={0} />
    </div>
  )
}

// Custom Tooltip with Natural Language Explanations
function CustomVeeTooltip({ active, payload }) {
  if (!active || !payload || payload.length === 0) return null

  const riskType = payload[0]?.name
  const riskValue = payload[0]?.value?.toFixed(1)

  // Natural language explanations for each risk component
  const explanations = {
    'Market Risk': {
      title: 'Market Risk',
      explanation: `This stock has ${riskValue}/100 exposure to systematic market movements. Higher values mean the stock tends to move strongly with overall market trends (high beta). During market crashes, high market risk stocks typically fall harder, but they also rally more aggressively in bull markets.`
    },
    'Volatility Risk': {
      title: 'Volatility Risk',
      explanation: `Volatility score of ${riskValue}/100 measures daily price swings. High volatility means larger unpredictable price movements, creating both opportunity and danger. Conservative investors prefer low volatility, while traders may seek higher volatility for profit opportunities.`
    },
    'Liquidity Risk': {
      title: 'Liquidity Risk',
      explanation: `Liquidity risk ${riskValue}/100 reflects how easily you can buy/sell without affecting the price. Higher scores indicate lower trading volumes or wider bid-ask spreads. Low liquidity can trap investors during selloffs or cause slippage when entering/exiting positions.`
    },
    'Correlation Risk': {
      title: 'Correlation Risk',
      explanation: `Correlation risk ${riskValue}/100 shows how this position relates to your overall portfolio. High correlation means this stock moves with your other holdings, reducing diversification benefits. If this sector crashes, a high-correlation portfolio amplifies losses.`
    }
  }

  const info = explanations[riskType] || { title: riskType, explanation: `Risk level: ${riskValue}/100` }

  return (
    <div className="bg-white border border-gray-300 rounded-lg shadow-xl p-4 max-w-sm">
      <p className="text-sm font-bold text-gray-900 mb-2">{info.title}</p>
      <p className="text-xs text-gray-700 leading-relaxed">{info.explanation}</p>
      <div className="mt-3 pt-3 border-t border-gray-200">
        <p className="text-xs text-gray-500">
          Risk Level: <span className="font-semibold text-amber-600">{riskValue}/100</span>
        </p>
      </div>
    </div>
  )
}
