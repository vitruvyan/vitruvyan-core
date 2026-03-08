// components/chat/ChatMessages.jsx
// Domain-Agnostic Chat Messages List — Vitruvyan Core
// Last updated: Feb 28, 2026
//
// Renders the message list with auto-scroll.
// No portfolio, no ticker references. Pure infrastructure.
'use client'

import { useRef, useEffect } from 'react'
import { ChatMessage } from './ChatMessage'

export function ChatMessages({
  messages,
  onFollowUpClick,
  onEntityClick,
  assistantName = 'Vitruvyan',
  extensions = {},
  getFeedback,
  onFeedback,
}) {
  const containerRef = useRef(null)

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight
    }
  }, [messages.length])

  if (messages.length === 0) {
    // Domain plugin can provide custom empty state
    const EmptyState = extensions?.emptyState || DefaultEmptyState
    return <EmptyState />
  }

  return (
    <div ref={containerRef} className="flex-1 p-4 space-y-4">
      {messages.map((msg) => (
        <ChatMessage
          key={msg.id}
          message={msg}
          onFollowUpClick={onFollowUpClick}
          onEntityClick={onEntityClick}
          assistantName={assistantName}
          extensions={extensions}
          currentFeedback={getFeedback ? getFeedback(msg.id) : null}
          onFeedback={onFeedback}
        />
      ))}
    </div>
  )
}

/**
 * Default empty state (domain-agnostic)
 * Domain plugins can replace this with branded content
 */
function DefaultEmptyState() {
  return (
    <div className="flex-1 flex items-center justify-center">
      <p className="text-gray-400 text-center">
        Start a conversation.<br />
        Ask any question to begin.
      </p>
    </div>
  )
}
