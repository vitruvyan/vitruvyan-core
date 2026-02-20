import React from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { TrendingUp, TrendingDown, Activity } from 'lucide-react'

/**
 * PerformanceChart — Portfolio vs Benchmark (30D)
 * TIER 2: Medium artifact component
 * 
 * Features:
 * - Time-series chart (30 days)
 * - Portfolio value vs SPY benchmark
 * - Performance metrics (return, max drawdown)
 * - Responsive design
 */

export default function PerformanceChart({ data, portfolioValue, benchmarkReturn }) {
  // Mock data for demo (replace with real API data)
  const mockData = data || generateMockPerformanceData(portfolioValue)
  
  const totalReturn = calculateTotalReturn(mockData)
  const maxDrawdown = calculateMaxDrawdown(mockData)
  const sharpeRatio = 1.42 // Mock value
  
  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-cyan-50">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Activity className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Performance (30 Days)</h3>
              <p className="text-sm text-gray-600">Portfolio vs SPY Benchmark</p>
            </div>
          </div>
          
          {/* Total Return Badge */}
          <div className={`px-4 py-2 rounded-lg ${totalReturn >= 0 ? 'bg-green-100' : 'bg-red-100'}`}>
            <div className="flex items-center space-x-2">
              {totalReturn >= 0 ? (
                <TrendingUp className="w-5 h-5 text-green-600" />
              ) : (
                <TrendingDown className="w-5 h-5 text-red-600" />
              )}
              <span className={`text-lg font-bold ${totalReturn >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                {totalReturn >= 0 ? '+' : ''}{totalReturn.toFixed(2)}%
              </span>
            </div>
            <p className="text-xs text-gray-600 text-center mt-1">Total Return</p>
          </div>
        </div>
      </div>
      
      {/* Chart */}
      <div className="p-6">
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={mockData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis 
              dataKey="date" 
              stroke="#6b7280"
              style={{ fontSize: '12px' }}
              tickFormatter={(value) => {
                const date = new Date(value)
                return `${date.getMonth() + 1}/${date.getDate()}`
              }}
            />
            <YAxis 
              stroke="#6b7280"
              style={{ fontSize: '12px' }}
              tickFormatter={(value) => `$${(value / 1000).toFixed(0)}K`}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend 
              wrapperStyle={{ paddingTop: '20px' }}
              iconType="line"
            />
            <Line 
              type="monotone" 
              dataKey="portfolio" 
              stroke="#10b981" 
              strokeWidth={3}
              dot={false}
              name="Portfolio"
              activeDot={{ r: 6 }}
            />
            <Line 
              type="monotone" 
              dataKey="benchmark" 
              stroke="#3b82f6" 
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={false}
              name="SPY (Benchmark)"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      
      {/* Metrics Footer */}
      <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center">
            <p className="text-sm text-gray-600">Total Return</p>
            <p className={`text-lg font-bold ${totalReturn >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {totalReturn >= 0 ? '+' : ''}{totalReturn.toFixed(2)}%
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-600">Max Drawdown</p>
            <p className="text-lg font-bold text-orange-600">
              {maxDrawdown.toFixed(2)}%
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-600">Sharpe Ratio</p>
            <p className="text-lg font-bold text-blue-600">
              {sharpeRatio.toFixed(2)}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

// Custom Tooltip Component
function CustomTooltip({ active, payload, label }) {
  if (!active || !payload || payload.length === 0) return null
  
  const portfolioValue = payload[0]?.value || 0
  const benchmarkValue = payload[1]?.value || 0
  const difference = portfolioValue - benchmarkValue
  const differencePercent = ((difference / benchmarkValue) * 100).toFixed(2)
  
  return (
    <div className="bg-white border border-gray-300 rounded-lg shadow-lg p-4">
      <p className="text-sm font-semibold text-gray-700 mb-2">
        {new Date(label).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
      </p>
      <div className="space-y-1">
        <div className="flex items-center justify-between space-x-4">
          <span className="text-sm text-gray-600 flex items-center">
            <span className="w-3 h-3 bg-green-500 rounded-full mr-2"></span>
            Portfolio:
          </span>
          <span className="text-sm font-bold text-gray-900">
            ${portfolioValue.toLocaleString()}
          </span>
        </div>
        <div className="flex items-center justify-between space-x-4">
          <span className="text-sm text-gray-600 flex items-center">
            <span className="w-3 h-3 bg-blue-500 rounded-full mr-2"></span>
            Benchmark:
          </span>
          <span className="text-sm font-bold text-gray-900">
            ${benchmarkValue.toLocaleString()}
          </span>
        </div>
        <div className="pt-2 mt-2 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Difference:</span>
            <span className={`text-sm font-bold ${difference >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {difference >= 0 ? '+' : ''}${difference.toLocaleString()} ({differencePercent}%)
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

// Mock Data Generator (replace with real API)
function generateMockPerformanceData(currentValue = 45230) {
  const data = []
  const startDate = new Date()
  startDate.setDate(startDate.getDate() - 30)
  
  let portfolioValue = currentValue * 0.92 // Start at 92% of current value
  let benchmarkValue = currentValue * 0.95 // Benchmark starts higher
  
  for (let i = 0; i <= 30; i++) {
    const date = new Date(startDate)
    date.setDate(date.getDate() + i)
    
    // Simulate portfolio volatility (higher than benchmark)
    const portfolioDelta = (Math.random() - 0.48) * 800 // Slightly positive drift
    portfolioValue = Math.max(portfolioValue + portfolioDelta, currentValue * 0.85)
    
    // Simulate benchmark (lower volatility)
    const benchmarkDelta = (Math.random() - 0.5) * 300
    benchmarkValue = Math.max(benchmarkValue + benchmarkDelta, currentValue * 0.90)
    
    data.push({
      date: date.toISOString(),
      portfolio: Math.round(portfolioValue),
      benchmark: Math.round(benchmarkValue)
    })
  }
  
  // Ensure last value matches current portfolio value
  data[data.length - 1].portfolio = currentValue
  
  return data
}

// Calculate Total Return
function calculateTotalReturn(data) {
  if (!data || data.length === 0) return 0
  const initial = data[0].portfolio
  const final = data[data.length - 1].portfolio
  return ((final - initial) / initial) * 100
}

// Calculate Max Drawdown
function calculateMaxDrawdown(data) {
  if (!data || data.length === 0) return 0
  
  let peak = data[0].portfolio
  let maxDrawdown = 0
  
  data.forEach(point => {
    if (point.portfolio > peak) {
      peak = point.portfolio
    }
    const drawdown = ((peak - point.portfolio) / peak) * 100
    if (drawdown > maxDrawdown) {
      maxDrawdown = drawdown
    }
  })
  
  return maxDrawdown
}
