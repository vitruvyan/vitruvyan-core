import { useState, useCallback } from 'react'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || ""

export function useTickerSearch() {
  const [isSearching, setIsSearching] = useState(false)
  const [searchResults, setSearchResults] = useState([])
  
  const searchTickers = useCallback(async (query) => {
    if (!query || query.length < 1) {
      setSearchResults([])
      return []
    }
    
    setIsSearching(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/tickers/search?q=${encodeURIComponent(query)}`)
      if (!response.ok) throw new Error('Search failed')
      const data = await response.json()
      setSearchResults(data.results || [])
      return data.results || []
    } catch (error) {
      console.error("[TickerSearch] API error:", error)
      setSearchResults([])
      return []
    } finally {
      setIsSearching(false)
    }
  }, [])
  
  const validateTicker = useCallback(async (ticker) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/tickers/search?q=${ticker}`)
      if (!response.ok) return false
      const data = await response.json()
      return data.results?.some(r => r.ticker === ticker.toUpperCase())
    } catch {
      return false
    }
  }, [])
  
  return {
    searchTickers,
    validateTicker,
    searchResults,
    isSearching
  }
}