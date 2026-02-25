/**
 * MULTI-FACTOR RADAR CHART
 * 
 * Displays 6 quantitative factors in radar/spider chart format.
 * 
 * Data Source: finalState.detailed.ranking.stocks[0].factors
 * 
 * Factors:
 * - Value (P/E, P/B ratios)
 * - Growth (earnings growth)
 * - Quality (profitability metrics)
 * - Momentum (academic momentum)
 * - Size (market cap)
 * - Multi-Timeframe Consensus (MTF)
 */

'use client'

import { useState } from 'react'
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Legend, Tooltip } from 'recharts'
import VeeLayer, { useVeeContext } from '@/components/explainability/vee/VeeLayer'
import { VeeChartTooltip } from '@/components/explainability/tooltips/TooltipLibrary'
import VeeBadge from '@/components/explainability/badges/VeeBadge'
import TabPanel from '@/components/ui/TabPanel'

export default function FactorRadarChart({ factors, explainability, className = '' }) {
  // Guard: Don't render if no factors
  if (!factors) return null

  // Normalize factors to 0-100 scale for better visualization
  const normalize = (value, max = 2) => {
    if (value === null || value === undefined) return 0
    return Math.min(Math.max((value / max) * 100, 0), 100)
  }

  const data = [
    {
      factor: 'Value',
      score: normalize(factors.value, 2),
      fullMark: 100,
    },
    {
      factor: 'Growth',
      score: normalize(factors.growth, 2),
      fullMark: 100,
    },
    {
      factor: 'Quality',
      score: normalize(factors.quality, 2),
      fullMark: 100,
    },
    {
      factor: 'Momentum',
      score: normalize(factors.acad_mom, 1),
      fullMark: 100,
    },
    {
      factor: 'Size',
      score: normalize(factors.size, 30),
      fullMark: 100,
    },
    {
      factor: 'MTF',
      score: normalize(factors.mtf_consensus, 1),
      fullMark: 100,
    },
  ]

  const tabs = [
    {
      label: 'Chart',
      content: (
        <VeeLayer explainability={explainability} chartType="radar">
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={data}>
              <PolarGrid stroke="#e5e7eb" />
              <PolarAngleAxis 
                dataKey="factor" 
                tick={{ fill: '#6b7280', fontSize: 12 }}
              />
              <PolarRadiusAxis 
                angle={90} 
                domain={[0, 100]} 
                tick={{ fill: '#9ca3af', fontSize: 10 }}
              />
              <Radar
                name="Score"
                dataKey="score"
                stroke="#333333"
                fill="#333333"
                fillOpacity={0.3}
              />
              <Tooltip 
                content={<CustomVeeTooltip />}
              />
            </RadarChart>
          </ResponsiveContainer>

          {/* Factor Details */}
          <div className="mt-4 grid grid-cols-3 gap-2 text-xs">
            <div>
              <span className="text-gray-500">Value:</span>
              <span className="ml-1 font-semibold text-gray-900">{factors.value?.toFixed(2)}</span>
            </div>
            <div>
              <span className="text-gray-500">Growth:</span>
              <span className="ml-1 font-semibold text-gray-900">{factors.growth?.toFixed(2)}</span>
            </div>
            <div>
              <span className="text-gray-500">Quality:</span>
              <span className="ml-1 font-semibold text-gray-900">{factors.quality?.toFixed(2)}</span>
            </div>
            <div>
              <span className="text-gray-500">Momentum:</span>
              <span className="ml-1 font-semibold text-gray-900">{factors.acad_mom?.toFixed(2)}</span>
            </div>
            <div>
              <span className="text-gray-500">Size:</span>
              <span className="ml-1 font-semibold text-gray-900">{factors.size?.toFixed(1)}B</span>
            </div>
            <div>
              <span className="text-gray-500">MTF:</span>
              <span className="ml-1 font-semibold text-gray-900">{factors.mtf_consensus?.toFixed(2)}</span>
            </div>
          </div>

          {/* VEE Badges for factors */}
          {explainability && (
            <div className="mt-3 flex flex-wrap gap-2">
              <VeeBadge text="Value: P/E and P/B ratios" />
              <VeeBadge text="Growth: Earnings expansion" />
              <VeeBadge text="Quality: Profitability metrics" />
            </div>
          )}
        </VeeLayer>
      )
    },
    {
      label: 'How to Read',
      content: (
        <div className="p-6 bg-blue-50 rounded-lg min-h-[300px]">
          <h3 className="font-bold mb-4 flex items-center gap-2 text-gray-900">
            📊 Understanding the Multi-Factor Chart
          </h3>
          <ul className="space-y-3 text-sm text-gray-700">
            <li className="flex items-start gap-2">
              <span className="text-blue-600 font-bold">•</span>
              <div>
                <strong>Each axis</strong> represents a quantitative factor measuring different aspects of stock performance
              </div>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-600 font-bold">•</span>
              <div>
                <strong>Larger area</strong> indicates stronger overall performance across all factors
              </div>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-600 font-bold">•</span>
              <div>
                <strong>Balanced shape</strong> shows diversified strength without over-reliance on single factors
              </div>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-600 font-bold">•</span>
              <div>
                <strong>Spikes</strong> reveal factor specialization — exceptional performance in specific areas
              </div>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-600 font-bold">•</span>
              <div>
                <strong>Compare shapes</strong> across tickers to identify different strength profiles
              </div>
            </li>
          </ul>
          
          <div className="mt-4 pt-4 border-t border-blue-200">
            <p className="text-xs text-gray-600 italic">
              💡 Tip: A well-balanced hexagon suggests stable performance, while irregular shapes indicate specialized strengths
            </p>
          </div>
        </div>
      )
    }
  ]

  return (
    <div className={`bg-white rounded-lg border border-gray-200 p-4 ${className}`}>
      <h3 className="text-sm font-semibold text-gray-900 mb-4">Multi-Factor Analysis</h3>
      <TabPanel tabs={tabs} defaultTab={0} />
    </div>
  )
}

// Custom Tooltip with Natural Language Explanations
function CustomVeeTooltip({ active, payload }) {
  if (!active || !payload || payload.length === 0) return null

  const factor = payload[0]?.payload?.factor
  const score = payload[0]?.value?.toFixed(1)

  // Natural language explanations for each factor
  const explanations = {
    'Value': {
      title: 'Value Factor',
      explanation: `This stock scores ${score}/100 on value metrics. Higher scores indicate the stock is undervalued based on P/E and P/B ratios compared to peers. A strong value score suggests potential upside if the market corrects its pricing.`
    },
    'Growth': {
      title: 'Growth Factor',
      explanation: `Growth score of ${score}/100 reflects earnings expansion potential. Higher values indicate strong historical revenue/earnings growth and analyst expectations for continued expansion. Growth stocks typically reinvest profits for future gains.`
    },
    'Quality': {
      title: 'Quality Factor',
      explanation: `Quality score ${score}/100 measures profitability and financial health. High scores indicate strong return on equity, stable margins, and healthy balance sheets. Quality stocks tend to be more resilient during market downturns.`
    },
    'Momentum': {
      title: 'Momentum Factor',
      explanation: `Momentum ${score}/100 captures recent price trends and buying pressure. High momentum suggests strong recent performance and positive market sentiment. This factor identifies stocks "riding the wave" of investor enthusiasm.`
    },
    'Size': {
      title: 'Size Factor',
      explanation: `Size score ${score}/100 reflects market capitalization positioning. Higher scores indicate larger, more established companies with typically lower volatility but potentially slower growth. Smaller scores suggest higher risk/reward profiles.`
    },
    'MTF': {
      title: 'Multi-Timeframe Consensus',
      explanation: `MTF score ${score}/100 shows agreement across short, medium, and long-term indicators. High scores mean bullish signals align across all timeframes, suggesting strong conviction. Low scores indicate conflicting signals between horizons.`
    }
  }

  const info = explanations[factor] || { title: factor, explanation: `Score: ${score}/100` }

  return (
    <div className="bg-white border border-gray-300 rounded-lg shadow-xl p-4 max-w-sm">
      <p className="text-sm font-bold text-gray-900 mb-2">{info.title}</p>
      <p className="text-xs text-gray-700 leading-relaxed">{info.explanation}</p>
      <div className="mt-3 pt-3 border-t border-gray-200">
        <p className="text-xs text-gray-500">
          Current Score: <span className="font-semibold text-vitruvyan-accent">{score}/100</span>
        </p>
      </div>
    </div>
  )
}
