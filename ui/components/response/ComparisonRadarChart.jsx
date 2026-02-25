// components/response/ComparisonRadarChart.jsx
import React from 'react'
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Legend, ResponsiveContainer } from 'recharts'

const ComparisonRadarChart = ({ tickersData }) => {
  if (!tickersData || tickersData.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No data available for radar chart
      </div>
    )
  }

  // Transform data for Recharts Radar format
  // Expected: [{ factor: 'Momentum', AAPL: 0.86, NVDA: 1.23 }, ...]
  const factors = ['momentum', 'trend', 'volatility', 'sentiment']
  const radarData = factors.map(factor => {
    const dataPoint = { factor: factor.charAt(0).toUpperCase() + factor.slice(1) }
    
    tickersData.forEach(ticker => {
      dataPoint[ticker.ticker] = ticker.factors[factor] || 0
    })
    
    return dataPoint
  })

  // Generate colors for each ticker
  const colors = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6']

  return (
    <div className="border border-gray-200 rounded-lg p-6 bg-white">
      <ResponsiveContainer width="100%" height={400}>
        <RadarChart data={radarData}>
          <PolarGrid stroke="#e5e7eb" />
          <PolarAngleAxis 
            dataKey="factor" 
            tick={{ fill: '#6b7280', fontSize: 12 }}
          />
          <PolarRadiusAxis 
            angle={90} 
            domain={[-2, 2]}
            tick={{ fill: '#6b7280', fontSize: 10 }}
          />
          
          {tickersData.map((ticker, idx) => (
            <Radar
              key={ticker.ticker}
              name={ticker.ticker}
              dataKey={ticker.ticker}
              stroke={colors[idx % colors.length]}
              fill={colors[idx % colors.length]}
              fillOpacity={0.2}
              strokeWidth={2}
            />
          ))}
          
          <Legend 
            wrapperStyle={{ paddingTop: '20px' }}
            iconType="circle"
          />
        </RadarChart>
      </ResponsiveContainer>

      {/* VEE Tooltip: Chart Interpretation */}
      <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="flex items-start gap-2">
          <div className="text-blue-600 mt-0.5">💡</div>
          <div className="text-xs text-blue-900 space-y-1">
            <p className="font-semibold">How to read this chart:</p>
            <p><strong>Momentum:</strong> Short-term price acceleration (RSI, MACD)</p>
            <p><strong>Trend:</strong> Long-term directional strength (SMA, EMA)</p>
            <p><strong>Volatility:</strong> Price stability (ATR) - lower = safer</p>
            <p><strong>Sentiment:</strong> Market consensus from news/social media</p>
            <p className="mt-2 text-blue-700">⚡ Larger area = stronger overall positioning</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ComparisonRadarChart
