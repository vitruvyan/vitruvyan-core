// app/api/portfolio/cash/route.js
// Feb 2, 2026 - User Cash Balance API
// Proxy to LangGraph backend (has PostgreSQL access)

import { NextResponse } from 'next/server'

export async function GET(request) {
  try {
    // Call LangGraph portfolio endpoint
    const LANGGRAPH_URL = process.env.LANGGRAPH_API_URL || 'http://vitruvyan_api_graph:8004'
    
    const response = await fetch(`${LANGGRAPH_URL}/portfolio/cash`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': 'dbaldoni' // TODO: Extract from Keycloak token
      }
    })

    if (response.ok) {
      const data = await response.json()
      return NextResponse.json(data)
    }

    // Fallback: return mock data
    return NextResponse.json({
      user_id: 'dbaldoni',
      cash_available: 100000.00,
      starting_capital: 100000.00,
      source: 'mock'
    })

  } catch (error) {
    console.error('[Portfolio Cash API] Error:', error)
    
    // Fallback: return mock data for development
    return NextResponse.json({
      user_id: 'dbaldoni',
      cash_available: 100000.00,
      starting_capital: 100000.00,
      source: 'mock'
    })
  }
}

