/**
 * 🧠 CANNodeUI - Conversational Advisor Node UI
 * Sacred Order: DISCOURSE (Presentation Layer)
 * 
 * Purpose: Display CAN conversational orchestration output
 * 
 * Architecture:
 * - Reads: canResponse prop from state.can_response
 * - Displays: Mental mode, follow-up suggestions, VSGS context indicator, sector insights
 * - Style: Consistent with Vitruvyan design system (CardLibrary, TooltipLibrary)
 * 
 * Props:
 * - canResponse: { mode, route, narrative, follow_ups, sector_insights, confidence, vsgs_context_used }
 * - onFollowUpClick?: (question: string) => void - Callback when follow-up chip clicked
 * 
 * NO LOGIC: This component only renders, no calculation, no API calls.
 * 
 * Author: Vitruvyan Sacred Orders
 * Date: December 27, 2025
 */

import React from 'react'
import { 
  Brain, 
  Compass, 
  AlertTriangle, 
  MessageSquare, 
  Sparkles, 
  ChevronRight,
  Layers,
  TrendingUp,
  Globe,
  Zap
} from 'lucide-react'
import { BaseCard } from '../cards/CardLibrary'

// Mental Mode Configuration
const MODE_CONFIG = {
  analytical: {
    icon: Brain,
    label: 'Analytical',
    emoji: '🔬',
    bgClass: 'bg-blue-50',
    borderClass: 'border-blue-300',
    textClass: 'text-blue-900',
    iconClass: 'text-blue-600',
    description: 'Deep technical analysis mode'
  },
  exploratory: {
    icon: Compass,
    label: 'Exploratory',
    emoji: '🔭',
    bgClass: 'bg-purple-50',
    borderClass: 'border-purple-300',
    textClass: 'text-purple-900',
    iconClass: 'text-purple-600',
    description: 'Discovering sectors & patterns'
  },
  urgent: {
    icon: AlertTriangle,
    label: 'Urgent',
    emoji: '🚨',
    bgClass: 'bg-red-50',
    borderClass: 'border-red-300',
    textClass: 'text-red-900',
    iconClass: 'text-red-600',
    description: 'Actionable decision needed'
  },
  conversational: {
    icon: MessageSquare,
    label: 'Context',
    emoji: '💬',
    bgClass: 'bg-gray-50',
    borderClass: 'border-gray-300',
    textClass: 'text-gray-900',
    iconClass: 'text-gray-600',
    description: 'General discussion mode'
  }
}

// Confidence Badge Component
const ConfidenceBadge = ({ confidence }) => {
  const percentage = Math.round((confidence || 0.7) * 100)
  
  let colorClass = 'bg-gray-200 text-gray-700'
  if (percentage >= 85) {
    colorClass = 'bg-green-100 text-green-800'
  } else if (percentage >= 70) {
    colorClass = 'bg-blue-100 text-blue-800'
  } else if (percentage >= 50) {
    colorClass = 'bg-yellow-100 text-yellow-800'
  } else {
    colorClass = 'bg-red-100 text-red-800'
  }
  
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${colorClass}`}>
      <Zap className="w-3 h-3 mr-1" />
      {percentage}% confidence
    </span>
  )
}

// VSGS Context Indicator
const VSGSIndicator = ({ used }) => {
  if (!used) return null
  
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
      <Layers className="w-3 h-3 mr-1" />
      VSGS® Context
    </span>
  )
}

// Follow-Up Chip Component
const FollowUpChip = ({ question, onClick }) => {
  return (
    <button
      onClick={() => onClick?.(question)}
      className="inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium 
                 bg-gradient-to-r from-slate-100 to-slate-50 
                 border border-slate-200 
                 text-slate-700 
                 hover:from-blue-50 hover:to-indigo-50 
                 hover:border-blue-300 hover:text-blue-800
                 transition-all duration-200 
                 shadow-sm hover:shadow-md
                 cursor-pointer"
    >
      <Sparkles className="w-3.5 h-3.5 mr-1.5 text-amber-500" />
      {question}
      <ChevronRight className="w-3.5 h-3.5 ml-1 text-slate-400" />
    </button>
  )
}

// Sector Insights Card
const SectorInsightsCard = ({ insights }) => {
  if (!insights) return null
  
  const { sectors, regions, risk_profile, patterns } = insights
  
  return (
    <div className="mt-4 p-3 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg border border-purple-200">
      <div className="flex items-center gap-2 mb-2">
        <Globe className="w-4 h-4 text-purple-600" />
        <span className="text-sm font-semibold text-purple-900">Sector Insights</span>
      </div>
      
      <div className="grid grid-cols-2 gap-2 text-xs">
        {sectors && sectors.length > 0 && (
          <div>
            <span className="text-purple-600 font-medium">Sectors:</span>
            <span className="ml-1 text-purple-900">{sectors.join(', ')}</span>
          </div>
        )}
        
        {regions && regions.length > 0 && (
          <div>
            <span className="text-purple-600 font-medium">Regions:</span>
            <span className="ml-1 text-purple-900">{regions.join(', ')}</span>
          </div>
        )}
        
        {risk_profile && (
          <div>
            <span className="text-purple-600 font-medium">Risk Profile:</span>
            <span className="ml-1 text-purple-900">{risk_profile.level || 'N/A'}</span>
          </div>
        )}
        
        {patterns && patterns.length > 0 && (
          <div className="col-span-2">
            <span className="text-purple-600 font-medium">Patterns:</span>
            <span className="ml-1 text-purple-900">{patterns.slice(0, 3).join(', ')}</span>
          </div>
        )}
      </div>
    </div>
  )
}

// Main Component
const CANNodeUI = ({ canResponse, onFollowUpClick }) => {
  // Early return if no CAN response
  if (!canResponse) {
    return null
  }

  const { 
    mode = 'conversational', 
    route,
    follow_ups = [], 
    sector_insights,
    confidence = 0.7,
    vsgs_context_used = false,
    mcp_tools_called = []
  } = canResponse

  // Get mode configuration
  const modeConfig = MODE_CONFIG[mode] || MODE_CONFIG.conversational
  const ModeIcon = modeConfig.icon

  return (
    <BaseCard 
      title="Context" 
      icon={Brain}
      variant="vitruvyan"
      className="mb-4"
    >
      {/* Mode Badge Row */}
      <div className="flex items-center justify-between flex-wrap gap-2 mb-3">
        {/* Mode Badge */}
        <div className={`inline-flex items-center px-3 py-1.5 rounded-lg ${modeConfig.bgClass} ${modeConfig.borderClass} border`}>
          <ModeIcon className={`w-4 h-4 mr-2 ${modeConfig.iconClass}`} />
          <span className={`text-sm font-semibold ${modeConfig.textClass}`}>
            {modeConfig.emoji} {modeConfig.label}
          </span>
        </div>
        
        {/* Right side badges */}
        <div className="flex items-center gap-2">
          <VSGSIndicator used={vsgs_context_used} />
          <ConfidenceBadge confidence={confidence} />
        </div>
      </div>
      
      {/* Mode Description */}
      <p className="text-xs text-gray-500 mb-3">{modeConfig.description}</p>
      
      {/* MCP Tools Called (if any) */}
      {mcp_tools_called && mcp_tools_called.length > 0 && (
        <div className="mb-3 flex items-center gap-2 text-xs text-gray-500">
          <TrendingUp className="w-3.5 h-3.5" />
          <span>Tools: {mcp_tools_called.join(', ')}</span>
        </div>
      )}
      
      {/* Sector Insights (if exploratory mode) */}
      {sector_insights && <SectorInsightsCard insights={sector_insights} />}
      
      {/* Follow-Up Suggestions */}
      {follow_ups && follow_ups.length > 0 && (
        <div className="mt-4">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="w-4 h-4 text-amber-500" />
            <span className="text-sm font-medium text-gray-700">Continue exploring</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {follow_ups.map((question, index) => (
              <FollowUpChip 
                key={index} 
                question={question} 
                onClick={onFollowUpClick}
              />
            ))}
          </div>
        </div>
      )}
    </BaseCard>
  )
}

export default CANNodeUI
