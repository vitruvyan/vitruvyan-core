// response/AllocationWeightsTable.jsx
'use client'

import { TrendingUp, Shield, Target } from 'lucide-react'

export function AllocationWeightsTable({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="text-gray-500 text-sm text-center py-4">
        No allocation data available
      </div>
    )
  }

  const getInsightIcon = (insight) => {
    if (insight.includes('momentum')) return <TrendingUp size={14} className="text-green-600" />
    if (insight.includes('stable')) return <Shield size={14} className="text-blue-600" />
    return <Target size={14} className="text-gray-600" />
  }

  const getInsightColor = (insight) => {
    if (insight.includes('Highest') || insight.includes('Strong')) return 'text-green-700'
    if (insight.includes('Most') || insight.includes('Solid')) return 'text-blue-700'
    return 'text-gray-700'
  }

  return (
    <div className="space-y-3">
      {data.map((row, index) => (
        <div key={row.ticker} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center gap-3">
            <div className="font-medium text-gray-900 min-w-[60px]">
              {row.ticker}
            </div>
            <div className="flex items-center gap-2">
              {getInsightIcon(row.insight)}
              <span className={`text-sm ${getInsightColor(row.insight)}`}>
                {row.insight}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-20 bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${Math.min(row.weight, 100)}%` }}
              />
            </div>
            <span className="text-sm font-medium text-gray-900 min-w-[45px] text-right">
              {row.weight}%
            </span>
          </div>
        </div>
      ))}
    </div>
  )
}