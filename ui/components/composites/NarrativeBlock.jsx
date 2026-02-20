// composites/NarrativeBlock.jsx
'use client'

import { tokens } from '../theme/tokens'

export function NarrativeBlock({ text, tone, recommendation }) {
  if (!text) return null

  // Tone-based styling
  const toneStyles = {
    neutral: '',
    cautious: 'border-l-4 border-l-amber-400 pl-3',
    confident: '',
    exploratory: 'italic'
  }

  return (
    <div className={toneStyles[tone] || ''}>
      <p className={tokens.typography.narrative}>
        {text}
      </p>

      {/* Recommendation badge (subtle, integrated) */}
      {recommendation && (
        <div className="mt-3 inline-flex items-center gap-2 text-sm">
          <span className="text-gray-500">Recommendation:</span>
          <span className={`font-medium ${
            recommendation.action === 'BUY' ? 'text-green-700' :
            recommendation.action === 'SELL' ? 'text-red-700' :
            'text-gray-700'
          }`}>
            {recommendation.action}
          </span>
        </div>
      )}
    </div>
  )
}