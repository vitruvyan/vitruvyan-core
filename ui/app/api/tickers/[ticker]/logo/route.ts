/**
 * TICKER LOGO API ENDPOINT - PROXY TO BACKEND
 * 
 * NEVER access PostgreSQL directly from frontend (Vercel build fails).
 * Uses backend endpoint: http://161.97.140.157:8004/api/tickers/[ticker]/logo
 * 
 * GET /api/tickers/[ticker]/logo - Get cached logo URL
 */

import { NextRequest, NextResponse } from 'next/server'

const BACKEND_API = process.env.NEXT_PUBLIC_API_URL || 'http://161.97.140.157:8004'

export async function GET(
  request: NextRequest,
  { params }: { params: { ticker: string } }
) {
  const ticker = params.ticker.toUpperCase()

  try {
    const response = await fetch(`${BACKEND_API}/api/tickers/${ticker}/logo`)
    
    if (!response.ok) {
      return NextResponse.json(
        { error: 'Ticker not found or backend error' },
        { status: response.status }
      )
    }
    
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('[API /tickers/[ticker]/logo Proxy] Error:', error)
    return NextResponse.json(
      { error: 'Backend unreachable' },
      { status: 500 }
    )
  }
}
