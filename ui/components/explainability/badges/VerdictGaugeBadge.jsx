/**
 * VERDICT GAUGE BADGE (Quick Decision Indicator)
 * 
 * Shows composite score with 5-level verdict system:
 * - STRONG BUY (80-100%): Dark green
 * - BUY (60-80%): Light green
 * - HOLD (40-60%): Yellow
 * - SELL (20-40%): Orange
 * - STRONG SELL (0-20%): Red
 * 
 * Features:
 * - Horizontal progress bar (space-efficient)
 * - Animated transitions
 * - Icon + Label + Score
 * 
 * Props:
 * - score: number (0.0-1.0) - Composite score from Neural Engine
 * - className?: string
 */

'use client'

import { TrendingUp, TrendingDown, Minus, AlertCircle } from 'lucide-react'

export default function VerdictGaugeBadge({ score, className = '' }) {
  // Guard: Handle invalid scores
  if (score === null || score === undefined) {
    return null
  }

  const scorePercent = score * 100

  // 5-level verdict calculation
  const getVerdict = (percent) => {
    if (percent >= 80) return {
      label: "STRONG BUY",
      icon: TrendingUp,
      bgColor: "bg-green-50",
      borderColor: "border-green-500",
      textColor: "text-green-700",
      barColor: "bg-green-500",
      iconColor: "text-green-600"
    }
    if (percent >= 60) return {
      label: "BUY",
      icon: TrendingUp,
      bgColor: "bg-green-50",
      borderColor: "border-green-400",
      textColor: "text-green-600",
      barColor: "bg-green-400",
      iconColor: "text-green-500"
    }
    if (percent >= 40) return {
      label: "HOLD",
      icon: Minus,
      bgColor: "bg-yellow-50",
      borderColor: "border-yellow-500",
      textColor: "text-yellow-700",
      barColor: "bg-yellow-500",
      iconColor: "text-yellow-600"
    }
    if (percent >= 20) return {
      label: "SELL",
      icon: TrendingDown,
      bgColor: "bg-orange-50",
      borderColor: "border-orange-400",
      textColor: "text-orange-600",
      barColor: "bg-orange-400",
      iconColor: "text-orange-500"
    }
    return {
      label: "STRONG SELL",
      icon: AlertCircle,
      bgColor: "bg-red-50",
      borderColor: "border-red-500",
      textColor: "text-red-700",
      barColor: "bg-red-500",
      iconColor: "text-red-600"
    }
  }

  const verdict = getVerdict(scorePercent)
  const Icon = verdict.icon

  return (
    <div className={`inline-flex items-center gap-2 ${className}`}>
      {/* Pill Badge with Horizontal Progress Bar */}
      <div className={`
        relative overflow-hidden
        px-4 py-1.5 rounded-full border-2
        ${verdict.bgColor} ${verdict.borderColor}
      `}>
        {/* Background Progress Bar (horizontal fill from left) */}
        <div 
          className={`
            absolute inset-0 ${verdict.barColor} opacity-20
            transition-all duration-500 ease-out
          `}
          style={{ width: `${scorePercent}%` }}
        />

        {/* Content */}
        <div className="relative flex items-center gap-2">
          <Icon className={`w-4 h-4 ${verdict.iconColor}`} />
          <span className={`text-sm font-bold ${verdict.textColor}`}>
            {verdict.label}
          </span>
          <span className={`text-sm font-semibold ${verdict.textColor}`}>
            {scorePercent.toFixed(0)}%
          </span>
        </div>
      </div>
    </div>
  )
}
