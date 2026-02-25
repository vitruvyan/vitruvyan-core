/**
 * RISK-REWARD SCATTER PLOT
 * X = Volatility (risk)
 * Y = Composite Score (reward)
 * Size = Momentum, Color = Sentiment
 * Shows classic 4-quadrant financial analysis
 */

'use client'

import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, ReferenceLine } from 'recharts'

export default function RiskRewardScatter({ data, className = '' }) {
  // data format: [{ticker, composite, vola_z, momentum_z, sentiment_z}, ...]

  // Prepare scatter data
  const scatterData = data.map(d => ({
    ticker: d.ticker,
    x: d.vola_z || 0, // Risk (volatility)
    y: d.composite || 0, // Reward (composite)
    z: Math.abs(d.momentum_z || 0) * 100 + 50, // Bubble size (50-250)
    sentiment: d.sentiment_z || 0
  }))

  // Color by sentiment
  const getSentimentColor = (sentiment) => {
    if (sentiment > 0.5) return '#10b981' // green
    if (sentiment > 0) return '#3b82f6'   // blue
    if (sentiment > -0.5) return '#f59e0b' // amber
    return '#ef4444' // red
  }

  // Custom tooltip
  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload || payload.length === 0) return null
    
    const data = payload[0].payload
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-3 shadow-lg text-xs">
        <div className="font-bold text-gray-900 mb-1">{data.ticker}</div>
        <div className="space-y-1 text-gray-600">
          <div>Composite: <span className="font-semibold">{data.y.toFixed(2)}</span></div>
          <div>Risk: <span className="font-semibold">{data.x.toFixed(2)}</span></div>
          <div>Sentiment: <span className="font-semibold">{data.sentiment.toFixed(2)}</span></div>
        </div>
      </div>
    )
  }

  return (
    <div className={`bg-white border border-gray-200 rounded-lg p-4 ${className}`}>
      <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
        🧭 Risk-Reward Analysis
      </h4>

      <ResponsiveContainer width="100%" height={350}>
        <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis 
            type="number" 
            dataKey="x" 
            name="Risk" 
            domain={[-2, 2]}
            label={{ value: 'Risk (Volatility) →', position: 'bottom', fill: '#6b7280' }}
            stroke="#6b7280"
          />
          <YAxis 
            type="number" 
            dataKey="y" 
            name="Reward" 
            domain={[-2, 2]}
            label={{ value: '↑ Reward (Composite)', angle: -90, position: 'left', fill: '#6b7280' }}
            stroke="#6b7280"
          />
          <Tooltip content={<CustomTooltip />} />
          
          {/* Quadrant dividers */}
          <ReferenceLine x={0} stroke="#9ca3af" strokeDasharray="3 3" />
          <ReferenceLine y={0} stroke="#9ca3af" strokeDasharray="3 3" />

          <Scatter data={scatterData} fill="#3b82f6">
            {scatterData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getSentimentColor(entry.sentiment)} />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>

      {/* Quadrant Labels */}
      <div className="grid grid-cols-2 gap-3 mt-3 text-xs">
        <div className="bg-green-50 border border-green-200 p-2 rounded text-center">
          <div className="font-semibold text-green-800">🎯 Top-Left</div>
          <div className="text-green-600">Low Risk, High Return</div>
        </div>
        <div className="bg-yellow-50 border border-yellow-200 p-2 rounded text-center">
          <div className="font-semibold text-yellow-800">⚡ Top-Right</div>
          <div className="text-yellow-600">High Risk, High Return</div>
        </div>
        <div className="bg-gray-50 border border-gray-200 p-2 rounded text-center">
          <div className="font-semibold text-gray-800">😐 Bottom-Left</div>
          <div className="text-gray-600">Low Risk, Low Return</div>
        </div>
        <div className="bg-red-50 border border-red-200 p-2 rounded text-center">
          <div className="font-semibold text-red-800">⚠️ Bottom-Right</div>
          <div className="text-red-600">High Risk, Low Return</div>
        </div>
      </div>

      {/* Legend */}
      <div className="mt-3 pt-3 border-t border-gray-100 text-xs text-gray-600">
        <div className="flex items-center gap-4">
          <span>Bubble size = Momentum strength</span>
          <span>•</span>
          <span>Color = Sentiment (🟢 positive, 🔴 negative)</span>
        </div>
      </div>
    </div>
  )
}
