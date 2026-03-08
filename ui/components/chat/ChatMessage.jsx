// components/chat/ChatMessage.jsx
// Domain-Agnostic Chat Message — Vitruvyan Core
// Last updated: Feb 28, 2026
//
// Renders a single message bubble (user or AI).
// No portfolio banners, no trading bubbles, no ticker headers.
// Domain plugins inject via extensions (ChatMessageExtensions).
'use client'

import { Circle } from 'lucide-react'
import { VitruvyanResponseRenderer } from '../response/VitruvyanResponseRenderer'
import { ThinkingSteps } from './ThinkingSteps'
import { MessageFeedback } from './MessageFeedback'

const MESSAGE_STYLES = {
  user: 'bg-gray-100 border border-gray-200 text-gray-900',
  ai: 'bg-blue-50 border border-blue-100 text-gray-900',
  processing: 'bg-blue-50 border border-blue-200 text-gray-900',
  error: 'bg-red-50 border border-red-200 text-gray-900'
}

export function ChatMessage({
  message,
  onFollowUpClick,
  onEntityClick,
  assistantName = 'Vitruvyan',
  extensions = {},
  currentFeedback = null,
  onFeedback,
}) {
  const { sender, text, uiPayload, finalState, isComplete, error, isStreaming, thinkingSteps } = message

  const isUser = sender === 'user'
  const isProcessing = !isComplete && !error
  const bubbleClass = error
    ? MESSAGE_STYLES.error
    : isProcessing
    ? MESSAGE_STYLES.processing
    : MESSAGE_STYLES[sender]

  // Domain plugin can provide custom assistant icon
  const AssistantIcon = extensions?.message?.assistantIcon || DefaultAssistantIcon

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-[85%] rounded-2xl p-4 ${bubbleClass} transition-all duration-300`}>
        {/* Avatar */}
        <div className="flex items-center gap-2 mb-2">
          {isUser ? (
            <div className="w-4 h-4 rounded-full bg-gray-400" />
          ) : (
            <AssistantIcon />
          )}
          <span className="text-xs font-medium text-gray-500">
            {isUser ? 'You' : (extensions?.message?.assistantName || assistantName)}
          </span>
        </div>

        {/* Content */}
        {isUser ? (
          <p className="text-sm">{text}</p>
        ) : uiPayload ? (
          <div>
            {/* Domain plugin: header component (e.g., AnalysisHeader) */}
            {extensions?.message?.headerComponent && (
              typeof extensions.message.headerComponent === 'function'
                ? extensions.message.headerComponent({ message })
                : extensions.message.headerComponent
            )}

            {/* Response rendered via contract-conformant payload */}
            <VitruvyanResponseRenderer
              response={uiPayload}
              onFollowUpClick={onFollowUpClick}
            />

            {/* Domain plugin: footer component (e.g., AdvisorInsight) */}
            {extensions?.message?.footerComponent && (
              typeof extensions.message.footerComponent === 'function'
                ? extensions.message.footerComponent({ message })
                : extensions.message.footerComponent
            )}
          </div>
        ) : finalState ? (
          <div>
            {/* finalState exists but no uiPayload — adapter not applied yet */}
            <p className="text-sm">{finalState.narrative || text || 'Analysis complete.'}</p>
          </div>
        ) : isStreaming || thinkingSteps?.length > 0 ? (
          <ThinkingSteps steps={thinkingSteps || []} isStreaming={isStreaming} />
        ) : (
          <p className="text-sm">{text}</p>
        )}

        {/* Feedback (thumbs up/down) — only for completed AI messages */}
        {onFeedback && (
          <MessageFeedback
            message={message}
            currentFeedback={currentFeedback}
            onFeedback={onFeedback}
          />
        )}
      </div>
    </div>
  )
}

/**
 * Default assistant icon (domain-agnostic geometric circle)
 */
function DefaultAssistantIcon() {
  return (
    <div className="relative w-4 h-4">
      <Circle size={16} className="text-blue-600 absolute inset-0" strokeWidth={2} />
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="w-1 h-1 bg-blue-600 rounded-full" />
      </div>
    </div>
  )
}
