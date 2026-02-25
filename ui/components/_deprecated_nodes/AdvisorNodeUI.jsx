/**
 * 🎯 AdvisorNodeUI - Actionable Recommendation Card
 * Sacred Order: DISCOURSE (Presentation Layer)
 * 
 * Purpose: Display advisor_recommendation from advisor_node
 * 
 * Architecture:
 * - Reads: advisorRecommendation prop (action, confidence, rationale, factors_considered)
 * - Displays: Card with icon, action label, confidence badge, rationale
 * - Style: Consistent with Vitruvyan design system (CardLibrary, TooltipLibrary)
 * 
 * NO LOGIC: This component only renders, no calculation, no API calls.
 * 
 * Author: Vitruvyan Sacred Orders
 * Date: December 26, 2025
 */

import React from 'react'
import { CheckCircle, AlertCircle, Circle, XCircle, Slash, ArrowRightCircle, TrendingUp } from 'lucide-react'

const AdvisorNodeUI = ({ advisorRecommendation }) => {
  if (!advisorRecommendation) {
    return null
  }

  const { action, confidence, rationale, factors_considered } = advisorRecommendation

  // Action configuration (icon, color, label)
  const getActionConfig = (action) => {
    if (action === 'BUY') {
      return {
        icon: CheckCircle,
        color: 'green',
        bgClass: 'bg-green-50',
        borderClass: 'border-green-300',
        textClass: 'text-green-900',
        iconClass: 'text-green-600',
        label: 'BUY',
        displayLabel: '🟢 Buy'
      }
    } else if (action === 'BUY_cautious') {
      return {
        icon: AlertCircle,
        color: 'yellow',
        bgClass: 'bg-yellow-50',
        borderClass: 'border-yellow-300',
        textClass: 'text-yellow-900',
        iconClass: 'text-yellow-600',
        label: 'BUY (Caution)',
        displayLabel: '🟡 Buy (Cautious)'
      }
    } else if (action === 'HOLD') {
      return {
        icon: Circle,
        color: 'gray',
        bgClass: 'bg-gray-50',
        borderClass: 'border-gray-300',
        textClass: 'text-gray-900',
        iconClass: 'text-gray-600',
        label: 'HOLD',
        displayLabel: '⚪ Hold'
      }
    } else if (action === 'SELL') {
      return {
        icon: XCircle,
        color: 'red',
        bgClass: 'bg-red-50',
        borderClass: 'border-red-300',
        textClass: 'text-red-900',
        iconClass: 'text-red-600',
        label: 'SELL',
        displayLabel: '🔴 Sell'
      }
    } else if (action === 'AVOID') {
      return {
        icon: Slash,
        color: 'red',
        bgClass: 'bg-red-50',
        borderClass: 'border-red-300',
        textClass: 'text-red-900',
        iconClass: 'text-red-700',
        label: 'AVOID',
        displayLabel: '⚫ Avoid'
      }
    } else if (action.startsWith('PREFER_')) {
      const ticker = action.replace('PREFER_', '')
      return {
        icon: ArrowRightCircle,
        color: 'blue',
        bgClass: 'bg-blue-50',
        borderClass: 'border-blue-300',
        textClass: 'text-blue-900',
        iconClass: 'text-blue-600',
        label: `PREFER ${ticker}`,
        displayLabel: `🟦 Prefer ${ticker}`
      }
    } else if (action === 'REBALANCE') {
      return {
        icon: TrendingUp,
        color: 'purple',
        bgClass: 'bg-purple-50',
        borderClass: 'border-purple-300',
        textClass: 'text-purple-900',
        iconClass: 'text-purple-600',
        label: 'REBALANCE',
        displayLabel: '🟪 Ribilancia Portfolio'
      }
    } else if (action.startsWith('LIGHTEN_')) {
      const ticker = action.replace('LIGHTEN_', '')
      return {
        icon: AlertCircle,
        color: 'orange',
        bgClass: 'bg-orange-50',
        borderClass: 'border-orange-300',
        textClass: 'text-orange-900',
        iconClass: 'text-orange-600',
        label: `LIGHTEN ${ticker}`,
        displayLabel: `🟠 Alleggerisci ${ticker}`
      }
    } else if (action === 'APPROVE_allocation') {
      return {
        icon: CheckCircle,
        color: 'green',
        bgClass: 'bg-green-50',
        borderClass: 'border-green-300',
        textClass: 'text-green-900',
        iconClass: 'text-green-600',
        label: 'APPROVE',
        displayLabel: '✅ Allocation Approvata'
      }
    } else if (action === 'REVIEW_allocation') {
      return {
        icon: AlertCircle,
        color: 'yellow',
        bgClass: 'bg-yellow-50',
        borderClass: 'border-yellow-300',
        textClass: 'text-yellow-900',
        iconClass: 'text-yellow-600',
        label: 'REVIEW',
        displayLabel: '⚠️ Revisione Allocation'
      }
    } else {
      // Default fallback
      return {
        icon: Circle,
        color: 'gray',
        bgClass: 'bg-gray-50',
        borderClass: 'border-gray-300',
        textClass: 'text-gray-900',
        iconClass: 'text-gray-600',
        label: action,
        displayLabel: action
      }
    }
  }

  const config = getActionConfig(action)
  const Icon = config.icon

  // Confidence label
  const getConfidenceLabel = (conf) => {
    if (conf >= 0.8) return 'High Confidence'
    if (conf >= 0.6) return 'Moderate Confidence'
    return 'Low Confidence'
  }

  const confidenceLabel = getConfidenceLabel(confidence)

  return (
    <div className="border border-emerald-200 rounded-lg bg-emerald-50 shadow-sm">
      {/* Header - Consistent with Market Intelligence style */}
      <div className="flex items-center gap-2 p-4 border-b border-emerald-100">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center">
          <Icon className="w-4 h-4 text-white" />
        </div>
        <div>
          <div className="font-semibold text-gray-900">📊 Advisor Recommendation</div>
          <div className="text-xs text-gray-500">AI-powered actionable insight</div>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {/* Action Card */}
        <div className={`${config.bgClass} ${config.borderClass} border rounded-lg p-4 mb-4`}>
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Icon className={`h-5 w-5 ${config.iconClass}`} />
              <span className={`text-sm font-semibold ${config.textClass}`}>
                {config.displayLabel}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className={`text-xs px-2 py-0.5 rounded-full border ${config.borderClass} ${config.textClass}`}>
                {confidenceLabel}
              </span>
              <span className={`text-xs font-mono ${config.textClass}`}>
                {Math.round(confidence * 100)}%
              </span>
            </div>
          </div>
          
          {/* Rationale */}
          <p className={`text-sm ${config.textClass} leading-relaxed`}>
            {rationale}
          </p>
        </div>

        {/* Factors Considered */}
        {factors_considered && factors_considered.length > 0 && (
          <div className="text-xs text-gray-600 pt-3 border-t border-gray-200">
            <span className="font-semibold">Factors considered:</span>{' '}
            <span className="font-mono">
              {factors_considered.join(', ')}
            </span>
          </div>
        )}

        {/* Disclaimer */}
        <div className="mt-4 p-3 bg-gray-50 border border-gray-200 rounded-lg">
          <p className="text-xs text-gray-600 leading-relaxed">
            ⚠️ <strong>Disclaimer:</strong> This recommendation is algorithmically generated and does not constitute financial advice. 
            Investment decisions should consider your personal situation and risk tolerance.
          </p>
        </div>
      </div>
    </div>
  )
}

export default AdvisorNodeUI
