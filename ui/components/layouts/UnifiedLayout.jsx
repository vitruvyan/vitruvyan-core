/**
 * UNIFIED LAYOUT WRAPPER - Single Ticker Style
 * Wraps all conversation types with consistent design pattern
 * Based on ComposeNodeUI single ticker template
 */

'use client'

import { FileText, TrendingUp, BarChart3, PieChart, AlertCircle } from 'lucide-react'

export default function UnifiedLayout({ 
  title,
  icon: Icon = FileText,
  iconColor = 'text-blue-600',
  narrative,
  veeExplanations,
  numericalPanel,
  children,
  className = ''
}) {
  // Render narrative with markdown-style formatting
  const renderNarrative = (text) => {
    if (!text) return null
    
    const lines = text.split('\n')
    return lines.map((line, index) => {
      // Headers (###)
      if (line.startsWith('###')) {
        return (
          <h3 key={index} className="text-lg font-semibold text-gray-900 mt-4 mb-2">
            {line.replace(/^###\s*/, '')}
          </h3>
        )
      }
      // Bold (**text**)
      if (line.includes('**')) {
        const parts = line.split(/\*\*(.*?)\*\*/)
        return (
          <p key={index} className="text-gray-700 mb-2">
            {parts.map((part, i) => 
              i % 2 === 1 ? <strong key={i}>{part}</strong> : part
            )}
          </p>
        )
      }
      // Lists (- item)
      if (line.startsWith('- ')) {
        return (
          <li key={index} className="text-gray-700 ml-4">
            {line.replace(/^-\s*/, '')}
          </li>
        )
      }
      // Regular paragraph
      if (line.trim()) {
        return (
          <p key={index} className="text-gray-700 mb-2 leading-relaxed">
            {line}
          </p>
        )
      }
      return <br key={index} />
    })
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header with Icon */}
      {title && (
        <div className="flex items-center gap-2 mb-2">
          <Icon size={20} className={iconColor} />
          <h2 className="text-xl font-bold text-gray-900">{title}</h2>
        </div>
      )}

      {/* VEE Narrative - Same gradient style as single ticker */}
      {narrative && (
        <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-4 rounded-lg border border-blue-100 shadow-sm">
          <div className="text-sm text-gray-700 leading-relaxed">
            {renderNarrative(narrative)}
          </div>
        </div>
      )}

      {/* Main Content */}
      {children}

      {/* Disclaimer Footer (like single ticker) */}
      <div className="bg-yellow-50 border border-yellow-200 p-3 rounded-lg">
        <p className="text-xs text-yellow-800">
          <strong>⚠️ Disclaimer:</strong> This analysis is for informational purposes only. 
          Not financial advice. Always perform your own due diligence and consult with a qualified 
          financial advisor before making investment decisions.
        </p>
      </div>
    </div>
  )
}
