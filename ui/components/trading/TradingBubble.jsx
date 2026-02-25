// trading/TradingBubble.jsx
// Feb 1, 2026 - Minimal Trading UI (Chat-First Philosophy)
//
// FILOSOFIA: Vitruvyan ≠ IBKR (complessità)
// - 3 click: Buy → Adjust Quantity → Confirm
// - Solo Market order (instant execution)
// - NO charts, NO limit orders, NO risk calculators (per ora)
// - Bubble expansion pattern (consistent con PortfolioBanner)
//
// Target UX: Robinhood/Cash App, NOT IBKR
// - Semplice = Accessibile a tutti
// - Trading avanzato → Pagina /trading separata (futuro)

'use client'

import { useState, useEffect } from 'react'
import { X, TrendingUp, DollarSign, AlertCircle, CheckCircle } from 'lucide-react'

export function TradingBubble({
  ticker,
  currentPrice: initialPrice = 0,
  side, // 'buy' or 'sell'
  veeSimple, // VEE 1-sentence rationale
  userHolding = null,
  onConfirm,
  onClose,
  onViewPortfolio // NEW: Callback to open portfolio (Feb 4, 2026)
}) {
  const [quantity, setQuantity] = useState(1)
  const [isAnimating, setIsAnimating] = useState(false)
  const [currentPrice, setCurrentPrice] = useState(initialPrice)
  const [cashAvailable, setCashAvailable] = useState(null)
  const [loading, setLoading] = useState(true)
  
  // Order execution state (Feb 4, 2026)
  const [executionState, setExecutionState] = useState('form') // 'form', 'executing', 'success', 'error'
  const [orderResult, setOrderResult] = useState(null)
  
  // Advanced options state (Feb 3, 2026 - Progressive disclosure)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [orderType, setOrderType] = useState('market') // 'market' or 'limit'
  const [limitPrice, setLimitPrice] = useState('')
  const [stopLoss, setStopLoss] = useState('')
  const [takeProfit, setTakeProfit] = useState('')
  const [timeInForce, setTimeInForce] = useState('day') // 'day', 'gtc', 'ioc', 'fok'

  // Animate bubble entrance
  useEffect(() => {
    setTimeout(() => setIsAnimating(true), 10)
  }, [])

  // Fetch real-time price and cash available
  useEffect(() => {
    const fetchPriceAndCash = async () => {
      try {
        setLoading(true)
        
        // Fetch current price from backend
        console.log('[TradingBubble] Fetching price for:', ticker)
        const priceResponse = await fetch(`/api/ticker-price?ticker=${ticker}`)
        console.log('[TradingBubble] Price response status:', priceResponse.status)
        
        if (priceResponse.ok) {
          const priceData = await priceResponse.json()
          console.log('[TradingBubble] Price data:', priceData)
          
          if (priceData.price && priceData.price > 0) {
            setCurrentPrice(priceData.price)
          }
        }
        
        // Fetch user cash available
        console.log('[TradingBubble] Fetching cash...')
        const cashResponse = await fetch('/api/portfolio/cash')
        console.log('[TradingBubble] Cash response status:', cashResponse.status)
        
        if (cashResponse.ok) {
          const cashData = await cashResponse.json()
          console.log('[TradingBubble] Cash data:', cashData)
          setCashAvailable(cashData.cash_available)
        }
      } catch (error) {
        console.error('[TradingBubble] Fetch error:', error)
      } finally {
        setLoading(false)
      }
    }
    
    fetchPriceAndCash()
  }, [ticker])

  // Calculate totals
  const total = quantity * currentPrice
  const maxQuantity = side === 'sell' && userHolding ? userHolding.quantity : 100

  // Handle quantity change (slider)
  const handleQuantityChange = (e) => {
    setQuantity(parseInt(e.target.value))
  }

  // Handle confirm (Feb 4, 2026 - Updated with async result handling)
  const handleConfirm = async () => {
    setExecutionState('executing')
    
    // Build order payload with advanced options if set
    const orderPayload = {
      quantity,
      orderType,
      ...(orderType === 'limit' && limitPrice && { limitPrice: parseFloat(limitPrice) }),
      ...(stopLoss && { stopLoss: parseFloat(stopLoss) }),
      ...(takeProfit && { takeProfit: parseFloat(takeProfit) }),
      ...(showAdvanced && { timeInForce })
    }
    
    // Execute order (returns result)
    const result = await onConfirm(orderPayload)
    
    if (result && result.success) {
      setExecutionState('success')
      setOrderResult(result.order)
    } else {
      setExecutionState('error')
      setOrderResult({ error: result?.error || 'Unknown error' })
    }
  }

  return (
    <div
      className={`mt-4 overflow-hidden transition-all duration-500 ease-in-out ${
        isAnimating 
          ? showAdvanced 
            ? 'max-h-[2000px] opacity-100'  // Expanded with advanced options
            : 'max-h-[800px] opacity-100'    // Normal expanded
          : 'max-h-0 opacity-0'              // Collapsed
      }`}
    >
      <div className="bg-white border-2 border-blue-200 rounded-xl p-6 shadow-lg">
        
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
            {side === 'buy' ? (
              <>
                <TrendingUp size={20} className="text-green-600" />
                <span>Buy {ticker}</span>
              </>
            ) : (
              <>
                <DollarSign size={20} className="text-red-600" />
                <span>Sell {ticker}</span>
              </>
            )}
          </h3>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X size={18} className="text-gray-500" />
          </button>
        </div>

        {/* SUCCESS STATE (Feb 4, 2026) */}
        {executionState === 'success' && orderResult && (
          <div className="space-y-4">
            {/* Success Icon */}
            <div className="flex flex-col items-center justify-center py-6">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
                <CheckCircle size={32} className="text-green-600" />
              </div>
              <h4 className="text-xl font-bold text-gray-900 mb-2">
                ✅ Order Completed!
              </h4>
              <p className="text-sm text-gray-600 text-center">
                Your order has been executed successfully
              </p>
            </div>

            {/* Transaction Summary */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium text-gray-600">Transaction</span>
                <span className="text-base font-bold text-gray-900">
                  {side === 'buy' ? 'Bought' : 'Sold'} {orderResult.quantity} {orderResult.ticker}
                </span>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium text-gray-600">Price</span>
                <span className="text-base font-semibold text-gray-900">
                  ${orderResult.price?.toFixed(2)}
                </span>
              </div>
              
              <div className="flex justify-between items-center pt-2 border-t border-blue-300">
                <span className="text-sm font-bold text-gray-700">Total</span>
                <span className="text-lg font-bold text-gray-900">
                  ${orderResult.total?.toFixed(2)}
                </span>
              </div>
              
              {orderResult.remainingCash && (
                <div className="flex justify-between items-center pt-2 border-t border-blue-300">
                  <span className="text-sm font-medium text-gray-600">Remaining Cash</span>
                  <span className="text-base font-semibold text-green-600">
                    ${orderResult.remainingCash?.toFixed(2)}
                  </span>
                </div>
              )}
              
              <div className="text-xs text-gray-500 pt-2">
                Order ID: {orderResult.orderId?.slice(0, 8)}...
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-3">
              <button
                onClick={onClose}
                className="flex-1 px-4 py-3 rounded-lg font-semibold text-gray-700 bg-gray-100 hover:bg-gray-200 transition-colors"
              >
                Close
              </button>
              {onViewPortfolio && (
                <button
                  onClick={() => {
                    onViewPortfolio()
                    onClose()
                  }}
                  className="flex-1 px-4 py-3 rounded-lg font-semibold text-white bg-blue-600 hover:bg-blue-700 transition-all hover:scale-105"
                >
                  View Portfolio →
                </button>
              )}
            </div>
          </div>
        )}

        {/* ERROR STATE */}
        {executionState === 'error' && orderResult && (
          <div className="space-y-4">
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <AlertCircle size={24} className="text-red-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-bold text-red-900 mb-1">Order Failed</h4>
                  <p className="text-sm text-red-700">{orderResult.error}</p>
                </div>
              </div>
            </div>
            
            <div className="flex gap-3">
              <button
                onClick={onClose}
                className="flex-1 px-4 py-3 rounded-lg font-semibold text-gray-700 bg-gray-100 hover:bg-gray-200 transition-colors"
              >
                Close
              </button>
              <button
                onClick={() => setExecutionState('form')}
                className="flex-1 px-4 py-3 rounded-lg font-semibold text-white bg-blue-600 hover:bg-blue-700 transition-colors"
              >
                Try Again
              </button>
            </div>
          </div>
        )}

        {/* EXECUTING STATE */}
        {executionState === 'executing' && (
          <div className="flex flex-col items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
            <p className="text-sm font-medium text-gray-600">Executing order...</p>
          </div>
        )}

        {/* FORM STATE (default) */}
        {executionState === 'form' && (
          <>
        {/* Live Price */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-blue-700 font-medium">Current Price</span>
            <span className="text-xl font-bold text-blue-900">
              ${currentPrice.toFixed(2)}
            </span>
          </div>
          <div className="text-xs text-blue-600 mt-1">🔴 Live (Market order)</div>
        </div>

        {/* Quantity Input + Slider */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Quantity
          </label>
          
          {/* Manual Input */}
          <div className="flex items-center gap-3 mb-3">
            <input
              type="number"
              min="1"
              max={maxQuantity}
              value={quantity}
              onChange={(e) => {
                const val = parseInt(e.target.value) || 1
                setQuantity(Math.min(Math.max(val, 1), maxQuantity))
              }}
              className="w-24 px-3 py-2 text-2xl font-bold text-gray-900 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none text-center"
            />
            <span className="text-sm text-gray-500">
              shares (max {maxQuantity})
            </span>
          </div>
          
          {/* Slider (optional quick adjust) */}
          <input
            type="range"
            min="1"
            max={maxQuantity}
            value={quantity}
            onChange={handleQuantityChange}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
          />
        </div>

        {/* Total + Cash Available */}
        <div className="space-y-3 mb-4">
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-600">Total</span>
              <span className="text-2xl font-bold text-gray-900">
                ${total.toFixed(2)}
              </span>
            </div>
          </div>
          
          {/* Cash Available (dynamic update) */}
          {cashAvailable !== null && side === 'buy' && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <div className="flex items-center justify-between text-sm">
                <span className="text-blue-700 font-medium">Cash Available</span>
                <span className="text-blue-900 font-bold">
                  ${cashAvailable.toFixed(2)}
                </span>
              </div>
              <div className="flex items-center justify-between text-xs mt-1">
                <span className="text-blue-600">After Purchase</span>
                <span className={`font-semibold ${
                  (cashAvailable - total) < 0 ? 'text-red-600' : 'text-green-600'
                }`}>
                  ${(cashAvailable - total).toFixed(2)}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* VEE Simple Rationale (1 sentence) */}
        {veeSimple && (
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-3 mb-4">
            <div className="flex items-start gap-2">
              <AlertCircle size={16} className="text-purple-600 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-purple-800">{veeSimple}</p>
            </div>
          </div>
        )}

        {/* User Holding (for Sell orders) */}
        {side === 'sell' && userHolding && (
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-4">
            <div className="text-xs text-amber-700">
              Current position: {userHolding.quantity} shares @ ${userHolding.avg_price?.toFixed(2) || '---'}
            </div>
            {quantity === userHolding.quantity && (
              <div className="text-xs text-amber-600 mt-1 font-medium">
                ⚠️ Closing entire position
              </div>
            )}
          </div>
        )}

        {/* Advanced Options (Progressive Disclosure) */}
        <div className="border-t border-gray-200 pt-4 mb-4">
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="w-full flex items-center justify-between px-4 py-2 rounded-lg hover:bg-gray-50 transition-colors group"
          >
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-gray-700 group-hover:text-gray-900">
                Advanced Options
              </span>
              <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full font-semibold">
                Pro
              </span>
            </div>
            <span className={`text-gray-400 transition-transform ${showAdvanced ? 'rotate-180' : ''}`}>
              ▼
            </span>
          </button>

          {/* Advanced Options Panel (Expandable) */}
          {showAdvanced && (
            <div className="mt-4 space-y-4 animate-in slide-in-from-top duration-300">
              {/* Order Type Toggle */}
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-2">
                  Order Type
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => setOrderType('market')}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                      orderType === 'market'
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    Market
                  </button>
                  <button
                    onClick={() => setOrderType('limit')}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                      orderType === 'limit'
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    Limit
                  </button>
                </div>
              </div>

              {/* Limit Price (conditional) */}
              {orderType === 'limit' && (
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-2">
                    Limit Price
                  </label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">$</span>
                    <input
                      type="number"
                      step="0.01"
                      value={limitPrice}
                      onChange={(e) => setLimitPrice(e.target.value)}
                      placeholder={currentPrice.toFixed(2)}
                      className="w-full pl-8 pr-3 py-2 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none"
                    />
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    Order executes only at this price or better
                  </p>
                </div>
              )}

              {/* Stop Loss */}
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-2">
                  Stop Loss (Optional)
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">$</span>
                  <input
                    type="number"
                    step="0.01"
                    value={stopLoss}
                    onChange={(e) => setStopLoss(e.target.value)}
                    placeholder="Protective exit price"
                    className="w-full pl-8 pr-3 py-2 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none"
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Automatically sell if price drops to this level
                </p>
              </div>

              {/* Take Profit */}
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-2">
                  Take Profit (Optional)
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">$</span>
                  <input
                    type="number"
                    step="0.01"
                    value={takeProfit}
                    onChange={(e) => setTakeProfit(e.target.value)}
                    placeholder="Target exit price"
                    className="w-full pl-8 pr-3 py-2 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none"
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Automatically sell when price reaches this target
                </p>
              </div>

              {/* Time in Force */}
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-2">
                  Time in Force
                </label>
                <select
                  value={timeInForce}
                  onChange={(e) => setTimeInForce(e.target.value)}
                  className="w-full px-3 py-2 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none"
                >
                  <option value="day">Day (Cancel at market close)</option>
                  <option value="gtc">GTC (Good 'til Canceled)</option>
                  <option value="ioc">IOC (Immediate or Cancel)</option>
                  <option value="fok">FOK (Fill or Kill)</option>
                </select>
              </div>

              {/* Risk Warning */}
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                <p className="text-xs text-amber-700">
                  ⚠️ Advanced orders require understanding of market mechanics. 
                  Orders may not execute if conditions aren't met.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="space-y-3 mt-4">
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-3 rounded-lg font-semibold text-gray-700 bg-gray-100 hover:bg-gray-200 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleConfirm}
              disabled={side === 'buy' && cashAvailable !== null && (cashAvailable - total) < 0}
              className={`flex-1 px-4 py-3 rounded-lg font-semibold text-white transition-all hover:scale-105 flex items-center justify-center gap-2 ${
                side === 'buy' 
                  ? 'bg-green-600 hover:bg-green-700 disabled:bg-gray-300 disabled:text-gray-500 disabled:cursor-not-allowed' 
                  : 'bg-red-600 hover:bg-red-700'
              }`}
            >
              <CheckCircle size={18} />
              <span>
                {orderType === 'limit' ? 'Place Limit Order' : 'Confirm Purchase'}
              </span>
            </button>
          </div>
          
        </div>

        {/* Disclaimer */}
        <p className="text-xs text-gray-400 mt-3 text-center">
          {orderType === 'market' 
            ? 'Market order executed at current market price'
            : 'Limit order executes only at specified price or better'
          }
        </p>
        </>
        )}
        {/* END FORM STATE */}

      </div>
    </div>
  )
}
