/**
 * MINI RADAR CHARTS - Multiple small radars in grid
 * Shows momentum, trend, volatility, sentiment as radar shape
 * Stile "Pokémon cards" - visual DNA of each ticker
 */

'use client'

import { RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts'

export default function MiniRadarGrid({ data, className = '' }) {
  // data format: [{ticker, momentum_z, trend_z, vola_z, sentiment_z}, ...]

  // Transform data for radar format
  const prepareRadarData = (row) => {
    // Normalize to 0-10 scale for visibility
    const normalize = (val) => Math.max(0, Math.min(10, (val + 2) * 2.5))
    
    return [
      { metric: 'Mom', value: normalize(row.momentum_z || 0) },
      { metric: 'Trd', value: normalize(row.trend_z || 0) },
      { metric: 'Vol', value: normalize(row.vola_z || 0) },
      { metric: 'Sen', value: normalize(row.sentiment_z || 0) },
      { metric: 'Div', value: normalize(row.dividend_yield_z || 0) }
    ]
  }

  // Get color based on average score (including dividend)
  const getCardColor = (row) => {
    const avg = (row.momentum_z + row.trend_z + (row.vola_z * -1) + row.sentiment_z + (row.dividend_yield_z || 0)) / 5
    if (avg > 0.8) return 'border-green-400 bg-green-50'
    if (avg > 0.4) return 'border-blue-400 bg-blue-50'
    if (avg > 0) return 'border-indigo-400 bg-indigo-50'
    if (avg > -0.4) return 'border-yellow-400 bg-yellow-50'
    return 'border-red-400 bg-red-50'
  }

  const getRadarColor = (row) => {
    const avg = (row.momentum_z + row.trend_z + (row.vola_z * -1) + row.sentiment_z + (row.dividend_yield_z || 0)) / 5
    if (avg > 0.5) return '#10b981'
    if (avg > 0) return '#3b82f6'
    return '#f59e0b'
  }

  return (
    <div className={className}>
      <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
        🕸️ Factor DNA (Mini-Radars)
      </h4>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
        {data.map((row) => {
          const radarData = prepareRadarData(row)
          const composite = row.composite || 0

          return (
            <div 
              key={row.ticker}
              className={`border-2 rounded-lg p-3 transition-all hover:shadow-lg ${getCardColor(row)}`}
            >
              {/* Header */}
              <div className="flex items-center justify-between mb-2">
                <div className="font-bold text-gray-900 text-sm">{row.ticker}</div>
                <div className={`text-xs font-semibold px-2 py-0.5 rounded ${
                  composite > 0.5 ? 'bg-green-500 text-white' :
                  composite < 0 ? 'bg-red-500 text-white' :
                  'bg-gray-500 text-white'
                }`}>
                  {composite.toFixed(2)}
                </div>
              </div>

              {/* Mini Radar */}
              <ResponsiveContainer width="100%" height={120}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="#d1d5db" />
                  <PolarAngleAxis 
                    dataKey="metric" 
                    tick={{ fill: '#6b7280', fontSize: 10 }}
                  />
                  <PolarRadiusAxis angle={90} domain={[0, 10]} tick={false} />
                  <Radar 
                    name={row.ticker}
                    dataKey="value" 
                    stroke={getRadarColor(row)}
                    fill={getRadarColor(row)}
                    fillOpacity={0.5}
                  />
                </RadarChart>
              </ResponsiveContainer>

              {/* Footer Stats */}
              <div className="mt-2 pt-2 border-t border-gray-200 grid grid-cols-2 gap-1 text-xs">
                <div className="text-gray-600">
                  <span className="font-semibold">Mom:</span> {(row.momentum_z || 0).toFixed(1)}
                </div>
                <div className="text-gray-600">
                  <span className="font-semibold">Trd:</span> {(row.trend_z || 0).toFixed(1)}
                </div>
                <div className="text-gray-600">
                  <span className="font-semibold">Vol:</span> {(row.vola_z || 0).toFixed(1)}
                </div>
                <div className="text-gray-600">
                  <span className="font-semibold">Sen:</span> {(row.sentiment_z || 0).toFixed(1)}
                </div>
                {row.dividend_yield_z !== undefined && (
                  <div className="text-gray-600 col-span-2">
                    <span className="font-semibold">🎁 Div:</span> {(row.dividend_yield_z || 0).toFixed(1)}
                  </div>
                )}
              </div>

              {/* Type Badge */}
              <div className="mt-2 text-center">
                <span className="text-xs px-2 py-0.5 bg-white bg-opacity-70 rounded-full text-gray-700">
                  {row.momentum_z > 1 && row.trend_z > 1 ? '🚀 Strong' :
                   Math.abs(row.vola_z) < 0.5 ? '🛡️ Stable' :
                   row.vola_z > 1 ? '⚡ Volatile' :
                   '😐 Mixed'}
                </span>
              </div>
            </div>
          )
        })}
      </div>

      {/* Legend */}
      <div className="mt-4 bg-gray-50 border border-gray-200 rounded-lg p-3 text-xs text-gray-600">
        <div className="font-semibold text-gray-700 mb-2">How to Read:</div>
        <ul className="space-y-1 list-disc list-inside">
          <li><strong>Large radar area</strong> = Well-balanced, strong on all metrics</li>
          <li><strong>Narrow/pointed</strong> = Specialized (strong on 1-2 metrics only)</li>
          <li><strong>Green border</strong> = Overall positive composite (&gt;0.8)</li>
          <li><strong>Red border</strong> = Weak or negative composite (&lt;-0.4)</li>
        </ul>
      </div>
    </div>
  )
}
