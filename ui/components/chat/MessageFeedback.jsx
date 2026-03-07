// components/chat/MessageFeedback.jsx
// Thumbs up/down feedback for AI messages — Plasticity integration
// Last updated: Mar 07, 2026
'use client'

import { ThumbsUp, ThumbsDown } from 'lucide-react'

/**
 * MessageFeedback — renders thumbs up/down under AI messages.
 *
 * Domain-agnostic. Sends FeedbackSignal via onFeedback callback.
 * Shows active state when feedback already submitted.
 *
 * @param {object} props
 * @param {object} props.message - ChatMessage object
 * @param {string|null} props.currentFeedback - 'positive'|'negative'|null
 * @param {function} props.onFeedback - (feedback: 'positive'|'negative') => void
 */
export function MessageFeedback({ message, currentFeedback, onFeedback }) {
  if (message.sender !== 'ai' || !message.isComplete || message.error) {
    return null
  }

  return (
    <div className="flex items-center gap-1 mt-2 pt-1 border-t border-gray-100">
      <span className="text-[10px] text-gray-400 mr-1">Helpful?</span>
      <button
        onClick={() => onFeedback('positive')}
        disabled={currentFeedback === 'positive'}
        className={`p-1 rounded transition-colors ${
          currentFeedback === 'positive'
            ? 'text-green-600 bg-green-50'
            : 'text-gray-400 hover:text-green-600 hover:bg-green-50'
        }`}
        aria-label="Thumbs up"
      >
        <ThumbsUp size={14} />
      </button>
      <button
        onClick={() => onFeedback('negative')}
        disabled={currentFeedback === 'negative'}
        className={`p-1 rounded transition-colors ${
          currentFeedback === 'negative'
            ? 'text-red-600 bg-red-50'
            : 'text-gray-400 hover:text-red-600 hover:bg-red-50'
        }`}
        aria-label="Thumbs down"
      >
        <ThumbsDown size={14} />
      </button>
      {currentFeedback && (
        <span className="text-[10px] text-gray-400 ml-1">
          {currentFeedback === 'positive' ? 'Thanks!' : 'Noted'}
        </span>
      )}
    </div>
  )
}
