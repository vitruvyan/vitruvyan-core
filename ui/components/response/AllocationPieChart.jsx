// response/AllocationPieChart.jsx
'use client'

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts'
import { TrendingUp, Activity, BarChart2, MessageCircle } from 'lucide-react'

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4', '#84CC16', '#F97316']

export function AllocationPieChart({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="text-gray-500 text-sm text-center py-8">
        No allocation data available
      </div>
    )
  }

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <div className="font-medium text-gray-900 mb-2">{data.name}</div>
          <div className="space-y-1 text-sm">
            <div className="flex justify-between gap-4">
              <span className="text-gray-600">Weight:</span>
              <span className="font-medium">{data.value}%</span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-gray-600">Composite:</span>
              <span className="font-medium">{data.composite?.toFixed(2) || 'N/A'}</span>
            </div>
            <div className="flex items-center gap-2">
              <TrendingUp size={12} className="text-gray-500" />
              <span className="text-gray-600">Momentum:</span>
              <span className="font-medium">{data.momentum?.toFixed(2) || 'N/A'}</span>
            </div>
            <div className="flex items-center gap-2">
              <Activity size={12} className="text-gray-500" />
              <span className="text-gray-600">Volatility:</span>
              <span className="font-medium">{data.volatility?.toFixed(2) || 'N/A'}</span>
            </div>
            <div className="flex items-center gap-2">
              <MessageCircle size={12} className="text-gray-500" />
              <span className="text-gray-600">Sentiment:</span>
              <span className="font-medium">{data.sentiment?.toFixed(2) || 'N/A'}</span>
            </div>
          </div>
        </div>
      )
    }
    return null
  }

  const renderCustomizedLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }) => {
    if (percent < 0.05) return null // Don't show labels for slices < 5%

    const RADIAN = Math.PI / 180
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5
    const x = cx + radius * Math.cos(-midAngle * RADIAN)
    const y = cy + radius * Math.sin(-midAngle * RADIAN)

    return (
      <text
        x={x}
        y={y}
        fill="white"
        textAnchor={x > cx ? 'start' : 'end'}
        dominantBaseline="central"
        fontSize={12}
        fontWeight="bold"
      >
        {`${(percent * 100).toFixed(0)}%`}
      </text>
    )
  }

  return (
    <div className="w-full">
      <div className="h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={renderCustomizedLabel}
              outerRadius={100}
              fill="#8884d8"
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
          </PieChart>
        </ResponsiveContainer>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap justify-center gap-4 mt-4">
        {data.map((entry, index) => (
          <div key={entry.name} className="flex items-center gap-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: COLORS[index % COLORS.length] }}
            />
            <span className="text-sm font-medium text-gray-700">
              {entry.name} ({entry.value}%)
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}