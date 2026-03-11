// components/chat/DocumentUpload.jsx
// Document Upload Widget — Vitruvyan Core
// Last updated: Mar 11, 2026
//
// Allows users to attach a document to their chat message.
// Optional checkbox to persist chunks in Qdrant for future RAG retrieval.
'use client'

import { useRef, useCallback } from 'react'
import { Paperclip, X, FileText } from 'lucide-react'
import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip'
import { useOnboardingTip, localizedTip } from '@/hooks/useOnboardingTip'

const UPLOAD_TIP = {
  en: 'Attach a document so Vitruvyan can answer questions about its content. Check "Save to memory" to remember it for future conversations.',
  it: 'Allega un documento per permettere a Vitruvyan di rispondere sul suo contenuto. Seleziona "Save to memory" per ricordarlo nelle conversazioni future.',
}

const ALLOWED_TYPES = [
  'text/plain',
  'text/markdown',
  'text/csv',
  'application/pdf',
  'application/json',
]
const MAX_SIZE = 5 * 1024 * 1024 // 5 MB

export function DocumentUpload({ file, onFileSelect, onFileClear, persistDocument, onPersistChange, disabled }) {
  const inputRef = useRef(null)
  const { shouldShow } = useOnboardingTip('doc_upload', 15)
  const tipText = localizedTip(UPLOAD_TIP)

  const handleClick = useCallback(() => {
    if (!disabled) inputRef.current?.click()
  }, [disabled])

  const handleChange = useCallback((e) => {
    const selected = e.target.files?.[0]
    if (!selected) return

    if (!ALLOWED_TYPES.includes(selected.type)) {
      alert(`Unsupported file type: ${selected.type}`)
      return
    }
    if (selected.size > MAX_SIZE) {
      alert('File too large (max 5 MB)')
      return
    }

    onFileSelect(selected)
    // Reset input so the same file can be re-selected
    e.target.value = ''
  }, [onFileSelect])

  return (
    <div className="flex items-center gap-2">
      {/* Hidden file input */}
      <input
        ref={inputRef}
        type="file"
        accept=".txt,.md,.csv,.pdf,.json"
        onChange={handleChange}
        className="hidden"
      />

      {/* Attach button */}
      {shouldShow ? (
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              type="button"
              onClick={handleClick}
              disabled={disabled}
              className="p-2 text-gray-500 hover:text-blue-600 disabled:opacity-50 transition-colors"
              title="Attach document"
            >
              <Paperclip size={20} />
            </button>
          </TooltipTrigger>
          <TooltipContent side="top" className="max-w-[280px]">
            {tipText}
          </TooltipContent>
        </Tooltip>
      ) : (
        <button
          type="button"
          onClick={handleClick}
          disabled={disabled}
          className="p-2 text-gray-500 hover:text-blue-600 disabled:opacity-50 transition-colors"
          title="Attach document"
        >
          <Paperclip size={20} />
        </button>
      )}

      {/* File preview pill + persist checkbox */}
      {file && (
        <div className="flex items-center gap-2 px-3 py-1 bg-blue-50 border border-blue-200 rounded-lg text-sm">
          <FileText size={14} className="text-blue-600" />
          <span className="text-blue-700 max-w-[150px] truncate">{file.name}</span>
          <span className="text-blue-400 text-xs">
            ({(file.size / 1024).toFixed(0)} KB)
          </span>

          {/* Persist to memory checkbox */}
          <label className="flex items-center gap-1 ml-2 text-xs text-gray-600 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={persistDocument}
              onChange={(e) => onPersistChange(e.target.checked)}
              className="rounded border-gray-300"
            />
            Save to memory
          </label>

          {/* Clear button */}
          <button
            type="button"
            onClick={onFileClear}
            className="ml-1 text-gray-400 hover:text-red-500 transition-colors"
            title="Remove attachment"
          >
            <X size={14} />
          </button>
        </div>
      )}
    </div>
  )
}
