/**
 * 💵 ORDER ENTRY DIALOG - Shadow Trading UI
 * ==========================================
 * Modal dialog for executing shadow BUY/SELL orders.
 * 
 * Features:
 * - Real-time price display
 * - Total cost calculation
 * - Cash balance validation
 * - Order confirmation
 * - Slippage warning
 * 
 * Props:
 * - isOpen: boolean
 * - onClose: () => void
 * - ticker: string
 * - side: 'buy' | 'sell'
 * - currentPrice: number
 * - cashBalance: number
 * - currentPosition: number (shares owned, for sell validation)
 * - onOrderExecuted: (result) => void
 * 
 * Created: Jan 3, 2026
 */

import React, { useState, useEffect } from 'react'
import { X, TrendingUp, TrendingDown, AlertTriangle, DollarSign } from 'lucide-react'

export default function OrderEntryDialog({
  isOpen,
  onClose,
  ticker,
  side,
  currentPrice,
  cashBalance,
  currentPosition = 0,
  onOrderExecuted
}) {
  const [quantity, setQuantity] = useState(100)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState(null)

  // Calculate total cost with slippage estimate
  const slippageRate = quantity > 1000 ? 0.0015 : 0.0005 // 0.05% or 0.15%
  const priceWithSlippage = side === 'buy' 
    ? currentPrice * (1 + slippageRate)
    : currentPrice * (1 - slippageRate)
  const totalCost = quantity * priceWithSlippage

  // Validation
  const isValid = side === 'buy' 
    ? totalCost <= cashBalance && quantity > 0
    : quantity > 0 && quantity <= currentPosition

  useEffect(() => {
    if (!isOpen) {
      setQuantity(100)
      setError(null)
      setIsSubmitting(false)
    }
  }, [isOpen])

  const handleSubmit = async () => {
    setIsSubmitting(true)
    setError(null)

    try {
      const response = await fetch(`/api/shadow/${side}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: localStorage.getItem('user_id') || 'default_user',
          ticker,
          quantity,
          reason: 'Manual order via UI'
        })
      })

      const result = await response.json()

      if (result.status === 'filled') {
        onOrderExecuted(result)
        onClose()
      } else {
        setError(result.message || 'Order rejected')
      }
    } catch (err) {
      setError(`Order failed: ${err.message}`)
    } finally {
      setIsSubmitting(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold flex items-center gap-2">
            {side === 'buy' ? (
              <TrendingUp className="w-6 h-6 text-green-600" />
            ) : (
              <TrendingDown className="w-6 h-6 text-red-600" />
            )}
            <span className="capitalize">{side}</span> {ticker}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Current Price */}
        <div className="bg-gray-50 rounded-lg p-4 mb-4">
          <div className="text-sm text-gray-600 mb-1">Current Price</div>
          <div className="text-2xl font-bold text-gray-900">
            ${currentPrice.toFixed(2)}
          </div>
          {quantity > 1000 && (
            <div className="flex items-center gap-1 mt-2 text-xs text-orange-600">
              <AlertTriangle className="w-3 h-3" />
              Large order: +0.15% slippage estimated
            </div>
          )}
        </div>

        {/* Quantity Input */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Quantity (shares)
          </label>
          <input
            type="number"
            value={quantity}
            onChange={(e) => setQuantity(parseInt(e.target.value) || 0)}
            min="1"
            max={side === 'sell' ? currentPosition : undefined}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          {side === 'sell' && (
            <div className="text-xs text-gray-500 mt-1">
              You own {currentPosition} shares
            </div>
          )}
        </div>

        {/* Order Summary */}
        <div className="bg-blue-50 rounded-lg p-4 mb-4 space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-gray-700">Price (with slippage)</span>
            <span className="font-medium">${priceWithSlippage.toFixed(2)}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-700">Total {side === 'buy' ? 'Cost' : 'Proceeds'}</span>
            <span className="font-bold text-lg">
              ${totalCost.toFixed(2)}
            </span>
          </div>
          {side === 'buy' && (
            <div className="flex justify-between text-sm">
              <span className="text-gray-700">Cash Remaining</span>
              <span className={cashBalance - totalCost >= 0 ? 'text-green-600' : 'text-red-600'}>
                ${(cashBalance - totalCost).toFixed(2)}
              </span>
            </div>
          )}
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
            <div className="text-sm text-red-800">{error}</div>
          </div>
        )}

        {/* Validation Messages */}
        {!isValid && !error && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-4">
            <div className="text-sm text-yellow-800">
              {side === 'buy'
                ? 'Insufficient cash balance'
                : 'Not enough shares to sell'}
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={!isValid || isSubmitting}
            className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${
              side === 'buy'
                ? 'bg-green-600 hover:bg-green-700 text-white'
                : 'bg-red-600 hover:bg-red-700 text-white'
            } disabled:bg-gray-300 disabled:cursor-not-allowed`}
          >
            {isSubmitting ? 'Processing...' : `Confirm ${side.toUpperCase()}`}
          </button>
        </div>

        {/* Slippage Disclaimer */}
        <div className="mt-4 text-xs text-gray-500 text-center">
          Shadow trading simulates market orders with realistic slippage.
          No real money is involved.
        </div>
      </div>
    </div>
  )
}
