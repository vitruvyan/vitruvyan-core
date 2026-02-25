/**
 * NormalizedPerformanceChart.jsx
 * 
 * Normalized line chart for comparing price performance across 2-3 tickers.
 * All tickers start at baseline 100, showing relative performance over time.
 * NO candlesticks - only clean line chart with multiple timeframes.
 * 
 * PHASE 5 of Comparison UX refactoring (Dec 19, 2025)
 */

import React, { useState, useMemo } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { TrendingUp, Calendar } from 'lucide-react'
import { Badge } from '@/components/ui/badge'

/**
 * NormalizedPerformanceChart
 * 
 * @param {Array} tickers - Array of ticker objects from numericalPanel
 * @param {string} veeNarrative - Optional VEE unified narrative for performance
 * @param {string} className - Optional CSS classes
 */
const NormalizedPerformanceChart = ({ tickers = [], veeNarrative, className = '' }) => {
  const [timeframe, setTimeframe] = useState('3M') // Default: 3 months

  if (!tickers || tickers.length === 0) {
    return null
  }

  /**
   * Color palette for tickers (max 3 tickers)
   */
  const tickerColors = [
    '#8B5CF6', // Purple
    '#10B981', // Green
    '#F59E0B', // Orange
  ]

  /**
   * Timeframe configurations
   */
  const timeframes = [
    { label: '1M', value: '1M', days: 30 },
    { label: '3M', value: '3M', days: 90 },
    { label: '6M', value: '6M', days: 180 },
    { label: '1Y', value: '1Y', days: 365 },
  ]

  /**
   * Generate mock normalized performance data
   * In production, this would come from historical price API
   * 
   * Format: [{date: '2024-12-01', AAPL: 100, NVDA: 100}, {date: '2024-12-02', AAPL: 102, NVDA: 98}, ...]
   */
  const generateNormalizedData = useMemo(() => {
    const selectedTimeframe = timeframes.find(tf => tf.value === timeframe)
    const days = selectedTimeframe?.days || 90
    
    // Generate date range
    const data = []
    const today = new Date()
    
    for (let i = days; i >= 0; i--) {
      const date = new Date(today)
      date.setDate(date.getDate() - i)
      
      const dataPoint = {
        date: date.toISOString().split('T')[0], // YYYY-MM-DD
      }
      
      // Generate normalized performance for each ticker
      // Starting at 100, add random walk (mock data)
      tickers.forEach((ticker, index) => {
        const momentum_z = ticker.momentum_z || 0
        const trend_z = ticker.trend_z || 0
        
        // Mock: use z-scores to simulate performance trajectory
        // Higher momentum/trend = upward trajectory
        const baseGrowth = ((momentum_z + trend_z) / 2) * 0.005 // ~0.5% per day for z=1
        const randomWalk = (Math.random() - 0.5) * 0.02 // ±1% daily volatility
        
        const progressRatio = (days - i) / days
        const cumulativeReturn = 100 * (1 + (baseGrowth + randomWalk) * progressRatio * days)
        
        dataPoint[ticker.ticker] = parseFloat(cumulativeReturn.toFixed(2))
      })
      
      data.push(dataPoint)
    }
    
    return data
  }, [tickers, timeframe])

  /**
   * Calculate performance metrics (final vs initial)
   */
  const performanceMetrics = useMemo(() => {
    if (generateNormalizedData.length === 0) return []
    
    const initial = generateNormalizedData[0]
    const final = generateNormalizedData[generateNormalizedData.length - 1]
    
    return tickers.map((ticker) => {
      const initialValue = initial[ticker.ticker]
      const finalValue = final[ticker.ticker]
      const change = finalValue - initialValue
      const changePercent = ((finalValue / initialValue) - 1) * 100
      
      return {
        ticker: ticker.ticker,
        initial: initialValue,
        final: finalValue,
        change: change,
        changePercent: changePercent,
        isPositive: change >= 0
      }
    })
  }, [generateNormalizedData, tickers])

  /**
   * Custom tooltip for chart
   */
  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload) return null
    
    return (
      <div className="bg-white border border-gray-300 rounded-lg shadow-lg p-3">
        <p className="text-xs font-semibold text-gray-700 mb-2">{label}</p>
        {payload.map((entry, index) => (
          <div key={index} className="flex items-center justify-between gap-3 text-xs">
            <span style={{ color: entry.color }} className="font-medium">
              {entry.name}:
            </span>
            <span className="font-semibold text-gray-900">
              {entry.value.toFixed(2)}
            </span>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className={`bg-white rounded-lg border border-gray-200 p-4 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-purple-600" />
          <h3 className="text-sm font-semibold text-gray-900">Normalized Performance</h3>
          <Badge variant="outline" className="text-xs">
            Baseline 100
          </Badge>
        </div>
        
        {/* Timeframe Selector */}
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-gray-500" />
          <div className="flex gap-1">
            {timeframes.map((tf) => (
              <button
                key={tf.value}
                onClick={() => setTimeframe(tf.value)}
                className={`px-3 py-1 text-xs font-medium rounded transition-colors ${
                  timeframe === tf.value
                    ? 'bg-purple-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {tf.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="mb-4">
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={generateNormalizedData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
            <XAxis 
              dataKey="date" 
              tick={{ fontSize: 11, fill: '#6B7280' }}
              tickFormatter={(value) => {
                // Format: "Dec 1" or "12/1"
                const date = new Date(value)
                return `${date.getMonth() + 1}/${date.getDate()}`
              }}
            />
            <YAxis 
              tick={{ fontSize: 11, fill: '#6B7280' }}
              domain={['auto', 'auto']}
              label={{ value: 'Normalized (100 = start)', angle: -90, position: 'insideLeft', fontSize: 11, fill: '#6B7280' }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend 
              wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }}
              iconType="line"
            />
            {tickers.map((ticker, index) => (
              <Line
                key={ticker.ticker}
                type="monotone"
                dataKey={ticker.ticker}
                stroke={tickerColors[index]}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Performance Summary Table */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
        {performanceMetrics.map((metric, index) => (
          <div 
            key={metric.ticker}
            className="bg-gray-50 rounded-lg p-3 border border-gray-200"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-semibold text-gray-900">{metric.ticker}</span>
              <Badge 
                className={`${
                  metric.isPositive 
                    ? 'bg-green-500 text-white' 
                    : 'bg-red-500 text-white'
                } text-xs px-2 py-0.5`}
              >
                {metric.isPositive ? '+' : ''}{metric.changePercent.toFixed(1)}%
              </Badge>
            </div>
            <div className="flex items-center gap-2">
              <div 
                className="w-3 h-3 rounded-full" 
                style={{ backgroundColor: tickerColors[index] }}
              ></div>
              <span className="text-xs text-gray-600">
                {metric.initial.toFixed(2)} → {metric.final.toFixed(2)}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* VEE Narrative (if provided) */}
      {veeNarrative && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-4 h-4 text-blue-600" />
            <h4 className="text-sm font-semibold text-blue-900">Performance Analysis</h4>
          </div>
          <p className="text-sm text-gray-700 leading-relaxed">{veeNarrative}</p>
        </div>
      )}

      {/* Auto-generated comparison text (if VEE not provided) */}
      {!veeNarrative && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <p className="text-sm text-gray-700 leading-relaxed">
            Normalized performance comparison over <strong>{timeframe}</strong> timeframe. 
            All tickers start at baseline 100. <strong>{performanceMetrics[0]?.ticker}</strong>{' '}
            {performanceMetrics[0]?.isPositive ? 'gained' : 'lost'}{' '}
            <strong>{Math.abs(performanceMetrics[0]?.changePercent || 0).toFixed(1)}%</strong>
            {performanceMetrics.length > 1 && (
              <>
                , while <strong>{performanceMetrics[1]?.ticker}</strong>{' '}
                {performanceMetrics[1]?.isPositive ? 'gained' : 'lost'}{' '}
                <strong>{Math.abs(performanceMetrics[1]?.changePercent || 0).toFixed(1)}%</strong>
              </>
            )}
            .
          </p>
        </div>
      )}
    </div>
  )
}

export default NormalizedPerformanceChart
