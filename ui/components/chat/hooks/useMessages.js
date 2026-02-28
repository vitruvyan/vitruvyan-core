// components/chat/hooks/useMessages.js
// Domain-Agnostic Message State — Vitruvyan Core
// Last updated: Feb 28, 2026
//
// Pure message state management. No domain concepts.

import { useState, useCallback, useRef } from 'react'

export function useMessages() {
  const [messages, setMessages] = useState([])
  const [isTyping, setIsTyping] = useState(false)
  const idCounter = useRef(0)

  const addMessage = useCallback((message) => {
    setMessages(prev => [...prev, {
      id: `msg_${Date.now()}_${idCounter.current++}`,
      timestamp: new Date().toISOString(),
      ...message
    }])
  }, [])

  const addUserMessage = useCallback((text) => {
    addMessage({
      text,
      sender: 'user',
      isComplete: true
    })
  }, [addMessage])

  const addAIMessage = useCallback((text, finalState = null, extraProps = {}) => {
    addMessage({
      text,
      sender: 'ai',
      finalState,
      uiPayload: null,
      isComplete: !!finalState,
      ...extraProps
    })
  }, [addMessage])

  const updateLastMessage = useCallback((updates) => {
    setMessages(prev => {
      const updated = [...prev]
      if (updated.length > 0) {
        updated[updated.length - 1] = {
          ...updated[updated.length - 1],
          ...updates
        }
      }
      return updated
    })
  }, [])

  const clearMessages = useCallback(() => {
    setMessages([])
  }, [])

  return {
    messages,
    isTyping,
    setIsTyping,
    addMessage,
    addUserMessage,
    addAIMessage,
    updateLastMessage,
    clearMessages
  }
}
