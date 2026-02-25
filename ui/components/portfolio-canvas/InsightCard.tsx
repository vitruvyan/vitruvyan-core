/**
 * InsightCard - Guardian Insight Display Component
 * 
 * Task 26.3.3: InsightCard Component (Jan 26, 2026)
 * 
 * Features:
 * - Strategic recommendations from Guardian Agent (Task 25.5)
 * - VEE explanation collapsible accordion
 * - Severity badges (critical/high/medium/low with color coding)
 * - Affected tickers display
 * - Timestamp formatting
 * - Desktop-optimized layout
 * - Hover effects
 * - Action buttons (dismiss, view details)
 * 
 * Severity Visual Hierarchy:
 * - Critical: Red border-left, red badge, urgent icon
 * - High: Orange border-left, orange badge, warning icon
 * - Medium: Blue border-left, blue badge, info icon
 * - Low: Gray border-left, gray badge, notification icon
 */

'use client'

import { useState } from 'react'
import { GuardianInsight } from '@/hooks/usePortfolioWebSocket'
import { 
  AlertTriangle, 
  TrendingUp, 
  Info, 
  Bell,
  ChevronDown,
  ChevronUp,
  X,
  ExternalLink,
  Clock
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

export interface InsightCardProps {
  insight: GuardianInsight
  isNew?: boolean
  onDismiss?: (insightId: number) => void
  onViewDetails?: (insightId: number) => void
}

// ========== Severity Configuration ==========

const SEVERITY_CONFIG = {
  critical: {
    borderColor: 'border-l-red-500',
    bgColor: 'bg-red-50',
    badgeBg: 'bg-red-100',
    badgeText: 'text-red-800',
    icon: AlertTriangle,
    iconColor: 'text-red-600',
    label: 'Critical'
  },
  high: {
    borderColor: 'border-l-orange-500',
    bgColor: 'bg-orange-50',
    badgeBg: 'bg-orange-100',
    badgeText: 'text-orange-800',
    icon: AlertTriangle,
    iconColor: 'text-orange-600',
    label: 'High Priority'
  },
  medium: {
    borderColor: 'border-l-blue-500',
    bgColor: 'bg-blue-50',
    badgeBg: 'bg-blue-100',
    badgeText: 'text-blue-800',
    icon: Info,
    iconColor: 'text-blue-600',
    label: 'Medium Priority'
  },
  low: {
    borderColor: 'border-l-gray-400',
    bgColor: 'bg-gray-50',
    badgeBg: 'bg-gray-100',
    badgeText: 'text-gray-700',
    icon: Bell,
    iconColor: 'text-gray-500',
    label: 'Low Priority'
  }
} as const

// ========== Category Configuration ==========

const CATEGORY_CONFIG = {
  PROTECT: {
    badge: 'bg-red-100 text-red-800',
    icon: '🛡️'
  },
  IMPROVE: {
    badge: 'bg-green-100 text-green-800',
    icon: '📈'
  },
  UNDERSTAND: {
    badge: 'bg-blue-100 text-blue-800',
    icon: '💡'
  }
} as const

export function InsightCard({ 
  insight, 
  isNew = false,
  onDismiss,
  onViewDetails 
}: InsightCardProps) {
  // ========== State ==========
  const [isVeeExpanded, setIsVeeExpanded] = useState(false)
  const [isRecommendationsExpanded, setIsRecommendationsExpanded] = useState(true)
  
  // ========== Configuration ==========
  const severityConfig = SEVERITY_CONFIG[insight.severity]
  const categoryConfig = CATEGORY_CONFIG[insight.category]
  const SeverityIcon = severityConfig.icon
  
  // ========== Handlers ==========
  const handleDismiss = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (onDismiss) {
      onDismiss(insight.insight_id)
    }
  }
  
  const handleViewDetails = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (onViewDetails) {
      onViewDetails(insight.insight_id)
    }
  }
  
  // ========== Render ==========
  return (
    <div 
      className={`
        insight-card relative
        bg-white rounded-lg border-l-4 ${severityConfig.borderColor}
        shadow-md hover:shadow-lg transition-all duration-200
        ${isNew ? 'ring-2 ring-indigo-500 ring-opacity-50' : ''}
      `}
    >
      {/* ========== Header ========== */}
      <div className="p-5">
        {/* Top Bar: Severity + Category + Actions */}
        <div className="flex items-start justify-between mb-3">
          {/* Left: Severity Badge + Category Badge */}
          <div className="flex items-center space-x-2">
            {/* Severity Badge */}
            <span 
              className={`
                inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-semibold
                ${severityConfig.badgeBg} ${severityConfig.badgeText}
              `}
            >
              <SeverityIcon className="w-3.5 h-3.5" />
              <span>{severityConfig.label}</span>
            </span>
            
            {/* Category Badge */}
            <span 
              className={`
                inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-medium
                ${categoryConfig.badge}
              `}
            >
              <span>{categoryConfig.icon}</span>
              <span>{insight.category}</span>
            </span>
            
            {/* New Badge */}
            {isNew && (
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold bg-indigo-100 text-indigo-800">
                NEW
              </span>
            )}
          </div>
          
          {/* Right: Action Buttons */}
          <div className="flex items-center space-x-1">
            {/* View Details */}
            {onViewDetails && (
              <button
                onClick={handleViewDetails}
                className="p-1.5 rounded-md hover:bg-gray-100 text-gray-500 hover:text-gray-700 transition-colors"
                title="View full details"
              >
                <ExternalLink className="w-4 h-4" />
              </button>
            )}
            
            {/* Dismiss */}
            {onDismiss && (
              <button
                onClick={handleDismiss}
                className="p-1.5 rounded-md hover:bg-gray-100 text-gray-500 hover:text-gray-700 transition-colors"
                title="Dismiss insight"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
        
        {/* Title */}
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          {insight.title}
        </h3>
        
        {/* Description */}
        <p className="text-sm text-gray-700 leading-relaxed mb-4">
          {insight.description}
        </p>
        
        {/* Affected Tickers */}
        {insight.affected_tickers && insight.affected_tickers.length > 0 && (
          <div className="flex items-center space-x-2 mb-4">
            <span className="text-xs font-medium text-gray-500">Affected:</span>
            <div className="flex flex-wrap gap-1.5">
              {insight.affected_tickers.map(ticker => (
                <span 
                  key={ticker}
                  className="px-2 py-0.5 bg-gray-100 text-gray-800 rounded text-xs font-mono font-semibold"
                >
                  {ticker}
                </span>
              ))}
            </div>
          </div>
        )}
        
        {/* ========== Recommendations (Task 25.5 - Strategic Recommendations) ========== */}
        {insight.recommendations && insight.recommendations.length > 0 && (
          <div className="mb-4">
            <button
              onClick={() => setIsRecommendationsExpanded(!isRecommendationsExpanded)}
              className="flex items-center justify-between w-full text-left text-sm font-medium text-gray-700 hover:text-gray-900 mb-2"
            >
              <span>Strategic Recommendations ({insight.recommendations.length})</span>
              {isRecommendationsExpanded ? (
                <ChevronUp className="w-4 h-4" />
              ) : (
                <ChevronDown className="w-4 h-4" />
              )}
            </button>
            
            {isRecommendationsExpanded && (
              <ul className="space-y-2 pl-4">
                {insight.recommendations.map((recommendation, index) => (
                  <li 
                    key={index}
                    className="text-sm text-gray-600 flex items-start space-x-2"
                  >
                    <span className="text-indigo-600 font-bold mt-0.5">•</span>
                    <span>{recommendation}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
        
        {/* ========== VEE Explanation (Collapsible) ========== */}
        {insight.vee_explanation && (
          <div className="border-t border-gray-200 pt-4">
            <button
              onClick={() => setIsVeeExpanded(!isVeeExpanded)}
              className="flex items-center justify-between w-full text-left text-sm font-medium text-gray-700 hover:text-gray-900"
            >
              <span className="flex items-center space-x-2">
                <span>🧠</span>
                <span>VEE Analysis</span>
              </span>
              {isVeeExpanded ? (
                <ChevronUp className="w-4 h-4" />
              ) : (
                <ChevronDown className="w-4 h-4" />
              )}
            </button>
            
            {isVeeExpanded && (
              <div className={`mt-3 p-4 rounded-md ${severityConfig.bgColor}`}>
                <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                  {insight.vee_explanation}
                </p>
              </div>
            )}
          </div>
        )}
      </div>
      
      {/* ========== Footer (Timestamp + Expiry) ========== */}
      <div className="px-5 py-3 bg-gray-50 border-t border-gray-100 flex items-center justify-between text-xs text-gray-500">
        {/* Timestamp */}
        <div className="flex items-center space-x-1.5">
          <Clock className="w-3.5 h-3.5" />
          <span>
            {formatDistanceToNow(new Date(insight.created_at), { addSuffix: true })}
          </span>
        </div>
        
        {/* Expiry (if applicable) */}
        {insight.expires_at && (
          <div className="flex items-center space-x-1.5 text-orange-600">
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>
              Expires {formatDistanceToNow(new Date(insight.expires_at), { addSuffix: true })}
            </span>
          </div>
        )}
      </div>
    </div>
  )
}
