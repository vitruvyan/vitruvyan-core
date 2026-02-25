/**
 * CANDLESTICK CHART COMPONENT
 * 
 * Displays historical price data with:
 * - Candlestick bodies (custom renderer)
 * - Volume bars
 * - SMA 20/50 overlays
 * 
 * Data Source: GET /api/chart/{ticker}?days=90
 * 
 * Props:
 * - ticker: Stock symbol (AAPL, NVDA, etc.)
 * - days: Historical period (default 90)
 * - className: Additional CSS classes
 */

'use client'

import { useState, useEffect } from 'react'
import { ComposedChart, Bar, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend, Cell } from 'recharts'
import { TrendingUp, TrendingDown, Loader2 } from 'lucide-react'
import VeeLayer from '@/components/explainability/vee/VeeLayer'
import { VeeChartTooltip } from '@/components/explainability/tooltips/TooltipLibrary'
import VeeAnnotation, { generateDemoAnnotations } from '@/components/explainability/vee/VeeAnnotation'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || ""

export default function CandlestickChart({ ticker, days = 90, explainability, className = '' }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const timestamp = new Date().toISOString()
    // [DEV] console.log(`[CandlestickChart ${timestamp}] Component mounted/updated`, { ticker, days, API_BASE_URL })
    
    if (!ticker) {
      console.warn(`[CandlestickChart ${timestamp}] No ticker provided, skipping fetch`)
      return
    }

    async function fetchChartData() {
      const fetchTimestamp = new Date().toISOString()
      const url = `${API_BASE_URL}/api/chart/${ticker}?days=${days}&interval=1d`
      // [DEV] console.log(`[CandlestickChart ${fetchTimestamp}] Fetching data from:`, url)
      
      try {
        setLoading(true)
        setError(null)

        const response = await fetch(url)
        // [DEV] console.log(`[CandlestickChart ${fetchTimestamp}] Response status:`, response.status, response.statusText)

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }

        const result = await response.json()
        // [DEV] log removed

        if (result.status === 'error') {
          throw new Error(result.message || 'Unknown error')
        }

        // [DEV] log removed
        setData(result.data)
        // [DEV] log removed
      } catch (err) {
        console.error(`[CandlestickChart ${fetchTimestamp}] ❌ ERROR:`, err)
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchChartData()
  }, [ticker, days])

  // Calculate min/max for Y-axis domain
  const getDomain = () => {
    if (!data || data.length === 0) return [0, 100]
    
    const prices = data.flatMap(d => [d.low, d.high])
    const min = Math.min(...prices)
    const max = Math.max(...prices)
    const padding = (max - min) * 0.1
    
    return [Math.floor(min - padding), Math.ceil(max + padding)]
  }

  // Custom Candlestick Shape
  const Candlestick = (props) => {
    const { x, y, width, height, payload } = props
    
    if (!payload || !payload.open || !payload.close) return null

    const isGreen = payload.close >= payload.open
    const color = isGreen ? '#10b981' : '#ef4444' // green-500 : red-500
    
    // Calculate dimensions
    const bodyTop = Math.min(payload.open, payload.close)
    const bodyBottom = Math.max(payload.open, payload.close)
    const bodyHeight = Math.abs(payload.close - payload.open)
    
    // Normalize to chart coordinates (Y-axis inverted)
    const [yMin, yMax] = getDomain()
    const yScale = height / (yMax - yMin)
    
    const wickY = (yMax - payload.high) * yScale + y
    const wickHeight = (payload.high - payload.low) * yScale
    const bodyY = (yMax - bodyBottom) * yScale + y
    const bodyHeightPx = bodyHeight * yScale || 1 // Min 1px for doji

    return (
      <g>
        {/* Wick (high-low line) */}
        <line
          x1={x + width / 2}
          y1={wickY}
          x2={x + width / 2}
          y2={wickY + wickHeight}
          stroke={color}
          strokeWidth={1}
        />
        
        {/* Body (open-close rectangle) */}
        <rect
          x={x + width * 0.2}
          y={bodyY}
          width={width * 0.6}
          height={bodyHeightPx}
          fill={color}
          stroke={color}
          strokeWidth={1}
        />
      </g>
    )
  }

  // Custom Tooltip with contextual interpretation
  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload || payload.length === 0) return null

    const data = payload[0].payload
    const isGreen = data.close >= data.open
    const change = ((data.close - data.open) / data.open * 100).toFixed(1)
    
    // Check position relative to SMAs
    const aboveSMA20 = data.sma_20 && data.close > data.sma_20
    const aboveSMA50 = data.sma_50 && data.close > data.sma_50

    return (
      <div className="bg-white border border-gray-200 rounded-lg p-3 shadow-lg max-w-xs">
        {/* Header with icon and interpretation */}
        <div className="flex items-center gap-2 mb-2">
          <span className="text-lg">{isGreen ? '📈' : '📉'}</span>
          <div>
            <p className="text-xs font-bold text-gray-900">{data.date}</p>
            <p className="text-xs font-medium" style={{color: isGreen ? '#10b981' : '#ef4444'}}>
              {isGreen ? 'Bullish' : 'Bearish'} day ({change > 0 ? '+' : ''}{change}%)
            </p>
          </div>
        </div>
        
        {/* OHLC Data */}
        <div className="space-y-1 text-xs text-gray-700">
          <div className="flex justify-between gap-3">
            <span>Open:</span>
            <span className="font-medium">${data.open.toFixed(2)}</span>
          </div>
          <div className="flex justify-between gap-3">
            <span>Close:</span>
            <span className="font-medium">${data.close.toFixed(2)}</span>
          </div>
          <div className="flex justify-between gap-3">
            <span>Range:</span>
            <span className="font-medium">${data.low.toFixed(2)} - ${data.high.toFixed(2)}</span>
          </div>
        </div>

        {/* SMA Context (if available) */}
        {(data.sma_20 || data.sma_50) && (
          <div className="mt-2 pt-2 border-t border-gray-100 text-xs">
            {data.sma_20 && (
              <p className={aboveSMA20 ? 'text-green-600' : 'text-red-600'}>
                {aboveSMA20 ? '↑' : '↓'} {Math.abs(((data.close - data.sma_20) / data.sma_20 * 100)).toFixed(1)}% vs 20-day MA
              </p>
            )}
            {data.sma_50 && (
              <p className={aboveSMA50 ? 'text-green-600' : 'text-red-600'}>
                {aboveSMA50 ? '↑' : '↓'} {Math.abs(((data.close - data.sma_50) / data.sma_50 * 100)).toFixed(1)}% vs 50-day MA
              </p>
            )}
          </div>
        )}
      </div>
    )
  }

  // Calculate price change
  const getPriceChange = () => {
    if (!data || data.length < 2) return null
    
    const firstClose = data[0].close
    const lastClose = data[data.length - 1].close
    const change = lastClose - firstClose
    const changePercent = (change / firstClose) * 100
    
    return {
      value: change.toFixed(2),
      percent: changePercent.toFixed(2),
      isPositive: change >= 0
    }
  }

  const priceChange = getPriceChange()

  // Render states
  if (loading) {
    return (
      <div className={`bg-white rounded-lg border border-gray-200 p-6 ${className}`}>
        <div className="flex items-center justify-center h-[400px]">
          <div className="text-center">
            <Loader2 className="h-8 w-8 animate-spin text-vitruvyan-accent mx-auto mb-3" />
            <p className="text-sm text-gray-600">Loading chart data...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`bg-white rounded-lg border border-red-200 p-6 ${className}`}>
        <div className="flex items-center justify-center h-[400px]">
          <div className="text-center">
            <div className="text-red-500 mb-2">⚠️</div>
            <p className="text-sm text-red-600">Error loading chart: {error}</p>
          </div>
        </div>
      </div>
    )
  }

  if (!data || data.length === 0) {
    return (
      <div className={`bg-white rounded-lg border border-gray-200 p-6 ${className}`}>
        <div className="flex items-center justify-center h-[400px]">
          <p className="text-sm text-gray-600">No data available for {ticker}</p>
        </div>
      </div>
    )
  }

  return (
    <div className={`bg-white rounded-lg border border-gray-200 p-4 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold text-gray-900">
            {ticker} Price History ({days} days)
          </h3>
          <p className="text-xs text-gray-500 mt-1">
            OHLC • {data.length} trading days
          </p>
        </div>
        
        {priceChange && (
          <div className={`flex items-center gap-2 px-3 py-1 rounded-lg ${
            priceChange.isPositive ? 'bg-green-50' : 'bg-red-50'
          }`}>
            {priceChange.isPositive ? (
              <TrendingUp size={16} className="text-green-600" />
            ) : (
              <TrendingDown size={16} className="text-red-600" />
            )}
            <div className="text-right">
              <div className={`text-sm font-semibold ${
                priceChange.isPositive ? 'text-green-600' : 'text-red-600'
              }`}>
                {priceChange.isPositive ? '+' : ''}{priceChange.value}
              </div>
              <div className={`text-xs ${
                priceChange.isPositive ? 'text-green-600' : 'text-red-600'
              }`}>
                {priceChange.isPositive ? '+' : ''}{priceChange.percent}%
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Chart */}
      <VeeLayer explainability={explainability} chartType="price">
        <ResponsiveContainer width="100%" height={400}>
          <ComposedChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
            <XAxis
              dataKey="date"
              tick={{ fill: '#6b7280', fontSize: 10 }}
              tickFormatter={(value) => {
                // Show only some labels to avoid crowding
                const date = new Date(value)
                return date.getDate() === 1 || date.getDay() === 1
                  ? `${date.getMonth() + 1}/${date.getDate()}`
                  : ''
              }}
            />
            <YAxis
              domain={getDomain()}
              tick={{ fill: '#6b7280', fontSize: 11 }}
              tickFormatter={(value) => `$${value}`}
              width={60}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ fontSize: '12px' }}
              iconType="line"
            />
            
            {/* SMA Lines */}
            <Line
              type="monotone"
              dataKey="sma_20"
              stroke="#f59e0b"
              strokeWidth={1.5}
              dot={false}
              name="SMA 20"
            />
            <Line
              type="monotone"
              dataKey="sma_50"
              stroke="#3b82f6"
              strokeWidth={1.5}
              dot={false}
              name="SMA 50"
            />
            
            {/* Candlesticks - Using Bar with custom shape */}
            <Bar
              dataKey="close"
              shape={<Candlestick />}
              name="Price"
            />
            
            {/* VEE Annotations */}
            {explainability && (
              <VeeAnnotation 
                data={data} 
                annotations={generateDemoAnnotations(data)} 
                yKey="close" 
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </VeeLayer>

      {/* Volume Chart (below main chart) */}
      <ResponsiveContainer width="100%" height={80} className="mt-4">
        <ComposedChart data={data} margin={{ top: 0, right: 10, left: 0, bottom: 0 }}>
          <XAxis dataKey="date" hide />
          <YAxis hide />
          <Tooltip
            formatter={(value) => `${(value / 1000000).toFixed(1)}M`}
            labelFormatter={(label) => `Volume on ${label}`}
          />
          <Bar dataKey="volume" name="Volume">
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.close >= entry.open ? '#10b98120' : '#ef444420'}
              />
            ))}
          </Bar>
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}

// Custom VEE Tooltip for Price Chart
function CustomVeeTooltip({ active, payload, label, explainability }) {
  if (!active || !payload || !explainability) {
    // Fallback to default tooltip
    if (active && payload) {
      const data = payload[0]?.payload
      if (!data) return null
      
      return (
        <div className="bg-white border border-gray-200 rounded-lg shadow-md p-3 text-xs">
          <p className="font-semibold text-gray-900 mb-2">{label}</p>
          <div className="space-y-1">
            <p><span className="text-gray-600">Open:</span> <span className="font-semibold">${data.open}</span></p>
            <p><span className="text-gray-600">High:</span> <span className="font-semibold text-green-600">${data.high}</span></p>
            <p><span className="text-gray-600">Low:</span> <span className="font-semibold text-red-600">${data.low}</span></p>
            <p><span className="text-gray-600">Close:</span> <span className="font-semibold">${data.close}</span></p>
          </div>
        </div>
      )
    }
    return null
  }

  return (
    <VeeChartTooltip
      active={active}
      payload={payload}
      label={label}
      simple={explainability.simple}
      technical={explainability.technical}
    />
  )
}
