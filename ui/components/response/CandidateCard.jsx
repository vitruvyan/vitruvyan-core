// components/response/CandidateCard.jsx
import React from 'react'
import { TrendingUp, Activity, Zap, MessageCircle, DollarSign, Scale, ChevronRight } from 'lucide-react'

const CandidateCard = ({
  rank,
  ticker,
  companyName,
  composite,
  dominantFactor,
  dominantFactorValue,
  selectionReason,
  factors,
  onExplore
}) => {
  // Rank badge styling
  const getRankBadgeStyle = (rank) => {
    if (rank === 1) return 'bg-yellow-400 text-yellow-900 font-bold'
    if (rank === 2) return 'bg-gray-300 text-gray-700 font-semibold'
    if (rank === 3) return 'bg-amber-600 text-amber-100 font-semibold'
    return 'bg-gray-200 text-gray-600'
  }

  // Dominant factor icon
  const getFactorIcon = (factor) => {
    const icons = {
      momentum: TrendingUp,
      trend: Activity,
      volatility: Zap,
      sentiment: MessageCircle,
      value: DollarSign,
      balanced: Scale
    }
    const Icon = icons[factor] || Scale
    return <Icon className="w-4 h-4" />
  }

  // Factor bar width (proportional to z-score, max at ±2.0)
  const getBarWidth = (value) => {
    const absValue = Math.abs(value || 0)
    const percentage = Math.min((absValue / 2.0) * 100, 100)
    return `${percentage}%`
  }

  // Factor bar color
  const getBarColor = (value) => {
    if (value > 1.0) return 'bg-green-500'
    if (value > 0.5) return 'bg-blue-500'
    if (value > 0) return 'bg-gray-400'
    return 'bg-red-500'
  }

  return (
    <div className="border border-gray-200 rounded-lg p-4 bg-white hover:shadow-md transition-shadow">
      {/* Header Row: Rank + Ticker + Company + Composite */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          {/* Rank Badge */}
          <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm ${getRankBadgeStyle(rank)}`}>
            #{rank}
          </div>
          
          {/* Ticker + Company */}
          <div>
            <div className="font-bold text-lg text-gray-900">{ticker}</div>
            <div className="text-sm text-gray-600">{companyName}</div>
          </div>
        </div>

        {/* Composite Score */}
        <div className="text-right">
          <div className="flex items-center gap-1 text-lg font-semibold text-gray-900">
            <span>⭐</span>
            <span>{composite?.toFixed(2) || 'N/A'}</span>
          </div>
        </div>
      </div>

      {/* Divider */}
      <div className="border-t border-gray-200 my-3"></div>

      {/* Dominant Factor Bar */}
      <div className="mb-3">
        <div className="flex items-center gap-2 text-sm text-gray-700 mb-1">
          {getFactorIcon(dominantFactor)}
          <span className="font-medium capitalize">{dominantFactor}:</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex-1 bg-gray-100 rounded-full h-3 overflow-hidden">
            <div 
              className={`h-full rounded-full transition-all ${getBarColor(dominantFactorValue)}`}
              style={{ width: getBarWidth(dominantFactorValue) }}
            ></div>
          </div>
          <span className="text-sm font-mono text-gray-600 w-12 text-right">
            {dominantFactorValue?.toFixed(1) || '0.0'}
          </span>
        </div>
      </div>

      {/* Selection Reason */}
      <div className="text-sm text-gray-700 italic mb-3">
        "{selectionReason}"
      </div>

      {/* Explore Button */}
      <button
        onClick={() => onExplore && onExplore(ticker)}
        className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-md transition-colors text-sm font-medium"
      >
        <span>Explore</span>
        <ChevronRight className="w-4 h-4" />
      </button>
    </div>
  )
}

export default CandidateCard
