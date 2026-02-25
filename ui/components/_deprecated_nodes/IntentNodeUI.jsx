/**
 * INTENT NODE UI
 * 
 * Displays detected intent, interactive horizon buttons, and verdict pill.
 * 
 * Backend Node: intent_detection_node.py, compose_node.py (verdict generation)
 * State Keys: state.intent, state.horizon, state.route, state.final_verdict
 * 
 * Props:
 * - intent: string - Detected intent ("trend" | "momentum" | "sentiment" | etc.)
 * - horizon: string | null - Time horizon ("short" | "medium" | "long")
 * - route: string - Current graph route
 * - finalVerdict: object - Backend-generated verdict {label, color, composite_score, confidence}
 * - activeHorizon: string - Currently selected horizon
 * - onHorizonChange: function - Callback to change horizon
 * - horizonData: object - Data for all 3 horizons from Neural Engine
 * - isLoadingHorizons: boolean - Loading state for horizon data
 * - className?: string - Optional Tailwind classes
 */

'use client'

import { Target, Clock, TrendingDown, TrendingUp, Loader2 } from 'lucide-react'
import { formatIntent } from '@/lib/utils/formatters'

export default function IntentNodeUI({ 
  intent, 
  horizon, 
  route, 
  finalVerdict,
  activeHorizon,
  onHorizonChange,
  horizonData,
  isLoadingHorizons,
  className = '' 
}) {
  // Guard: Don't render if no intent
  if (!intent || intent === 'unknown') {
    return null
  }

  // Intent color mapping
  const getIntentColor = (intent) => {
    const colorMap = {
      trend: 'bg-blue-50 text-blue-700 border-blue-200',
      momentum: 'bg-purple-50 text-purple-700 border-purple-200',
      sentiment: 'bg-green-50 text-green-700 border-green-200',
      risk: 'bg-red-50 text-red-700 border-red-200',
      portfolio_review: 'bg-yellow-50 text-yellow-700 border-yellow-200',
      small_talk: 'bg-gray-50 text-gray-700 border-gray-200',
    }
    return colorMap[intent] || 'bg-gray-50 text-gray-700 border-gray-200'
  }

  // Map backend verdict to frontend colors
  const getVerdictColor = (label) => {
    const colorMap = {
      'Strong Buy': 'bg-green-100 text-green-800 border-green-300',
      'Buy': 'bg-green-50 text-green-700 border-green-200',
      'Hold': 'bg-gray-100 text-gray-700 border-gray-300',
      'Sell': 'bg-orange-100 text-orange-700 border-orange-300',
      'Strong Sell': 'bg-red-100 text-red-800 border-red-300',
    }
    return colorMap[label] || 'bg-gray-100 text-gray-700 border-gray-300'
  }

  // Use backend-generated verdict directly (SINGLE SOURCE OF TRUTH)
  const verdict = finalVerdict ? {
    label: finalVerdict.label,
    color: getVerdictColor(finalVerdict.label),
    compositeScore: finalVerdict.composite_score
  } : null

  const horizons = [
    { value: 'short', label: 'Short 1-3m' },
    { value: 'medium', label: 'Medium 3-12m' },
    { value: 'long', label: 'Long 12m+' }
  ]

  return (
    <div className={`flex items-center flex-wrap gap-3 ${className}`}>
      {/* Intent Badge */}
      <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border ${getIntentColor(intent)}`}>
        <Target size={14} />
        <span className="text-sm font-medium">{formatIntent(intent)}</span>
      </div>

      {/* Verdict Pill */}
      {verdict && (
        <div className={`flex items-center gap-2 px-4 py-1.5 rounded-full border font-semibold ${verdict.color}`}>
          {isLoadingHorizons ? (
            <Loader2 size={14} className="animate-spin" />
          ) : verdict.label.includes('Buy') || verdict.label === 'Strong Buy' ? (
            <TrendingUp size={14} />
          ) : verdict.label.includes('Sell') ? (
            <TrendingDown size={14} />
          ) : null}
          <span className="text-sm">{verdict.label}</span>
        </div>
      )}

      {/* Horizon Buttons */}
      <div className="flex items-center gap-2 ml-auto">
        {horizons.map((h) => (
          <button
            key={h.value}
            onClick={() => onHorizonChange(h.value)}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-sm font-medium transition-colors ${
              activeHorizon === h.value
                ? 'bg-blue-600 text-white border-blue-600'
                : 'bg-white text-gray-600 border-gray-300 hover:border-blue-400 hover:text-blue-600'
            }`}
          >
            <Clock size={14} />
            <span>{h.label}</span>
          </button>
        ))}
      </div>

      {/* Route Badge (dev info) */}
      {process.env.NODE_ENV === 'development' && (
        <span className="text-xs text-gray-400 font-mono w-full mt-2">
          route: {route}
        </span>
      )}
    </div>
  )
}
