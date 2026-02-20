// composites/FollowUpChips.jsx
'use client'

import { Sparkles } from 'lucide-react'

export function FollowUpChips({ questions, onChipClick }) {
  if (!questions?.length) return null

  return (
    <div>
      <div className="flex items-center gap-2 mb-2">
        <Sparkles size={16} className="text-amber-500" />
        <span className="text-sm font-medium text-gray-700">Continue exploring</span>
      </div>
      <div className="flex flex-wrap gap-2">
        {questions.map((question, index) => (
          <button
            key={index}
            onClick={() => onChipClick?.(question)}
            className="px-3 py-1.5 text-sm bg-white border border-gray-200 rounded-full hover:bg-gray-50 hover:border-gray-300 transition-all"
          >
            {question}
          </button>
        ))}
      </div>
    </div>
  )
}