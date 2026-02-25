/**
 * HOOK: useTickerNames
 * 
 * Fetches company names from PostgreSQL for given tickers
 * Uses direct database query (not via backend API)
 */

import { useState, useEffect } from 'react'

export default function useTickerNames(tickers) {
  const [tickerNames, setTickerNames] = useState({})
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!tickers || tickers.length === 0) {
      setTickerNames({})
      return
    }

    const fetchNames = async () => {
      setLoading(true)
      try {
        // Call Next.js API route that queries PostgreSQL
        const response = await fetch('/api/ticker-names', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ tickers })
        })

        if (response.ok) {
          const data = await response.json()
          setTickerNames(data.tickerNames || {})
        } else {
          console.warn('Failed to fetch ticker names:', response.statusText)
          setTickerNames({})
        }
      } catch (error) {
        console.error('Error fetching ticker names:', error)
        setTickerNames({})
      } finally {
        setLoading(false)
      }
    }

    fetchNames()
  }, [JSON.stringify(tickers)]) // Re-fetch when tickers change

  return { tickerNames, loading }
}
