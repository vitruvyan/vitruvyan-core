// composites/AdvisorInsight.jsx
// UX Constitution compliant - Jan 2, 2026
// 
// GOLDEN RULE: NO TEMPLATES - Pure LLM (filtered by MCP)
// This component displays ONLY what the backend provides.
// If backend provides no text, show orientation badge only.
//
// POSITIONING RULE (BINDING):
// - ALWAYS visible (never collapsed)
// - ALWAYS after accordions (not before)
// - Cognitive compass, not introduction
//
// SIGNAL ORIENTATION RULE (BINDING):
// - MUST explicitly state: Favorable / Mixed / Caution
// - MUST align with composite score
// - MUST NOT use BUY / SELL / HOLD

'use client'

import { TrendingUp, TrendingDown, Minus, Compass, Target, Shield } from 'lucide-react'

// Signal orientation configuration
// Labels are descriptive, NOT directive (no buy/sell/hold)
// 🎯 UPDATED Feb 1, 2026: Map backend 5-signal system (STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL)
const ORIENTATION_CONFIG = {
  positive: {
    label: 'Favorable Setup',
    subtitle: 'Signals suggest positive momentum',
    icon: TrendingUp,
    iconColor: 'text-green-600',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    badgeBg: 'bg-green-100',
    badgeText: 'text-green-700'
  },
  neutral: {
    label: 'Hold Position',
    subtitle: 'Neutral signals, maintain current position',
    icon: Minus,
    iconColor: 'text-amber-500',
    bgColor: 'bg-amber-50',
    borderColor: 'border-amber-200',
    badgeBg: 'bg-amber-100',
    badgeText: 'text-amber-700'
  },
  negative: {
    label: 'Caution Advised',
    subtitle: 'Signals warrant careful consideration',
    icon: TrendingDown,
    iconColor: 'text-red-600',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
    badgeBg: 'bg-red-100',
    badgeText: 'text-red-700'
  },
  // Allocation-specific orientations
  concentrated: {
    label: 'Concentrated Allocation',
    subtitle: 'High concentration in top holdings',
    icon: Target,
    iconColor: 'text-orange-600',
    bgColor: 'bg-orange-50',
    borderColor: 'border-orange-200',
    badgeBg: 'bg-orange-100',
    badgeText: 'text-orange-700'
  },
  balanced: {
    label: 'Balanced Allocation',
    subtitle: 'Well-distributed portfolio weights',
    icon: Minus,
    iconColor: 'text-blue-600',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
    badgeBg: 'bg-blue-100',
    badgeText: 'text-blue-700'
  },
  diversified: {
    label: 'Diversified Allocation',
    subtitle: 'Broadly spread across holdings',
    icon: Shield,
    iconColor: 'text-green-600',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    badgeBg: 'bg-green-100',
    badgeText: 'text-green-700'
  }
}

export function AdvisorInsight({ insight }) {
  // Handle both legacy string format and new object format
  if (!insight) return null
  
  // Map backend signal_label to frontend orientation
  const mapSignalToOrientation = (signalLabel) => {
    if (!signalLabel) return 'neutral'
    const label = signalLabel.toLowerCase()
    
    // 🎯 NEW: Map backend 5-signal system (Feb 1, 2026)
    if (label.includes('strong_buy') || label.includes('strong buy')) return 'positive'
    if (label.includes('buy') || label.includes('acquisto') || label.includes('favorable')) return 'positive'
    if (label.includes('hold') || label.includes('mantieni')) return 'neutral'
    if (label.includes('sell') || label.includes('vendita') || label.includes('caution')) return 'negative'
    if (label.includes('strong_sell') || label.includes('strong sell')) return 'negative'
    
    // Allocation-specific mappings
    if (label.includes('concentrated')) return 'concentrated'
    if (label.includes('balanced')) return 'balanced'
    if (label.includes('diversified')) return 'diversified'
    
    return 'neutral'
  }
  
  const {
    action = '',        // NEW: Backend field (STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL)
    signal_label = '',  // Legacy field
    orientation: legacyOrientation = '',  // Legacy field
    rationale = '',
    interpretation = '',
    conditions = '',
    source = 'unknown'
  } = typeof insight === 'object' ? insight : { rationale: insight }

  // Use action mapping first, fallback to signal_label, then legacy orientation
  const backendSignal = action || signal_label
  const orientation = mapSignalToOrientation(backendSignal) || legacyOrientation || 'neutral'

  const config = ORIENTATION_CONFIG[orientation] || ORIENTATION_CONFIG.neutral
  const OrientationIcon = config.icon
  const hasRationale = rationale && rationale.trim() !== ''

  // GOLDEN RULE: If no LLM text, show minimal badge-only view
  // Do NOT synthesize fake advisory text
  if (!hasRationale) {
    return (
      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className={`p-4 ${config.bgColor} rounded-xl border ${config.borderColor}`}>
          <div className="flex items-center gap-3">
            <Compass size={18} className="text-slate-500" />
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">
              Signal Assessment
            </span>
            <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full ${config.badgeBg} ml-auto`}>
              <OrientationIcon size={14} className={config.iconColor} />
              <span className={`text-xs font-semibold ${config.badgeText}`}>
                {config.label}
              </span>
            </div>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            {config.subtitle}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="mt-6 pt-4 border-t border-gray-200">
      <div className={`p-4 ${config.bgColor} rounded-xl border ${config.borderColor}`}>
        
        {/* Header with orientation badge */}
        <div className="flex items-center gap-3 mb-3">
          <Compass size={18} className="text-slate-500" />
          <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">
            Advisor Insight
          </span>
          
          {/* Signal Orientation Badge */}
          <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full ${config.badgeBg} ml-auto`}>
            <OrientationIcon size={14} className={config.iconColor} />
            <span className={`text-xs font-semibold ${config.badgeText}`}>
              {config.label}
            </span>
          </div>
        </div>

        {/* Insight content - from LLM only */}
        <div className="space-y-2">
          {/* Main rationale (LLM-generated) */}
          <p className="text-sm text-gray-700 leading-relaxed">
            {rationale}
          </p>
          
          {/* Interpretation (if LLM provided) */}
          {interpretation && (
            <p className="text-sm text-gray-600 leading-relaxed">
              {interpretation}
            </p>
          )}
          
          {/* Conditions (if LLM provided) */}
          {conditions && (
            <p className="text-xs text-gray-500 leading-relaxed italic">
              {conditions}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
