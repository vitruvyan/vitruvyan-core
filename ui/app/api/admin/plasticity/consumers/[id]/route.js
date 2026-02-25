import { NextResponse } from 'next/server'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8004'

// Mock data for development
const MOCK_CONSUMERS = {
  'NarrativeEngine': {
    name: 'NarrativeEngine',
    health: 0.78,
    last_adjustment: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2h ago
    parameters: [
      {
        name: 'confidence_threshold',
        description: 'Minimum confidence score required for narrative generation',
        value: 0.652,
        bounds: { min: 0.1, max: 0.9 },
        locked: false
      },
      {
        name: 'temperature',
        description: 'LLM temperature for narrative creativity',
        value: 0.421,
        bounds: { min: 0.0, max: 1.0 },
        locked: false
      },
      {
        name: 'context_window',
        description: 'Number of previous messages for context',
        value: 0.725,
        bounds: { min: 0.3, max: 0.95 },
        locked: true
      }
    ]
  },
  'RiskGuardian': {
    name: 'RiskGuardian',
    health: 0.95,
    last_adjustment: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(), // 1d ago
    parameters: [
      {
        name: 'threshold',
        description: 'Risk alert threshold for portfolio concentration',
        value: 0.589,
        bounds: { min: 0.2, max: 0.8 },
        locked: false
      },
      {
        name: 'lookback_window',
        description: 'Historical data lookback period (normalized)',
        value: 0.843,
        bounds: { min: 0.5, max: 1.0 },
        locked: false
      }
    ]
  },
  'OrthodoxyWarden': {
    name: 'OrthodoxyWarden',
    health: 0.91,
    last_adjustment: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(), // 6h ago
    parameters: [
      {
        name: 'validation_strictness',
        description: 'Strictness level for epistemic validation',
        value: 0.714,
        bounds: { min: 0.4, max: 0.95 },
        locked: false
      }
    ]
  }
}

export async function GET(request, { params }) {
  try {
    const { id } = params
    
    // TODO: Forward JWT token from request headers
    // const token = request.headers.get('authorization')
    
    const response = await fetch(`${API_BASE_URL}/admin/plasticity/consumers/${id}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        // 'Authorization': token || ''
      }
    })

    if (!response.ok) {
      // Return mock data for development
      const mockData = MOCK_CONSUMERS[id]
      if (!mockData) {
        return NextResponse.json(
          { error: 'Consumer not found' },
          { status: 404 }
        )
      }
      return NextResponse.json(mockData)
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Error fetching consumer detail:', error)
    
    // Fallback to mock data
    const mockData = MOCK_CONSUMERS[params.id]
    if (mockData) {
      return NextResponse.json(mockData)
    }
    
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
