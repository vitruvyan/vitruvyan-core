// components/chat/ThinkingSteps.jsx
// Domain-Agnostic Thinking Steps — Vitruvyan Core
// Last updated: Feb 28, 2026
//
// Animated step indicator during AI processing.
// Steps are configurable via ChatContract.DEFAULT_THINKING_STEPS
// or domain plugin override.

import { Loader2, Check } from 'lucide-react'

export function ThinkingSteps({ steps = [], isStreaming = false }) {
  if (steps.length === 0) {
    return null
  }

  return (
    <div className="space-y-1.5 mb-3">
      {steps.map((step) => (
        <div
          key={step.id}
          className={`flex items-center gap-2 text-xs transition-all duration-300 ${
            step.status === 'active'
              ? 'text-blue-600 font-medium'
              : step.status === 'complete'
              ? 'text-gray-500'
              : 'text-gray-400'
          }`}
        >
          {/* Status Icon */}
          <span className="flex-shrink-0 w-5 h-5 flex items-center justify-center">
            {step.status === 'active' ? (
              <Loader2 size={14} className="animate-spin text-blue-600" />
            ) : step.status === 'complete' ? (
              <Check size={14} className="text-green-500" />
            ) : (
              <span className="text-gray-400">•</span>
            )}
          </span>

          {/* Step Icon (Unicode geometric) */}
          <span className="text-base">{step.icon}</span>

          {/* Label */}
          <span className={step.status === 'active' ? 'animate-pulse' : ''}>
            {step.label}
            {step.status === 'active' && '...'}
          </span>
        </div>
      ))}

      {/* Global streaming indicator */}
      {isStreaming && steps.every(s => s.status === 'complete') && (
        <div className="flex items-center gap-2 text-xs text-blue-600 font-medium animate-pulse">
          <Loader2 size={14} className="animate-spin" />
          <span>Processing...</span>
        </div>
      )}
    </div>
  )
}
