/**
 * API Route: /api/tickers/search
 * 
 * Search tickers via backend PostgreSQL (519 validated tickers).
 * Used by hero-landing.jsx autocomplete.
 * 
 * @param {string} q - Search query (e.g., "NV" → ["NVDA", "NVS"])
 * @returns {object} { status: "success", results: [{ticker, name, sector, match_score}] }
 */

export async function GET(request) {
  const { searchParams } = new URL(request.url)
  const query = searchParams.get('q')

  if (!query || query.length < 1) {
    return Response.json({ status: "success", results: [] })
  }

  try {
    // Call backend API for ticker search
    // Use localhost:8004 when running in dev mode (frontend outside Docker)
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8004'
    const response = await fetch(`${backendUrl}/api/tickers/search?q=${encodeURIComponent(query)}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    })

    if (!response.ok) {
      // If backend doesn't have this endpoint, fallback to direct PostgreSQL query
      // For now, return empty results
      console.warn(`[/api/tickers/search] Backend returned ${response.status}`)
      return Response.json({ status: "success", results: [] })
    }

    const data = await response.json()
    return Response.json(data)
  } catch (error) {
    console.error('[/api/tickers/search] Error:', error.message)
    return Response.json({ status: "error", results: [], error: error.message })
  }
}
