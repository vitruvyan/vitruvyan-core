/**
 * usePortfolioCanvas Hook
 * 
 * State management for portfolio banner canvas overlay.
 * Handles opening/closing state and portfolio data fetching.
 * 
 * Created: January 20, 2026
 */

import { useState, useEffect, useCallback } from 'react'

export function usePortfolioCanvas(userId) {
  const [isOpen, setIsOpen] = useState(false)
  const [portfolioData, setPortfolioData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [currentTicker, setCurrentTicker] = useState(null)

  const fetchPortfolioData = useCallback(async () => {
    console.log('[usePortfolioCanvas] fetchPortfolioData called, userId:', userId)
    
    if (!userId) {
      console.warn('[usePortfolioCanvas] No userId, cannot fetch')
      setError('User ID required')
      return
    }

    setLoading(true)
    setError(null)

    try {
      // Get Keycloak token from localStorage (Feb 4, 2026)
      const keycloakUserStr = localStorage.getItem('keycloak_user')
      const token = keycloakUserStr ? JSON.parse(keycloakUserStr).token : null
      
      console.log('[usePortfolioCanvas] Token available:', !!token, 'userId:', userId)
      
      const headers = {
        'Content-Type': 'application/json'
      }
      
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }
      
      const url = `/api/portfolio/holdings/${userId}`
      console.log('[usePortfolioCanvas] Fetching:', url)
      
      const response = await fetch(url, { headers })
      
      console.log('[usePortfolioCanvas] Response status:', response.status)
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`)
      }

      const result = await response.json()
      console.log('[usePortfolioCanvas] API result:', result)
      console.log('[usePortfolioCanvas] Holdings count:', result.data?.holdings?.length || 0)
      
      setPortfolioData(result.data) // Extract data from wrapper
      console.log('[usePortfolioCanvas] portfolioData set successfully')
    } catch (err) {
      console.error('[usePortfolioCanvas] Fetch error:', err)
      setError(err.message)
      setPortfolioData(null)
    } finally {
      setLoading(false)
    }
  }, [userId])

  const openCanvas = useCallback(() => {
    console.log('[usePortfolioCanvas] openCanvas called, userId:', userId)
    setIsOpen(true)
    // Fetch fresh data when opening
    if (userId) {
      console.log('[usePortfolioCanvas] Fetching portfolio data on open')
      fetchPortfolioData()
    } else {
      console.warn('[usePortfolioCanvas] Cannot fetch, userId is null')
    }
  }, [userId, fetchPortfolioData])

  const closeCanvas = useCallback(() => {
    setIsOpen(false)
  }, [])

  const updateCurrentTicker = useCallback((ticker) => {
    setCurrentTicker(ticker)
  }, [])

  // Auto-fetch on mount if userId available
  useEffect(() => {
    console.log('[usePortfolioCanvas] Auto-fetch useEffect triggered:', { userId, hasPortfolioData: !!portfolioData })
    
    if (userId && !portfolioData) {
      console.log('[usePortfolioCanvas] Triggering auto-fetch')
      fetchPortfolioData()
    }
  }, [userId, portfolioData, fetchPortfolioData])

  // ESC key listener
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && isOpen) {
        closeCanvas()
      }
    }

    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [isOpen, closeCanvas])

  return {
    isOpen,
    portfolioData,
    loading,
    error,
    currentTicker,
    openCanvas,
    closeCanvas,
    updateCurrentTicker,
    refreshData: fetchPortfolioData
  }
}
