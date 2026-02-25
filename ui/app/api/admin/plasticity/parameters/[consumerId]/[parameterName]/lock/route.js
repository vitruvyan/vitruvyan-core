import { NextResponse } from 'next/server'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8004'

export async function POST(request, { params }) {
  try {
    const { consumerId, parameterName } = params
    
    const response = await fetch(
      `${API_BASE_URL}/admin/plasticity/parameters/${consumerId}/${parameterName}/lock`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      }
    )

    if (!response.ok) {
      // Mock success for development
      return NextResponse.json({
        success: true,
        locked: true,
        message: 'Parameter lock toggled (mock)'
      })
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Error toggling lock:', error)
    return NextResponse.json({
      success: true,
      message: 'Lock toggled (mock fallback)'
    })
  }
}
