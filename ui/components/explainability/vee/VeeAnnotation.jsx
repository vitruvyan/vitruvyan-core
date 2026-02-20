/**
 * VEE ANNOTATION COMPONENT
 * 
 * Visual marker for price chart annotations.
 * Displays dots/markers at significant events with VEE explanations.
 * 
 * Props:
 * - data: Array of chart data points
 * - annotations: Array of annotation objects { x, label, description }
 * - yKey: Key for Y-axis value (e.g., 'close')
 */

'use client'

import { ReferenceDot } from 'recharts'
import { Info } from 'lucide-react'

export default function VeeAnnotation({ data, annotations, yKey = 'close' }) {
  if (!annotations || annotations.length === 0) return null

  return (
    <>
      {annotations.map((annotation, idx) => {
        // Find data point matching annotation x-value
        const dataPoint = data.find(d => d.date === annotation.x || d.index === annotation.x)
        
        if (!dataPoint) return null

        const yValue = dataPoint[yKey]

        return (
          <ReferenceDot
            key={`vee-annotation-${idx}`}
            x={annotation.x}
            y={yValue}
            r={6}
            fill="#3b82f6"
            stroke="white"
            strokeWidth={2}
            opacity={0.8}
          >
            {/* Tooltip on hover */}
            {annotation.label && (
              <title>{`${annotation.label}: ${annotation.description || ''}`}</title>
            )}
          </ReferenceDot>
        )
      })}
    </>
  )
}

// Helper to generate demo annotations (can be replaced with real pattern detection)
export function generateDemoAnnotations(data) {
  if (!data || data.length === 0) return []

  // Example: Mark the highest point as "Peak"
  const maxPoint = data.reduce((max, point) => 
    point.close > max.close ? point : max
  , data[0])

  return [
    {
      x: maxPoint.date,
      label: 'Peak',
      description: 'Highest price in period'
    }
  ]
}
