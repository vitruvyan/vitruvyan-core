import { NextResponse } from 'next/server'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8004'

export async function GET(request, { params }) {
  try {
    const { consumerId, parameterName } = params
    
    const response = await fetch(
      `${API_BASE_URL}/admin/plasticity/trajectories/${consumerId}/${parameterName}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      }
    )

    if (!response.ok) {
      // Return mock data for development
      return NextResponse.json({
        values: generateMockTrajectory(),
        bounds: { min: 0.1, max: 0.9 }
      })
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Error fetching trajectory:', error)
    // Return mock data on error
    return NextResponse.json({
      values: generateMockTrajectory(),
      bounds: { min: 0.1, max: 0.9 }
    })
  }
}

function generateMockTrajectory() {
  const now = Date.now()
  const points = []
  for (let i = 7; i >= 0; i--) {
    points.push({
      timestamp: new Date(now - i * 24 * 60 * 60 * 1000).toISOString(),
      value: 0.5 + (Math.random() - 0.5) * 0.3
    })
  }
  return points
}
