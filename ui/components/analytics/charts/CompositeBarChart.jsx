/**
 * COMPOSITE BAR CHART - Horizontal ranking visualization
 * Shows composite scores as horizontal bars with colors
 * Used in: Screening (2-4), Portfolio (5+)
 */

'use client'

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, ResponsiveContainer } from 'recharts'

export default function CompositeBarChart({ data, className = '' }) {
  // data format: [{ticker: 'NVDA', composite: 1.85}, ...]
  
  // Sort by composite desc
  const sortedData = [...data].sort((a, b) => b.composite - a.composite)

  // Color scale function
  const getBarColor = (value) => {
    if (value > 0.8) return '#10b981' // green-500
    if (value > 0.4) return '#3b82f6' // blue-500
    if (value > 0) return '#6366f1'   // indigo-500
    if (value > -0.4) return '#f59e0b' // amber-500
    return '#ef4444' // red-500
  }

  return (
    <div className={`bg-white border border-gray-200 rounded-lg p-4 ${className}`}>
      <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
        📊 Composite Score Ranking
      </h4>
      
      <ResponsiveContainer width="100%" height={Math.max(200, data.length * 50)}>
        <BarChart data={sortedData} layout="vertical" margin={{ top: 5, right: 30, left: 60, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis type="number" domain={[-2, 2]} stroke="#6b7280" />
          <YAxis type="category" dataKey="ticker" stroke="#6b7280" />
          <Tooltip 
            formatter={(value) => value.toFixed(2)}
            contentStyle={{ backgroundColor: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: '6px' }}
          />
          <Bar dataKey="composite" radius={[0, 4, 4, 0]}>
            {sortedData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getBarColor(entry.composite)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Quick Stats */}
      <div className="mt-3 pt-3 border-t border-gray-100 flex justify-between text-xs text-gray-600">
        <div>
          <span className="font-semibold text-green-600">Leader:</span> {sortedData[0]?.ticker} ({sortedData[0]?.composite.toFixed(2)})
        </div>
        <div>
          <span className="font-semibold text-gray-500">Average:</span> {(sortedData.reduce((sum, d) => sum + d.composite, 0) / sortedData.length).toFixed(2)}
        </div>
      </div>
    </div>
  )
}
