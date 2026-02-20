'use client'

import { AlertCircle, RefreshCw } from 'lucide-react'

export function FallbackMessage({ error, onRetry }) {
  return (
    <div className="bg-red-50 border border-red-200 p-4 rounded-lg">
      <div className="flex items-start gap-3">
        <AlertCircle className="text-red-500 mt-0.5" size={20} />
        <div className="flex-1">
          <p className="text-sm font-medium text-red-800">Something went wrong</p>
          <p className="text-xs text-red-600 mt-1">
            {error?.message || 'Unable to process your request. Please try again.'}
          </p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="mt-3 inline-flex items-center gap-1.5 text-xs font-medium text-red-700 hover:text-red-900"
            >
              <RefreshCw size={14} />
              Try again
            </button>
          )}
        </div>
      </div>
    </div>
  )
}