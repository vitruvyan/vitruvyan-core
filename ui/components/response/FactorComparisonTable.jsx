// components/response/FactorComparisonTable.jsx
import React, { useState } from 'react'
import { ArrowUp, ArrowDown, Minus, Info } from 'lucide-react'

const FactorComparisonTable = ({ factorComparison, winnerTicker, loserTicker }) => {
  const [tooltipVisible, setTooltipVisible] = useState(null)

  // VEE tooltips for factors
  const factorTooltips = {
    Momentum: 'Short-term price acceleration (RSI, MACD, rate-of-change). Positive momentum signals buying pressure.',
    Trend: 'Long-term directional strength (SMA, EMA, Bollinger Bands). Strong trend indicates sustained movement.',
    Volatility: 'Price stability measured by ATR. Lower volatility = lower risk, but also lower potential returns.',
    Sentiment: 'Market consensus from news and social media (FinBERT). Positive sentiment = favorable market perception.',
    Fundamentals: 'Financial health (revenue growth, EPS, margins, FCF, P/E ratio). Strong fundamentals = solid business.'
  }
  // ✅ NULL-SAFE: Validate inputs
  if (!factorComparison || !factorComparison.factors || !Array.isArray(factorComparison.factors)) {
    return (
      <div className="border border-yellow-200 bg-yellow-50 rounded-lg p-4 text-center">
        <p className="text-sm text-yellow-800">⚠️ Factor comparison data not available</p>
      </div>
    )
  }

  const { factors, keyDifferentiator } = factorComparison

  // Get signal icon based on delta
  const getSignalIcon = (delta) => {
    if (delta > 0.3) return <ArrowUp className="w-5 h-5 text-green-600" />
    if (delta < -0.3) return <ArrowDown className="w-5 h-5 text-red-600" />
    return <Minus className="w-5 h-5 text-gray-400" />
  }

  // Get cell styling based on value
  const getCellStyle = (value) => {
    if (value > 1.0) return 'bg-green-100 text-green-800 font-semibold'
    if (value > 0.5) return 'bg-blue-50 text-blue-700'
    if (value > 0) return 'bg-gray-50 text-gray-700'
    if (value < -1.0) return 'bg-red-100 text-red-800 font-semibold'
    if (value < -0.5) return 'bg-orange-50 text-orange-700'
    return 'bg-gray-50 text-gray-600'
  }

  // Highlight key differentiator row
  const isKeyDifferentiator = (factor) => factor === keyDifferentiator

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden bg-white">
      <table className="w-full">
        <thead className="bg-gray-100">
          <tr>
            <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Factor</th>
            <th className="px-4 py-3 text-center text-sm font-semibold text-gray-700">{winnerTicker}</th>
            <th className="px-4 py-3 text-center text-sm font-semibold text-gray-700">{loserTicker}</th>
            <th className="px-4 py-3 text-center text-sm font-semibold text-gray-700">Δ</th>
            <th className="px-4 py-3 text-center text-sm font-semibold text-gray-700">Leader</th>
          </tr>
        </thead>
        <tbody>
          {factors.map((f, idx) => (
            <tr
              key={f.factor}
              className={`
                border-t border-gray-200
                ${isKeyDifferentiator(f.factor) ? 'bg-yellow-50 border-yellow-200' : ''}
                ${idx % 2 === 0 ? 'bg-gray-50' : 'bg-white'}
              `}
            >
              {/* Factor Name with VEE Tooltip */}
              <td className="px-4 py-3 text-sm font-medium text-gray-900">
                <div className="flex items-center gap-2">
                  <span>{f.factor}</span>
                  {factorTooltips[f.factor] && (
                    <div className="relative inline-block">
                      <Info
                        className="w-4 h-4 text-blue-500 cursor-help"
                        onMouseEnter={() => setTooltipVisible(f.factor)}
                        onMouseLeave={() => setTooltipVisible(null)}
                      />
                      {tooltipVisible === f.factor && (
                        <div className="absolute z-50 left-0 top-6 w-64 bg-white border border-gray-300 rounded-lg shadow-lg p-3 text-xs text-gray-700 leading-relaxed">
                          {factorTooltips[f.factor]}
                          <div className="absolute -top-2 left-4 w-3 h-3 bg-white border-l border-t border-gray-300 transform rotate-45"></div>
                        </div>
                      )}
                    </div>
                  )}
                  {isKeyDifferentiator(f.factor) && (
                    <span className="text-xs text-yellow-600">🔑 Key</span>
                  )}
                </div>
              </td>

              {/* Winner Value */}
              <td className={`px-4 py-3 text-center text-sm font-mono ${getCellStyle(f.winner)}`}>
                {f.winner?.toFixed(2)}
              </td>

              {/* Loser Value */}
              <td className={`px-4 py-3 text-center text-sm font-mono ${getCellStyle(f.loser)}`}>
                {f.loser?.toFixed(2)}
              </td>

              {/* Delta */}
              <td className="px-4 py-3 text-center text-sm font-mono font-semibold">
                {f.delta > 0 ? '+' : ''}{f.delta?.toFixed(2)}
              </td>

              {/* Leader Icon */}
              <td className="px-4 py-3 text-center">
                {getSignalIcon(f.delta)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Legend */}
      <div className="bg-gray-50 px-4 py-3 border-t border-gray-200 flex items-center gap-4 text-xs text-gray-600">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-green-100 border border-green-200 rounded"></div>
          <span>Strong (&gt;1.0)</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-blue-50 border border-blue-200 rounded"></div>
          <span>Good (&gt;0.5)</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-gray-50 border border-gray-200 rounded"></div>
          <span>Neutral</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-red-100 border border-red-200 rounded"></div>
          <span>Weak (&lt;-1.0)</span>
        </div>
      </div>
    </div>
  )
}

export default FactorComparisonTable
