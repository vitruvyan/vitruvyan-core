// hooks/useTradingOrder.js
// Feb 4, 2026 - Trading Order Hook
// 
// Custom hook for order execution with state management
// Separates business logic from UI components
//
// GOLDEN RULE: Trading logic MUST live in hooks, NOT in components
// - Reusability across Chat, /trading page, mobile app
// - Testability (mock-friendly)
// - Separation of concerns (UI vs business logic)

'use client'

import { useState, useCallback } from 'react'

export function useTradingOrder() {
  const [orderState, setOrderState] = useState('idle') // idle, executing, success, error
  const [lastOrder, setLastOrder] = useState(null)
  const [error, setError] = useState(null)

  /**
   * Execute a trading order (buy/sell)
   * 
   * @param {Object} orderData - Order details
   * @param {string} orderData.ticker - Stock ticker symbol
   * @param {string} orderData.side - 'buy' or 'sell'
   * @param {number} orderData.quantity - Number of shares
   * @param {number} orderData.price - Current price (for display)
   * @param {string} orderData.user_id - User ID (optional, extracted from JWT)
   * 
   * @returns {Promise<Object>} { success: boolean, order?: Object, error?: string }
   */
  const executeOrder = useCallback(async (orderData) => {
    const { ticker, side, quantity, price } = orderData
    
    setOrderState('executing')
    setError(null)
    
    try {
      // Get Keycloak token from localStorage
      const keycloakUser = JSON.parse(localStorage.getItem('keycloak_user') || '{}')
      const token = keycloakUser.token
      
      if (!token) {
        throw new Error('Authentication required. Please login.')
      }
      
      console.log('[useTradingOrder] Executing order:', orderData)
      
      // Call trading API with Authorization header
      const response = await fetch('/api/trading/order', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          ticker,
          side,
          quantity,
          user_id: orderData.user_id // Optional, backend extracts from JWT
        }),
        credentials: 'include'
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Unknown error')
      }
      
      const result = await response.json()
      console.log('[useTradingOrder] Order executed successfully:', result)
      
      // Build order result object
      const orderResult = {
        ticker,
        side,
        quantity,
        price: result.execution_price || price,
        total: result.total_cost || (quantity * price),
        orderId: result.order_id,
        timestamp: new Date().toISOString(),
        remainingCash: result.remaining_cash
      }
      
      setLastOrder(orderResult)
      setOrderState('success')
      
      return { success: true, order: orderResult }
      
    } catch (err) {
      console.error('[useTradingOrder] Order execution failed:', err)
      setError(err.message)
      setOrderState('error')
      return { success: false, error: err.message }
    }
  }, [])
  
  /**
   * Reset order state (after closing success/error modal)
   */
  const resetOrder = useCallback(() => {
    setOrderState('idle')
    setLastOrder(null)
    setError(null)
  }, [])

  return {
    // Actions
    executeOrder,
    resetOrder,
    
    // State
    orderState,    // 'idle' | 'executing' | 'success' | 'error'
    lastOrder,     // Last executed order details (or null)
    error,         // Error message (or null)
    
    // Computed
    isExecuting: orderState === 'executing',
    isSuccess: orderState === 'success',
    isError: orderState === 'error'
  }
}
