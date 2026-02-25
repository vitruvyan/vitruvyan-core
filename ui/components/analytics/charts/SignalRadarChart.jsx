/**
 * SIGNAL DRIVERS RADAR CHART
 * 
 * Displays 4 signal driver z-scores in radar/spider format.
 * 
 * REUSABLE COMPOSITE PATTERN:
 * - Can be used in single ticker, comparison, screening, allocation
 * - Receives normalized data, doesn't fetch
 * - Provides VEE tooltips for explainability
 * 
 * Signal Drivers:
 * - Momentum (short-term price acceleration)
 * - Trend (long-term directional strength)
 * - Volatility (risk/opportunity measure)
 * - Sentiment (market narrative consensus)
 */

'use client'

import { useState } from 'react'
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip } from 'recharts'
import { Activity, TrendingUp, BarChart2, MessageCircle, HelpCircle } from 'lucide-react'

// Z-score normalization: convert -3 to +3 range to 0-100 for visualization
const normalizeZScore = (value) => {
  if (value === null || value === undefined) return 50 // neutral
  // Map -3 to 0, 0 to 50, +3 to 100
  return Math.min(Math.max(((value + 3) / 6) * 100, 0), 100)
}

// Signal driver metadata
const SIGNAL_METADATA = {
  momentum: {
    label: 'Momentum',
    icon: Activity,
    color: '#10b981', // emerald-500
    description: 'Short-term price acceleration and buying pressure',
    technical: 'Measures RSI (14-day), MACD histogram, and recent price velocity. High momentum (>1.0) suggests strong buying pressure; low momentum (<-1.0) indicates selling pressure.'
  },
  trend: {
    label: 'Trend',
    icon: TrendingUp,
    color: '#3b82f6', // blue-500
    description: 'Long-term directional strength and sustainability',
    technical: 'Evaluates 50/200 SMA relationship, ADX strength, and price position relative to moving averages. Strong trend (>1.0) confirms sustained directional movement.'
  },
  volatility: {
    label: 'Volatility',
    icon: BarChart2,
    color: '#f59e0b', // amber-500
    description: 'Price fluctuation intensity (opportunity & risk)',
    technical: 'ATR-based measurement of daily price swings. High volatility offers profit opportunities but increases risk. Low volatility suggests consolidation.'
  },
  sentiment: {
    label: 'Sentiment',
    icon: MessageCircle,
    color: '#8b5cf6', // purple-500
    description: 'Market narrative consensus from news and social',
    technical: 'Aggregates news sentiment, social mentions, and analyst ratings via FinBERT NLP. Positive sentiment (>0.5) reflects bullish market narrative.'
  }
}

export default function SignalRadarChart({ 
  signals, 
  showLegend = true,
  showTooltips = true,
  height = 280,
  className = '' 
}) {
  const [activeSignal, setActiveSignal] = useState(null)

  // Guard: Don't render if no signals
  if (!signals) return null

  // Check if we have at least some data
  const hasData = Object.values(signals).some(v => v !== null && v !== undefined)
  if (!hasData) return null

  // Build radar data
  const data = [
    {
      signal: 'Momentum',
      key: 'momentum',
      value: normalizeZScore(signals.momentum_z),
      raw: signals.momentum_z,
      fullMark: 100,
    },
    {
      signal: 'Trend',
      key: 'trend',
      value: normalizeZScore(signals.trend_z),
      raw: signals.trend_z,
      fullMark: 100,
    },
    {
      signal: 'Volatility',
      key: 'volatility',
      value: normalizeZScore(signals.volatility_z),
      raw: signals.volatility_z,
      fullMark: 100,
    },
    {
      signal: 'Sentiment',
      key: 'sentiment',
      value: normalizeZScore(signals.sentiment_z),
      raw: signals.sentiment_z,
      fullMark: 100,
    },
  ]

  return (
    <div className={`${className}`}>
      {/* Radar Chart */}
      <ResponsiveContainer width="100%" height={height}>
        <RadarChart data={data} margin={{ top: 20, right: 30, bottom: 20, left: 30 }}>
          <PolarGrid stroke="#e5e7eb" />
          <PolarAngleAxis 
            dataKey="signal" 
            tick={({ payload, x, y, cx, cy, ...rest }) => {
              const meta = SIGNAL_METADATA[payload.value.toLowerCase()]
              const Icon = meta?.icon || HelpCircle
              return (
                <g transform={`translate(${x},${y})`}>
                  <text
                    x={0}
                    y={0}
                    dy={4}
                    textAnchor={x > cx ? 'start' : x < cx ? 'end' : 'middle'}
                    fill="#4b5563"
                    fontSize={11}
                    fontWeight={500}
                  >
                    {payload.value}
                  </text>
                </g>
              )
            }}
          />
          <PolarRadiusAxis 
            angle={90} 
            domain={[0, 100]} 
            tick={{ fill: '#9ca3af', fontSize: 9 }}
            tickCount={5}
          />
          <Radar
            name="Signal Strength"
            dataKey="value"
            stroke="#1f2937"
            fill="#1f2937"
            fillOpacity={0.2}
            strokeWidth={2}
          />
          {showTooltips && (
            <Tooltip content={<SignalTooltip />} />
          )}
        </RadarChart>
      </ResponsiveContainer>

      {/* Legend with z-scores */}
      {showLegend && (
        <div className="mt-3 grid grid-cols-2 gap-2">
          {data.map(item => {
            const meta = SIGNAL_METADATA[item.key]
            const Icon = meta.icon
            const rawValue = item.raw
            const badge = getZScoreBadge(rawValue)
            
            return (
              <div 
                key={item.key}
                className="flex items-center gap-2 p-2 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors"
                onMouseEnter={() => setActiveSignal(item.key)}
                onMouseLeave={() => setActiveSignal(null)}
              >
                <Icon size={14} style={{ color: meta.color }} />
                <span className="text-xs text-gray-600 flex-1">{meta.label}</span>
                <span className={`text-xs font-semibold ${badge.color}`}>
                  {rawValue?.toFixed(2) || '-'}
                </span>
              </div>
            )
          })}
        </div>
      )}

      {/* Active signal explanation */}
      {activeSignal && (
        <div className="mt-2 p-2 bg-blue-50 rounded-lg border border-blue-100">
          <p className="text-xs text-blue-800">
            {SIGNAL_METADATA[activeSignal].description}
          </p>
        </div>
      )}
    </div>
  )
}

// Z-score badge helper
function getZScoreBadge(value) {
  if (value === null || value === undefined) return { color: 'text-gray-400' }
  if (value > 1.0) return { color: 'text-green-600' }
  if (value > 0.3) return { color: 'text-emerald-600' }
  if (value > -0.3) return { color: 'text-gray-600' }
  if (value > -1.0) return { color: 'text-orange-600' }
  return { color: 'text-red-600' }
}

// Custom tooltip with VEE-style explanations
function SignalTooltip({ active, payload }) {
  if (!active || !payload || payload.length === 0) return null

  const item = payload[0]?.payload
  const meta = SIGNAL_METADATA[item?.key]
  if (!meta) return null

  const rawValue = item.raw
  const interpretation = interpretZScore(rawValue, item.key)

  return (
    <div className="bg-white border border-gray-200 rounded-xl shadow-lg p-4 max-w-xs">
      <div className="flex items-center gap-2 mb-2">
        <meta.icon size={16} style={{ color: meta.color }} />
        <span className="text-sm font-semibold text-gray-900">{meta.label}</span>
      </div>
      
      <p className="text-xs text-gray-600 mb-3">
        {meta.description}
      </p>
      
      <div className="border-t border-gray-100 pt-2">
        <div className="flex justify-between items-center mb-1">
          <span className="text-xs text-gray-500">Z-Score</span>
          <span className={`text-sm font-bold ${getZScoreBadge(rawValue).color}`}>
            {rawValue?.toFixed(2) || '-'}
          </span>
        </div>
        <p className="text-xs text-gray-700 italic">
          {interpretation}
        </p>
      </div>
    </div>
  )
}

// Interpret z-score in natural language
function interpretZScore(value, signalKey) {
  if (value === null || value === undefined) return 'No data available'
  
  const signalName = SIGNAL_METADATA[signalKey]?.label || signalKey

  if (value > 1.5) return `Exceptionally strong ${signalName.toLowerCase()} — top performers`
  if (value > 1.0) return `Strong ${signalName.toLowerCase()} signal — above average`
  if (value > 0.3) return `Positive ${signalName.toLowerCase()} — slightly above baseline`
  if (value > -0.3) return `Neutral ${signalName.toLowerCase()} — near market average`
  if (value > -1.0) return `Weak ${signalName.toLowerCase()} — below average`
  return `Very weak ${signalName.toLowerCase()} — significant concern`
}

export { SignalRadarChart, SIGNAL_METADATA, normalizeZScore }
