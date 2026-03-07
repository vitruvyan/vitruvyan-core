// hooks/useFeedback.js
// Plasticity feedback hook — sends thumbs up/down to backend
// Last updated: Mar 07, 2026
'use client'

import { useState, useCallback, useRef } from 'react'

/**
 * useFeedback — manages message feedback state and submission.
 *
 * Sends FeedbackSignal to the backend endpoint, which records it
 * as an Outcome in OutcomeTracker for the Plasticity learning loop.
 *
 * @param {string} apiEndpoint - Backend URL (default: from env)
 * @returns {{ submitFeedback, getFeedback }}
 */
export function useFeedback(apiEndpoint) {
  const baseUrl = apiEndpoint || process.env.NEXT_PUBLIC_API_URL || ''
  const feedbackMapRef = useRef(new Map())
  const [, forceUpdate] = useState(0)

  const submitFeedback = useCallback(async (signal) => {
    const { message_id, feedback } = signal

    // Optimistic update
    feedbackMapRef.current.set(message_id, feedback)
    forceUpdate((n) => n + 1)

    try {
      const res = await fetch(`${baseUrl}/api/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(signal),
      })

      if (!res.ok) {
        // Revert on failure
        feedbackMapRef.current.delete(message_id)
        forceUpdate((n) => n + 1)
        console.error(`Feedback submission failed: ${res.status}`)
      }
    } catch (err) {
      feedbackMapRef.current.delete(message_id)
      forceUpdate((n) => n + 1)
      console.error('Feedback submission error:', err)
    }
  }, [baseUrl])

  const getFeedback = useCallback((messageId) => {
    return feedbackMapRef.current.get(messageId) || null
  }, [])

  return { submitFeedback, getFeedback }
}
