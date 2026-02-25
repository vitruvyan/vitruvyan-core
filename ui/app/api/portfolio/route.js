/**
 * Portfolio API Route - PROXY TO BACKEND
 * 
 * NEVER access PostgreSQL directly from frontend (Vercel build fails).
 * Uses backend endpoint: http://161.97.140.157:8004/api/portfolio
 * 
 * Usage:
 *   GET /api/portfolio?user_id=default_user
 *   
 * Response:
 *   { tickers: ["AAPL", "MSFT", "TSLA"], source: "backend" }
 */

import { NextResponse } from 'next/server'

const BACKEND_API = process.env.NEXT_PUBLIC_API_URL || 'http://161.97.140.157:8004'

export async function GET(request) {
  try {
    const { searchParams } = new URL(request.url)
    const userId = searchParams.get('user_id') || 'default_user'
    
    console.log('[Portfolio API Proxy] Fetching portfolio for user:', userId)
    
    // Proxy to backend API
    const response = await fetch(`${BACKEND_API}/api/portfolio?user_id=${userId}`, {
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    if (!response.ok) {
      console.error('[Portfolio API Proxy] Backend error:', response.status)
      return NextResponse.json({ 
        tickers: [], 
        source: 'empty',
        error: `Backend returned ${response.status}`
      }, { status: response.status })
    }
    
    const data = await response.json()
    console.log('[Portfolio API Proxy] Received from backend:', data)
    
    return NextResponse.json(data)
  } catch (error) {
    console.error('[Portfolio API Proxy] Error:', error)
    return NextResponse.json({ 
      tickers: [], 
      source: 'error',
      error: error.message 
    }, { status: 500 })
  }
}
