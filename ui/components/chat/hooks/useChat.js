// components/chat/hooks/useChat.js
// Domain-Agnostic Chat Hook — Vitruvyan Core
// Last updated: Feb 28, 2026
//
// No tickers, no horizons, no allocation strategies.
// Uses entities (opaque strings) instead of domain-specific concepts.
// Thinking steps are configurable via props.

import { useState, useCallback } from 'react'
import { useMessages } from './useMessages'

const DEFAULT_THINKING_STEPS = [
  { id: 1, icon: '◈', label: 'Parsing intent & context', status: 'pending', duration: 600 },
  { id: 2, icon: '⊕', label: 'Resolving entities', status: 'pending', duration: 700 },
  { id: 3, icon: '◉', label: 'Retrieving knowledge', status: 'pending', duration: 900 },
  { id: 4, icon: '△', label: 'Computing analysis', status: 'pending', duration: 1100 },
  { id: 5, icon: '◆', label: 'Running cognitive engine', status: 'pending', duration: 1300 },
  { id: 6, icon: '⬡', label: 'Generating narrative', status: 'pending', duration: 1000 },
  { id: 7, icon: '⊞', label: 'Finalizing response', status: 'pending', duration: 800 }
]

export function useChat({ apiEndpoint = '/api/graph/run', userId = null, thinkingSteps = null } = {}) {
  const { messages, isTyping, setIsTyping, addUserMessage, addAIMessage, updateLastMessage } = useMessages()

  const [selectedEntities, setSelectedEntities] = useState([])

  const steps = thinkingSteps || DEFAULT_THINKING_STEPS

  const sendMessage = useCallback(async (text, entities = []) => {
    if (!text.trim()) return

    // Add user message
    addUserMessage(text)

    // Add placeholder AI message
    setIsTyping(true)
    addAIMessage('', null, { isStreaming: true, thinkingSteps: [] })

    // Animate thinking steps
    const updateThinkingSteps = (currentSteps) => {
      updateLastMessage({ thinkingSteps: currentSteps, isStreaming: true })
    }

    const simulateThinkingSteps = async () => {
      for (let i = 0; i < steps.length; i++) {
        const updatedSteps = steps.map((step, idx) => ({
          ...step,
          status: idx < i ? 'complete' : idx === i ? 'active' : 'pending'
        }))
        updateThinkingSteps(updatedSteps)
        await new Promise(resolve => setTimeout(resolve, steps[i].duration || 800))
      }
    }

    try {
      // Start thinking animation
      simulateThinkingSteps()

      // Call backend
      const response = await fetch(apiEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: text,
          user_id: userId || 'anonymous',
          entities: entities.length > 0 ? entities : undefined
        })
      })

      if (!response.ok) {
        throw new Error(`Backend error: ${response.status}`)
      }

      const result = await response.json()

      updateLastMessage({
        text: result.narrative || 'Analysis complete.',
        finalState: result,
        isComplete: true,
        isStreaming: false,
        thinkingSteps: []
      })
    } catch (error) {
      console.error('[Chat] Error:', error)
      updateLastMessage({
        text: 'Sorry, something went wrong. Please try again.',
        error: error.message,
        isComplete: true,
        isStreaming: false,
        thinkingSteps: []
      })
    } finally {
      setIsTyping(false)
    }
  }, [apiEndpoint, userId, steps, addUserMessage, addAIMessage, updateLastMessage, setIsTyping])

  return {
    messages,
    isProcessing: isTyping,
    selectedEntities,
    sendMessage,
    setSelectedEntities
  }
}
