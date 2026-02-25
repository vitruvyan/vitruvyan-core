// adapters/AdvisorAdapter.jsx
// Feb 1, 2026 - Adapter Pattern per Advisor + Trading Bubble
//
// Filosofia: Vitruvyan = "Trading accessibile a tutti"
// - Chat-first UX (NO pagine complesse stile IBKR)
// - 5-signal system chiaro: STRONG_BUY > BUY > HOLD > SELL > STRONG_SELL
// - Bubble expansion pattern (coerente con PortfolioBanner)
// - 3 click: Buy → Adjust Quantity → Confirm
//
// Architecture:
// - Adapter extracts advisor_recommendation from state
// - Maps backend 5-signal → UI configuration
// - Renders AdvisorInsight (signal display) + TradingBubble (order form)
// - Handles order execution via Shadow Trading API

'use client'

import { useState } from 'react'
import { TrendingUp, TrendingDown, Minus, ShoppingCart, DollarSign } from 'lucide-react'
import { AdvisorInsight } from '../composites/AdvisorInsight'
import { TradingBubble } from '../trading/TradingBubble'

// 🎯 5-Signal Configuration (Feb 1, 2026)
// Maps backend action (STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL) → UI config
const SIGNAL_CONFIG = {
  STRONG_BUY: {
    label: 'Strong Buy',
    shortLabel: 'Acquisto Forte',
    icon: TrendingUp,
    iconColor: 'text-green-700',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-300',
    badgeBg: 'bg-green-600',
    badgeText: 'text-white',
    showBuyButton: true,
    showSellButton: false,
    orientation: 'positive'
  },
  BUY: {
    label: 'Buy',
    shortLabel: 'Acquisto',
    icon: TrendingUp,
    iconColor: 'text-green-600',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    badgeBg: 'bg-green-100',
    badgeText: 'text-green-700',
    showBuyButton: true,
    showSellButton: false,
    orientation: 'positive'
  },
  HOLD: {
    label: 'Hold',
    shortLabel: 'Mantieni',
    icon: Minus,
    iconColor: 'text-amber-600',
    bgColor: 'bg-amber-50',
    borderColor: 'border-amber-200',
    badgeBg: 'bg-amber-100',
    badgeText: 'text-amber-700',
    showBuyButton: true,  // ✅ ALWAYS show - user's right to buy
    showSellButton: false,
    orientation: 'neutral'
  },
  SELL: {
    label: 'Sell',
    shortLabel: 'Vendita',
    icon: TrendingDown,
    iconColor: 'text-red-600',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
    badgeBg: 'bg-red-100',
    badgeText: 'text-red-700',
    showBuyButton: true,  // ✅ ALWAYS show - user's right to buy against advisor
    showSellButton: true,
    orientation: 'negative'
  },
  STRONG_SELL: {
    label: 'Strong Sell',
    shortLabel: 'Vendita Forte',
    icon: TrendingDown,
    iconColor: 'text-red-700',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-300',
    badgeBg: 'bg-red-600',
    badgeText: 'text-white',
    showBuyButton: true,  // ✅ ALWAYS show - user's right to buy against advisor
    showSellButton: true,
    orientation: 'negative'
  }
}

export function AdvisorAdapter({ 
  advisorRecommendation, 
  ticker, 
  currentPrice,
  userHolding = null,
  onOrderExecuted,
  onViewPortfolio = null // Feb 4, 2026: Portfolio navigation callback (optional)
}) {
  const [showTradingBubble, setShowTradingBubble] = useState(false)
  const [orderSide, setOrderSide] = useState('buy') // 'buy' or 'sell'

  if (!advisorRecommendation) {
    return null
  }

  const { action, confidence, rationale, signal_label } = advisorRecommendation
  
  // Map backend action to UI config
  const signalKey = action || 'HOLD'
  const config = SIGNAL_CONFIG[signalKey] || SIGNAL_CONFIG.HOLD
  const SignalIcon = config.icon

  // Determine if user has position (for Sell button visibility)
  const hasPosition = userHolding && userHolding.quantity > 0

  // Handle Buy button click
  const handleBuyClick = () => {
    setOrderSide('buy')
    setShowTradingBubble(true)
  }

  // Handle Sell button click
  const handleSellClick = () => {
    setOrderSide('sell')
    setShowTradingBubble(true)
  }

  // Handle close bubble
  const handleCloseBubble = () => {
    setShowTradingBubble(false)
  }

  // Handle order confirmation (Feb 4, 2026 - Updated with success state)
  const handleOrderConfirm = async (orderPayload) => {
    // Debug log
    console.log('[AdvisorAdapter] handleOrderConfirm received:', orderPayload)
    console.log('[AdvisorAdapter] typeof orderPayload:', typeof orderPayload)
    
    // Extract quantity from payload (TradingBubble sends full orderPayload object)
    const quantity = typeof orderPayload === 'number' 
      ? orderPayload 
      : orderPayload.quantity
    
    console.log('[AdvisorAdapter] Extracted quantity:', quantity, 'type:', typeof quantity)
    
    // Execute order via parent callback (returns result)
    if (onOrderExecuted) {
      const result = await onOrderExecuted({
        ticker,
        side: orderSide,
        quantity: parseInt(quantity),  // Ensure it's an integer
        price: currentPrice
      })
      
      // Pass result back to TradingBubble (it will update its own state)
      return result
    }
    
    return { success: false, error: 'No order handler available' }
  }

  return (
    <div className="mt-6">
      {/* Signal Display (AdvisorInsight) */}
      <AdvisorInsight 
        insight={{
          signal_label: config.shortLabel,
          orientation: config.orientation,
          rationale: rationale,
          confidence: confidence
        }}
      />

      {/* Trading Actions (Buy/Sell buttons) */}
      <div className="mt-4 flex gap-3">
        {/* Buy button - ALWAYS visible (user's right to choose) */}
        <button
          onClick={handleBuyClick}
          className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-semibold transition-all hover:scale-105 ${
            signalKey === 'STRONG_BUY' || signalKey === 'BUY'
              ? `${config.badgeBg} ${config.badgeText}`
              : 'bg-gray-100 text-gray-700 border-2 border-gray-300'
          }`}
        >
          <ShoppingCart size={18} />
          <span>Compra {ticker}</span>
        </button>

        {/* Sell button - Only if user has position */}
        {hasPosition && (
          <button
            onClick={handleSellClick}
            className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-semibold transition-all hover:scale-105 ${
              signalKey === 'SELL' || signalKey === 'STRONG_SELL'
                ? `${config.badgeBg} ${config.badgeText}`
                : 'bg-gray-100 text-gray-700 border-2 border-gray-300'
            }`}
          >
            <DollarSign size={18} />
            <span>Vendi {ticker}</span>
            <span className="text-xs opacity-75">({userHolding.quantity} shares)</span>
          </button>
        )}
      </div>

      {/* Trading Bubble (inline expansion, stile PortfolioBanner) */}
      {showTradingBubble && (
        <TradingBubble
          ticker={ticker}
          currentPrice={currentPrice}
          side={orderSide}
          veeSimple={rationale?.split('.')[0] || `Segnale ${config.shortLabel.toLowerCase()}`}
          userHolding={userHolding}
          onConfirm={handleOrderConfirm}
          onClose={handleCloseBubble}
          onViewPortfolio={onViewPortfolio}
        />
      )}
    </div>
  )
}
