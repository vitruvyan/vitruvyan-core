/**
 * COMPOSITE SCORE GAUGE
 * 
 * Displays composite score as semicircle gauge (speedometer style).
 * 
 * Data Source: finalState.numerical_panel[0].composite_score
 * 
 * Score Ranges:
 * - 0-40: Red (Weak)
 * - 40-70: Yellow (Neutral)
 * - 70-100: Green (Strong)
 */

'use client'

import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts'
import { TrendingUp } from 'lucide-react'

export default function CompositeScoreGauge({ score, verdict, className = '' }) {
  // Guard: Don't render if no score
  if (score === null || score === undefined) return null

  // Convert 0-1 score to 0-100
  const percentage = score * 100

  // Gauge data (semicircle, 180 degrees)
  const gaugeData = [
    { value: percentage, color: getScoreColor(percentage) },
    { value: 100 - percentage, color: '#e5e7eb' }, // gray-200 for remaining
  ]

  // Needle angle (0-180 degrees)
  const needleAngle = (percentage / 100) * 180 - 90

  function getScoreColor(score) {
    if (score >= 70) return '#10b981' // green-500
    if (score >= 40) return '#f59e0b' // amber-500
    return '#ef4444' // red-500
  }

  function getScoreLabel(score) {
    if (score >= 70) return 'Strong'
    if (score >= 40) return 'Neutral'
    return 'Weak'
  }

  return (
    <div className={`bg-white rounded-lg border border-gray-200 p-4 ${className}`}>
      <h3 className="text-sm font-semibold text-gray-900 mb-2">Composite Score</h3>

      <div className="relative w-full" style={{ height: '200px' }}>
        {/* Gauge Chart */}
        <div className="absolute inset-0">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={gaugeData}
                cx="50%"
                cy="50%"
                startAngle={180}
                endAngle={0}
                innerRadius="45%"
                outerRadius="65%"
                paddingAngle={0}
                dataKey="value"
              >
                {gaugeData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Score Display - positioned below gauge arc */}
        <div className="absolute left-1/2 -translate-x-1/2 text-center" style={{ top: '65%' }}>
          <div className="text-5xl font-bold text-gray-900 leading-none mb-1">
            {percentage.toFixed(1)}%
          </div>
          <div 
            className="text-sm font-semibold"
            style={{ color: getScoreColor(percentage) }}
          >
            {getScoreLabel(percentage)}
          </div>
        </div>

        {/* Gauge scale markers */}
        <div className="absolute text-xs font-medium text-gray-500" style={{ left: '10%', top: '50%' }}>0</div>
        <div className="absolute text-xs font-medium text-gray-500 left-1/2 -translate-x-1/2" style={{ top: '8%' }}>50</div>
        <div className="absolute text-xs font-medium text-gray-500" style={{ right: '10%', top: '50%' }}>100</div>
      </div>

      {/* Verdict Badge */}
      {verdict && (
        <div className="mt-4 flex items-center justify-center gap-2 p-3 bg-gray-50 rounded-lg">
          <TrendingUp size={16} className="text-vitruvyan-accent" />
          <span className="text-sm font-semibold text-gray-900">
            Verdict: <span style={{ color: getScoreColor(percentage) }}>{verdict.label}</span>
          </span>
        </div>
      )}

      {/* Score Ranges Legend */}
      <div className="mt-4 grid grid-cols-3 gap-2 text-xs">
        <div className="text-center">
          <div className="w-full h-2 bg-red-500 rounded mb-1"></div>
          <span className="text-gray-600">0-40</span>
        </div>
        <div className="text-center">
          <div className="w-full h-2 bg-amber-500 rounded mb-1"></div>
          <span className="text-gray-600">40-70</span>
        </div>
        <div className="text-center">
          <div className="w-full h-2 bg-green-500 rounded mb-1"></div>
          <span className="text-gray-600">70-100</span>
        </div>
      </div>
    </div>
  )
}
