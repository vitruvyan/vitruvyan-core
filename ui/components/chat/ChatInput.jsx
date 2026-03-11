// components/chat/ChatInput.jsx
// Domain-Agnostic Chat Input — Vitruvyan Core
// Last updated: Feb 28, 2026
//
// No tickers, no allocation selectors, no domain-specific UI.
// Domain plugins inject via extensions prop (ChatInputExtensions).
'use client'

import { useState, useRef, useCallback } from 'react'
import { Send } from 'lucide-react'
import { DocumentUpload } from './DocumentUpload'

export function ChatInput({
  onSend,
  isProcessing,
  selectedEntities = [],
  onEntityAdd,
  onEntityRemove,
  placeholder = 'Ask a question...',
  extensions = {},
  // Document upload props
  attachedFile = null,
  onFileSelect,
  onFileClear,
  persistDocument = false,
  onPersistChange,
}) {
  const [inputValue, setInputValue] = useState('')
  const textareaRef = useRef(null)

  const handleSubmit = useCallback(() => {
    if (!inputValue.trim() || isProcessing) return
    onSend(inputValue, selectedEntities)
    setInputValue('')
  }, [inputValue, selectedEntities, isProcessing, onSend])

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }, [handleSubmit])

  // Domain plugin can provide a custom entity pill renderer
  const renderEntityPill = extensions?.entityPillRenderer || defaultEntityPill

  return (
    <div className="border-t bg-white p-4">
      {/* Selected Entities (domain-agnostic pills) */}
      {selectedEntities.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-2">
          {selectedEntities.map(entity => renderEntityPill(entity, onEntityRemove))}
        </div>
      )}

      {/* Domain plugin action buttons (optional) */}
      {extensions?.actionButtons?.filter(b => b.visible !== false).map(button => (
        <button
          key={button.id}
          onClick={button.onClick}
          className="mb-2 mr-2 px-3 py-1 text-xs rounded-lg bg-gray-100 hover:bg-gray-200 text-gray-700 transition-colors"
        >
          {button.label}
        </button>
      ))}

      {/* Input Area */}
      <div className="flex items-center gap-3">
        {/* Document upload */}
        {onFileSelect && (
          <DocumentUpload
            file={attachedFile}
            onFileSelect={onFileSelect}
            onFileClear={onFileClear}
            persistDocument={persistDocument}
            onPersistChange={onPersistChange}
            disabled={isProcessing}
          />
        )}

        <textarea
          ref={textareaRef}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="flex-1 resize-none border border-gray-200 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          rows={1}
          disabled={isProcessing}
        />

        <button
          onClick={handleSubmit}
          disabled={!inputValue.trim() || isProcessing}
          className="p-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <Send size={20} />
        </button>
      </div>
    </div>
  )
}

/**
 * Default entity pill renderer (domain-agnostic)
 * Domain plugins can replace this with branded pills
 */
function defaultEntityPill(entity, onRemove) {
  return (
    <span
      key={entity}
      className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-medium"
    >
      {entity}
      <button
        onClick={() => onRemove(entity)}
        className="ml-1 hover:text-blue-900"
      >
        ×
      </button>
    </span>
  )
}
