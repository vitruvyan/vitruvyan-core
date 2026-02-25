/**
 * COMPARATIVE RADAR CHART
 * 
 * Multi-ticker factor comparison visualization.
 * Shows z-scores for each ticker across multiple factors.
 * 
 * Created: Dec 21, 2025
 * 
 * Props:
 * - tickers: string[] - Array of ticker symbols
 * - numericalPanel: array - Array of {ticker, momentum_z, trend_z, vola_z, sentiment_z, ...}
 * - factors?: string[] - Custom factor list (default: momentum, trend, volatility, sentiment)
 */

'use client'

import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Legend, Tooltip } from 'recharts'
import { Info } from 'lucide-react'
import { DarkTooltip } from '../../explainability/tooltips/TooltipLibrary'

// Color palette for tickers (max 5 tickers)
const TICKER_COLORS = [
  '#8b5cf6', // purple (winner)
  '#3b82f6', // blue
  '#10b981', // green
  '#f59e0b', // amber
  '#ef4444', // red (loser)
]

// Default factors to display with detailed explanations
const DEFAULT_FACTORS = [
  { 
    key: 'momentum_z', 
    label: 'Momentum', 
    description: 'Short-term price momentum strength',
    tooltip: 'Measures recent price acceleration using RSI and MACD indicators. Positive z-scores indicate strong upward momentum, negative scores suggest downward pressure. Range: typically -3σ to +3σ.'
  },
  { 
    key: 'trend_z', 
    label: 'Trend', 
    description: 'Long-term directional strength',
    tooltip: 'Evaluates sustained price direction using moving averages (SMA, EMA). Positive values indicate bullish trends, negative values signal bearish trends. Higher absolute values = stronger trend.'
  },
  { 
    key: 'vola_z', 
    label: 'Volatility', 
    description: 'Price stability (inverted)',
    tooltip: 'Price fluctuation intensity - INVERTED so lower values are better. Negative z-scores indicate stability (good), positive scores suggest high volatility (risky). Based on historical volatility analysis.'
  },
  { 
    key: 'sentiment_z', 
    label: 'Sentiment', 
    description: 'Market sentiment analysis',
    tooltip: 'Aggregated market sentiment from news, social media, and analyst opinions. Positive scores = bullish sentiment, negative = bearish. Analyzed via FinBERT NLP model with 91% accuracy.'
  },
]

export default function ComparativeRadarChart({ 
  tickers = [], 
  numericalPanel = [],
  factors = DEFAULT_FACTORS,
  className = '' 
}) {
  // Guard: Need at least 2 tickers
  if (!tickers || tickers.length < 2 || !numericalPanel || numericalPanel.length < 2) {
    return (
      <div className={`bg-gradient-to-br from-purple-50 to-indigo-50 border border-purple-200 rounded-lg p-6 ${className}`}>
        <div className="flex items-center gap-2 mb-4">
          <h3 className="text-lg font-semibold text-gray-900">📊 Visual Comparison</h3>
          <DarkTooltip content="Radar chart showing factor z-scores for each ticker. Higher values = better performance." asSpan>
            <Info className="w-4 h-4 text-gray-400 cursor-help" />
          </DarkTooltip>
        </div>
        <div className="text-center py-8 text-gray-500 text-sm">
          No comparison data available
        </div>
      </div>
    )
  }

  // Build data map: ticker → {factor: z-score}
  const tickerDataMap = {}
  numericalPanel.forEach(item => {
    tickerDataMap[item.ticker] = item
  })

  // Transform data for Recharts radar format
  // Each factor becomes a data point with multiple ticker values
  const radarData = factors.map(factor => {
    const dataPoint = {
      factor: factor.label,
      fullMark: 3, // z-score range: -3 to +3
    }
    
    // Add each ticker's z-score for this factor
    tickers.forEach((ticker, index) => {
      const tickerData = tickerDataMap[ticker]
      const zScore = tickerData?.[factor.key] || 0
      // Normalize to 0-100 scale (z-score -3 to +3 → 0 to 100)
      dataPoint[ticker] = ((zScore + 3) / 6) * 100
    })
    
    return dataPoint
  })

  // Custom tooltip with factor explanations
  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload || payload.length === 0) return null

    const factorData = factors.find(f => f.label === payload[0]?.payload?.factor)

    return (
      <div className="bg-white p-4 rounded-lg shadow-xl border border-gray-200 max-w-xs">
        <div className="mb-2 pb-2 border-b border-gray-200">
          <p className="font-semibold text-sm text-gray-900">{payload[0]?.payload?.factor}</p>
          {factorData && (
            <p className="text-xs text-gray-600 mt-1">{factorData.tooltip}</p>
          )}
        </div>
        
        <div className="space-y-1.5">
          {payload.map((entry, index) => {
            // Convert back to z-score for display
            const normalizedValue = entry.value || 0
            const zScore = ((normalizedValue / 100) * 6) - 3
            
            // Get color-coded interpretation
            let interpretation = ''
            let interpretColor = 'text-gray-600'
            
            if (factorData?.key === 'vola_z') {
              // Volatility is inverted: negative = good
              if (zScore < -1) {
                interpretation = 'Very Stable'
                interpretColor = 'text-green-600'
              } else if (zScore < 0) {
                interpretation = 'Stable'
                interpretColor = 'text-green-600'
              } else if (zScore < 1) {
                interpretation = 'Volatile'
                interpretColor = 'text-orange-600'
              } else {
                interpretation = 'Very Volatile'
                interpretColor = 'text-red-600'
              }
            } else {
              // Normal factors: positive = good
              if (zScore > 1.5) {
                interpretation = 'Exceptional'
                interpretColor = 'text-green-600'
              } else if (zScore > 0.5) {
                interpretation = 'Strong'
                interpretColor = 'text-green-600'
              } else if (zScore > -0.5) {
                interpretation = 'Average'
                interpretColor = 'text-gray-600'
              } else if (zScore > -1.5) {
                interpretation = 'Weak'
                interpretColor = 'text-orange-600'
              } else {
                interpretation = 'Very Weak'
                interpretColor = 'text-red-600'
              }
            }
            
            return (
              <div key={index} className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2 flex-1">
                  <div 
                    className="w-3 h-3 rounded-full flex-shrink-0" 
                    style={{ backgroundColor: entry.color }}
                  />
                  <span className="font-medium text-xs">{entry.name}:</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`font-mono text-xs font-semibold ${zScore > 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {zScore > 0 ? '+' : ''}{zScore.toFixed(2)}σ
                  </span>
                  <span className={`text-xs font-medium ${interpretColor}`}>
                    {interpretation}
                  </span>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    )
  }

  return (
    <div className={`bg-gradient-to-br from-purple-50 to-indigo-50 border border-purple-200 rounded-lg p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <h3 className="text-lg font-semibold text-gray-900">📊 Visual Comparison</h3>
          <DarkTooltip 
            content={
              <div className="space-y-2">
                <p className="font-semibold">Multi-Ticker Radar Chart</p>
                <p>Compares z-scores across {factors.length} quantitative factors:</p>
                <ul className="list-disc list-inside space-y-1 text-xs">
                  {factors.map(f => (
                    <li key={f.key}><strong>{f.label}</strong>: {f.description}</li>
                  ))}
                </ul>
                <p className="text-xs italic border-t border-gray-600 pt-2 mt-2">
                  Hover over chart points for detailed explanations and interpretations.
                </p>
              </div>
            }
            asSpan
          >
            <Info className="w-4 h-4 text-gray-400 cursor-help" />
          </DarkTooltip>
        </div>
        <div className="text-xs text-gray-500">
          {tickers.length} tickers • {factors.length} factors
        </div>
      </div>

      {/* Radar Chart */}
      <ResponsiveContainer width="100%" height={400}>
        <RadarChart data={radarData}>
          <PolarGrid stroke="#d1d5db" />
          <PolarAngleAxis 
            dataKey="factor" 
            tick={{ fill: '#374151', fontSize: 12, fontWeight: 500 }}
          />
          <PolarRadiusAxis 
            angle={90} 
            domain={[0, 100]} 
            tick={{ fill: '#6b7280', fontSize: 10 }}
            tickFormatter={(value) => {
              // Convert back to z-score for axis labels
              const zScore = ((value / 100) * 6) - 3
              return `${zScore.toFixed(1)}σ`
            }}
          />
          
          {/* Render a Radar line for each ticker */}
          {tickers.map((ticker, index) => (
            <Radar
              key={ticker}
              name={ticker}
              dataKey={ticker}
              stroke={TICKER_COLORS[index % TICKER_COLORS.length]}
              fill={TICKER_COLORS[index % TICKER_COLORS.length]}
              fillOpacity={0.2}
              strokeWidth={2}
            />
          ))}
          
          <Legend 
            wrapperStyle={{ paddingTop: '20px' }}
            iconType="circle"
          />
          <Tooltip content={<CustomTooltip />} />
        </RadarChart>
      </ResponsiveContainer>

      {/* Footer explanation with z-score legend */}
      <div className="mt-4 pt-4 border-t border-purple-200">
        <div className="text-xs text-gray-600 space-y-2">
          <p className="italic text-center">
            Each point represents a factor's z-score for the ticker. Higher values = stronger performance.
          </p>
          <div className="flex items-center justify-center gap-6 text-xs">
            <div className="flex items-center gap-1">
              <span className="text-green-600 font-semibold">+2.0σ</span>
              <span className="text-gray-500">Exceptional</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="text-green-600 font-semibold">+1.0σ</span>
              <span className="text-gray-500">Strong</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="text-gray-600 font-semibold">0.0σ</span>
              <span className="text-gray-500">Average</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="text-red-600 font-semibold">-1.0σ</span>
              <span className="text-gray-500">Weak</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
