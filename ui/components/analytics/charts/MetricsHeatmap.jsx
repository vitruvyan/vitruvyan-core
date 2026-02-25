/**
 * METRICS HEATMAP - Factor analysis grid
 * Shows momentum, trend, volatility, sentiment as colored cells
 * Color: red → yellow → green (z-score normalized)
 */

'use client'

export default function MetricsHeatmap({ data, className = '' }) {
  // data format: [{ticker, momentum_z, trend_z, vola_z, sentiment_z}, ...]

  // Color scale: z-score → hue
  const getHeatColor = (value) => {
    if (value > 1.0) return 'bg-green-500 text-white'
    if (value > 0.5) return 'bg-green-400 text-white'
    if (value > 0.2) return 'bg-green-300 text-gray-900'
    if (value > -0.2) return 'bg-yellow-300 text-gray-900'
    if (value > -0.5) return 'bg-orange-400 text-white'
    if (value > -1.0) return 'bg-red-400 text-white'
    return 'bg-red-500 text-white'
  }

  const getEmoji = (value) => {
    if (value > 1.0) return '🟩'
    if (value > 0.5) return '🟨'
    if (value > 0) return '🟧'
    return '🟥'
  }

  const metrics = [
    { key: 'momentum_z', label: 'Momentum' },
    { key: 'trend_z', label: 'Trend' },
    { key: 'vola_z', label: 'Volatility' },
    { key: 'sentiment_z', label: 'Sentiment' },
    { key: 'dividend_yield_z', label: 'Dividend', icon: '🎁' }
  ]

  return (
    <div className={`bg-white border border-gray-200 rounded-lg overflow-hidden ${className}`}>
      <div className="bg-gradient-to-r from-purple-50 to-pink-50 px-4 py-3 border-b border-gray-200">
        <h4 className="font-semibold text-gray-900 flex items-center gap-2">
          🌈 Factor Heatmap
        </h4>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-4 py-3 text-left font-semibold text-gray-700 sticky left-0 bg-gray-50">Ticker</th>
              {metrics.map(m => (
                <th key={m.key} className="px-4 py-3 text-center font-semibold text-gray-700">
                  {m.icon && <span className="mr-1">{m.icon}</span>}
                  {m.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {data.map((row) => (
              <tr key={row.ticker} className="hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3 font-bold text-gray-900 sticky left-0 bg-white">
                  {row.ticker}
                </td>
                {metrics.map(m => {
                  const value = row[m.key] || 0
                  return (
                    <td key={m.key} className="px-2 py-2 text-center">
                      <div className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-md font-semibold text-xs ${getHeatColor(value)}`}>
                        <span>{getEmoji(value)}</span>
                        <span>{value >= 0 ? '+' : ''}{value.toFixed(2)}</span>
                      </div>
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="bg-gray-50 px-4 py-3 border-t border-gray-200">
        <div className="flex flex-wrap gap-3 text-xs text-gray-600">
          <div className="flex items-center gap-1">
            <span className="inline-block w-4 h-4 bg-green-500 rounded"></span>
            <span>&gt; 1.0 (Strong)</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="inline-block w-4 h-4 bg-yellow-300 rounded"></span>
            <span>±0.2 (Neutral)</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="inline-block w-4 h-4 bg-red-500 rounded"></span>
            <span>&lt; -1.0 (Weak)</span>
          </div>
        </div>
      </div>
    </div>
  )
}
