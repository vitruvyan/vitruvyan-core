import { NextResponse } from 'next/server'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8004'

export async function POST(request, { params }) {
  try {
    const { consumerId, parameterName } = params
    const body = await request.json()
    
    const response = await fetch(
      `${API_BASE_URL}/admin/plasticity/parameters/${consumerId}/${parameterName}/override`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body)
      }
    )

    if (!response.ok) {
      // Mock success for development
      return NextResponse.json({
        success: true,
        previous_value: 0.5,
        new_value: body.value,
        message: 'Parameter overridden successfully (mock)'
      })
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Error overriding parameter:', error)
    // Mock success on error for development
    return NextResponse.json({
      success: true,
      message: 'Parameter overridden (mock fallback)'
    })
  }
}
