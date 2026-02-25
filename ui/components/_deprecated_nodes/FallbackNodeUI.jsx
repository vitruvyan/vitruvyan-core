/**
 * FALLBACK NODE UI
 * 
 * Displays clarification request when query cannot be processed.
 * 
 * Backend Node: fallback_node.py
 * State Keys: state.action = "clarify", state.needed_slots, state.questions
 * 
 * ⚠️ CRITICAL: This component has ZERO business logic.
 * It only receives clarification data from final_state and displays it.
 * 
 * Props:
 * - questions: string[] - Clarification questions from backend
 * - neededSlots?: string[] - Missing slots (tickers, horizon, etc.)
 * - className?: string - Optional Tailwind classes
 */

'use client'

import { HelpCircle, AlertCircle } from 'lucide-react'
import { useState } from 'react'

export default function FallbackNodeUI({ questions, neededSlots, tickerOptions, onTickerSelect, className = '' }) {
  const [selectedTicker, setSelectedTicker] = useState(null)

  // Guard: Don't render if no questions
  if (!questions || questions.length === 0) {
    return null
  }

  const handleTickerClick = (ticker, name) => {
    setSelectedTicker(ticker)
    if (onTickerSelect) {
      // Send enriched query: "Analyze {CompanyName} ({TICKER}) trend"
      onTickerSelect(ticker, name)
    }
  }

  return (
    <div className={`space-y-3 ${className}`}>
      {/* Header */}
      <div className="flex items-center gap-2 text-emerald-700">
        <AlertCircle size={18} />
        <span className="font-semibold">Need More Information</span>
      </div>

      {/* Clarification Message */}
      <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4 space-y-3">
        {/* Questions */}
        <div className="space-y-2">
          {questions.map((question, index) => (
            <div key={index} className="flex items-start gap-2">
              <HelpCircle size={16} className="text-emerald-600 mt-0.5 flex-shrink-0" />
              <p className="text-gray-800">{question}</p>
            </div>
          ))}
        </div>

        {/* Ticker Options Pills (Clickable) */}
        {tickerOptions && tickerOptions.length > 0 && (
          <div className="pt-3 flex flex-wrap gap-2">
            {tickerOptions.map((option) => (
              <button
                key={option.ticker}
                onClick={() => handleTickerClick(option.ticker, option.name)}
                disabled={selectedTicker === option.ticker}
                className={`
                  px-4 py-2 rounded-full font-medium transition-all
                  ${selectedTicker === option.ticker
                    ? 'bg-green-500 text-white cursor-default'
                    : 'bg-amber-500 text-white hover:bg-amber-600 cursor-pointer'
                  }
                `}
              >
                {option.ticker} • {option.name}
              </button>
            ))}
          </div>
        )}

        {/* Missing Slots (dev info) */}
        {neededSlots && neededSlots.length > 0 && process.env.NODE_ENV === 'development' && (
          <div className="pt-2 border-t border-emerald-200">
            <div className="text-xs text-emerald-700">
              Missing slots: {neededSlots.join(', ')}
            </div>
          </div>
        )}

        {/* Helper Text */}
        <p className="text-sm text-gray-600 italic">
          💡 Please provide the requested information so I can help you.
        </p>
      </div>
    </div>
  )
}
