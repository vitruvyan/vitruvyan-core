/**
 * API Route: /api/ticker-names
 * 
 * Fetches company names for given tickers via backend API
 * 
 * ✅ VERCEL COMPATIBLE (Dec 12, 2025)
 * - Uses backend VPS API instead of localhost PostgreSQL
 * - Zero impact on ticker validation logic (validation uses /api/tickers/search directly)
 * - Only affects display of company names in UI badges
 */

import { NextResponse } from 'next/server'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://graph.vitruvyan.com'

export async function POST(request) {
  try {
    const { tickers } = await request.json()

    if (!tickers || !Array.isArray(tickers) || tickers.length === 0) {
      return NextResponse.json({ tickerNames: {} })
    }

    // 🔥 Fetch company names via backend API (Vercel-compatible)
    // Backend endpoint: GET /api/tickers/search?q={ticker}
    // Returns exact match when query is exact ticker symbol
    const tickerNames = {}
    
    await Promise.all(
      tickers.map(async (ticker) => {
        try {
          const response = await fetch(
            `${API_BASE_URL}/api/tickers/search?q=${encodeURIComponent(ticker)}`,
            {
              method: 'GET',
              headers: { 'Content-Type': 'application/json' },
            }
          )

          if (response.ok) {
            const data = await response.json()
            // Find exact ticker match (backend returns fuzzy results)
            const exactMatch = data.results?.find(r => r.ticker === ticker)
            if (exactMatch && exactMatch.name) {
              tickerNames[ticker] = exactMatch.name
            }
          }
        } catch (err) {
          console.warn(`Failed to fetch name for ${ticker}:`, err.message)
          // Continue with other tickers (non-blocking)
        }
      })
    )

    return NextResponse.json({ tickerNames })
  } catch (error) {
    console.error('Error fetching ticker names:', error)
    return NextResponse.json({ tickerNames: {}, error: error.message }, { status: 500 })
  }
}
