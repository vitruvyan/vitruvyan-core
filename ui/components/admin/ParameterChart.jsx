'use client'

import { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

export default function ParameterChart({ parameter, consumerId }) {
  const [trajectoryData, setTrajectoryData] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchTrajectory()
  }, [consumerId, parameter.name])

  const fetchTrajectory = async () => {
    setLoading(true)
    try {
      const response = await fetch(`/api/admin/plasticity/trajectories/${consumerId}/${parameter.name}`)
      const data = await response.json()
      
      // Format data for Recharts
      const formattedData = data.values.map(point => ({
        timestamp: new Date(point.timestamp).toLocaleTimeString('en-US', { 
          month: 'short', 
          day: 'numeric', 
          hour: '2-digit' 
        }),
        value: point.value,
        fullTimestamp: point.timestamp
      }))
      
      setTrajectoryData(formattedData)
    } catch (error) {
      console.error('Failed to fetch trajectory:', error)
      // Mock data fallback
      setTrajectoryData(generateMockTrajectory())
    } finally {
      setLoading(false)
    }
  }

  const generateMockTrajectory = () => {
    const now = Date.now()
    const points = []
    for (let i = 7; i >= 0; i--) {
      points.push({
        timestamp: new Date(now - i * 24 * 60 * 60 * 1000).toLocaleTimeString('en-US', { 
          month: 'short', 
          day: 'numeric' 
        }),
        value: parameter.value + (Math.random() - 0.5) * 0.1
      })
    }
    return points
  }

  const calculateTrend = () => {
    if (trajectoryData.length < 2) return 'stable'
    const first = trajectoryData[0].value
    const last = trajectoryData[trajectoryData.length - 1].value
    const change = ((last - first) / first) * 100
    
    if (change > 5) return 'up'
    if (change < -5) return 'down'
    return 'stable'
  }

  const getTrendIcon = () => {
    const trend = calculateTrend()
    if (trend === 'up') return <TrendingUp className="h-4 w-4 text-green-600" />
    if (trend === 'down') return <TrendingDown className="h-4 w-4 text-red-600" />
    return <Minus className="h-4 w-4 text-gray-600" />
  }

  if (loading) {
    return (
      <div className="border border-gray-200 rounded-lg p-4">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
          <div className="h-48 bg-gray-200 rounded"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="border border-gray-200 rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold text-gray-900">{parameter.name}</h3>
          <p className="text-xs text-gray-600">Current: {parameter.value.toFixed(3)}</p>
        </div>
        {getTrendIcon()}
      </div>

      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={trajectoryData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis 
            dataKey="timestamp" 
            tick={{ fontSize: 10 }}
            stroke="#9ca3af"
          />
          <YAxis 
            domain={[parameter.bounds.min, parameter.bounds.max]}
            tick={{ fontSize: 10 }}
            stroke="#9ca3af"
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: '#fff', 
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              fontSize: '12px'
            }}
            formatter={(value) => value.toFixed(4)}
          />
          
          {/* Bounds reference lines */}
          <ReferenceLine 
            y={parameter.bounds.max} 
            stroke="#f59e0b" 
            strokeDasharray="5 5" 
            label={{ value: 'Max', position: 'right', fontSize: 10 }}
          />
          <ReferenceLine 
            y={parameter.bounds.min} 
            stroke="#f59e0b" 
            strokeDasharray="5 5" 
            label={{ value: 'Min', position: 'right', fontSize: 10 }}
          />
          
          <Line 
            type="monotone" 
            dataKey="value" 
            stroke="#3b82f6" 
            strokeWidth={2}
            dot={{ fill: '#3b82f6', r: 3 }}
            activeDot={{ r: 5 }}
          />
        </LineChart>
      </ResponsiveContainer>

      <div className="mt-3 flex justify-between text-xs text-gray-600">
        <span>Min: {parameter.bounds.min.toFixed(2)}</span>
        <span>Max: {parameter.bounds.max.toFixed(2)}</span>
      </div>
    </div>
  )
}
