// components/chat/Chat.jsx
// Domain-Agnostic Chat Container — Vitruvyan Core
// Last updated: Feb 28, 2026
//
// This component is INFRASTRUCTURE, not a domain feature.
// It does NOT know about tickers, portfolios, trading, or any vertical.
// Domain plugins inject behavior via extensions (ChatContract.ts).
'use client'

import { useEffect, useRef } from 'react'
import { useChat } from './hooks'
import { useFeedback } from './hooks/useFeedback'
import { ChatMessages } from './ChatMessages'
import { ChatInput } from './ChatInput'

/**
 * Chat — Domain-Agnostic Container
 *
 * Props:
 * - initialQuery: auto-submit on mount (optional)
 * - apiEndpoint: backend graph endpoint URL
 * - userId: authenticated user ID (optional)
 * - extensions: domain plugin injections (see ChatContract.ts)
 * - adaptResponse: domain adapter function (finalState → UIResponsePayload)
 * - onResponseComplete: callback when AI response is ready
 * - placeholder: input placeholder text
 * - assistantName: AI assistant display name (default: "Vitruvyan")
 * - thinkingSteps: custom thinking step definitions (from domain plugin)
 */
export default function Chat({
  initialQuery = '',
  apiEndpoint = '/api/graph/run',
  userId = null,
  extensions = {},
  adaptResponse = null,
  onResponseComplete = null,
  placeholder = 'Ask a question...',
  assistantName = 'Vitruvyan',
  thinkingSteps = null,
  isVisible = true
}) {
  const {
    messages,
    isProcessing,
    selectedEntities,
    sendMessage,
    setSelectedEntities,
  } = useChat({ apiEndpoint, userId, thinkingSteps, adaptResponse })

  const { submitFeedback, getFeedback } = useFeedback(apiEndpoint)

  // Auto-submit initial query on mount
  const hasSubmittedInitial = useRef(false)

  useEffect(() => {
    if (initialQuery && !hasSubmittedInitial.current && isVisible) {
      hasSubmittedInitial.current = true
      sendMessage(initialQuery, [])
    }
  }, [initialQuery, isVisible, sendMessage])

  // Notify parent when AI response is complete
  useEffect(() => {
    if (onResponseComplete && messages.length > 0) {
      const lastMessage = messages[messages.length - 1]
      if (lastMessage.sender === 'ai' && lastMessage.isComplete && lastMessage.finalState) {
        onResponseComplete(lastMessage.finalState)
      }
    }
  }, [messages, onResponseComplete])

  const handleSend = (text, entities) => {
    sendMessage(text, entities)
  }

  const handleFollowUpClick = (question) => {
    sendMessage(question, selectedEntities)
  }

  const handleEntityClick = (entity) => {
    if (extensions.onEntityClick) {
      extensions.onEntityClick(entity)
    }
  }

  const handleEntityAdd = (entity) => {
    if (!selectedEntities.includes(entity)) {
      setSelectedEntities([...selectedEntities, entity])
    }
  }

  const handleEntityRemove = (entity) => {
    setSelectedEntities(selectedEntities.filter(e => e !== entity))
  }

  return (
    <div className="flex flex-col min-h-screen bg-white">
      {/* Messages Area */}
      <div className="flex-1">
        <div className="max-w-7xl mx-auto">
          <ChatMessages
            messages={messages}
            onFollowUpClick={handleFollowUpClick}
            onEntityClick={handleEntityClick}
            assistantName={assistantName}
            extensions={extensions}
            getFeedback={getFeedback}
            onFeedback={submitFeedback}
          />
        </div>
      </div>

      {/* Input Area */}
      <div className="max-w-7xl mx-auto w-full">
        <ChatInput
          onSend={handleSend}
          isProcessing={isProcessing}
          selectedEntities={selectedEntities}
          onEntityAdd={handleEntityAdd}
          onEntityRemove={handleEntityRemove}
          placeholder={placeholder}
          extensions={extensions.input}
        />
      </div>
    </div>
  )
}
