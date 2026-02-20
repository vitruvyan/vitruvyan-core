/**
 * ThinkingSteps Component
 * 
 * Displays Leonardo's real-time thinking process during analysis.
 * Shows animated steps with geometric Unicode icons
 */

import { Loader2, Check } from 'lucide-react'

export function ThinkingSteps({ steps = [], isStreaming = false }) {
  if (steps.length === 0) {
    return null
  }

  return (
    <div className="space-y-1.5 mb-3">
      {steps.map((step, index) => (
        <div
          key={step.id}
          className={`flex items-center gap-2 text-xs transition-all duration-300 ${
            step.status === 'active'
              ? 'text-emerald-600 font-medium'
              : step.status === 'complete'
              ? 'text-gray-500'
              : 'text-gray-400'
          }`}
          style={{
            animation: step.status === 'active' ? 'fadeIn 0.3s ease-in' : 'none'
          }}
        >
          {/* Icon */}
          <span className="flex-shrink-0 w-5 h-5 flex items-center justify-center">
            {step.status === 'active' ? (
              <Loader2 size={14} className="animate-spin text-emerald-600" />
            ) : step.status === 'complete' ? (
              <Check size={14} className="text-emerald-500" />
            ) : (
              <span className="text-gray-400">•</span>
            )}
          </span>

          {/* Geometric Unicode Icon */}
          <span className="text-base">{step.emoji}</span>

          {/* Label */}
          <span className={`${step.status === 'active' ? 'animate-pulse' : ''}`}>
            {step.label}
            {step.status === 'active' && '...'}
          </span>
        </div>
      ))}
      
      {/* Global streaming indicator */}
      {isStreaming && steps.every(s => s.status === 'complete') && (
        <div className="flex items-center gap-2 text-xs text-emerald-600 font-medium animate-pulse">
          <Loader2 size={14} className="animate-spin" />
          <span>Processing...</span>
        </div>
      )}
    </div>
  )
}

// Add fadeIn animation via inline style (or add to global CSS)
if (typeof document !== 'undefined') {
  const style = document.createElement('style')
  style.textContent = `
    @keyframes fadeIn {
      from {
        opacity: 0;
        transform: translateY(-4px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }
  `
  document.head.appendChild(style)
}
