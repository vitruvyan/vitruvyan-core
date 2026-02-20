'use client'

import { useState, useRef, useCallback } from 'react'
import { Send, TrendingUp } from 'lucide-react'
import { AllocationStrategySelector } from './AllocationStrategySelector'

export function ChatInput({ 
  onSend, 
  isTyping, 
  confirmedTickers,
  onTickerConfirm,
  onTickerRemove
}) {
  const [inputValue, setInputValue] = useState('')
  const [showAllocationSelector, setShowAllocationSelector] = useState(false)
  const [selectedStrategy, setSelectedStrategy] = useState(null)
  const textareaRef = useRef(null)
  
  const handleSubmit = useCallback(() => {
    if (!inputValue.trim() || isTyping) return
    
    // Check if user wants allocation
    const isAllocationRequest = inputValue.toLowerCase().includes('allocate') || 
                               inputValue.toLowerCase().includes('allocare')
    
    if (isAllocationRequest && confirmedTickers.length > 0) {
      setShowAllocationSelector(true)
      return
    }
    
    onSend(inputValue, confirmedTickers)
    setInputValue('')
  }, [inputValue, confirmedTickers, onSend])
  
  const handleStrategySelect = useCallback((strategy) => {
    setSelectedStrategy(strategy)
    setShowAllocationSelector(false)
    // Send message with strategy
    onSend(inputValue, confirmedTickers, { strategy })
    setInputValue('')
  }, [inputValue, confirmedTickers, onSend])
  
  const handleStrategyCancel = useCallback(() => {
    setShowAllocationSelector(false)
  }, [])
  
  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }, [handleSubmit])
  
  return (
    <div className="border-t bg-white p-4">
      {/* Confirmed Tickers Pills */}
      {confirmedTickers.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-2">
          {confirmedTickers.map(ticker => (
            <span 
              key={ticker}
              className="inline-flex items-center gap-1 px-2 py-1 bg-emerald-100 text-emerald-700 rounded-full text-xs font-medium"
            >
              <TrendingUp size={12} />
              {ticker}
              <button 
                onClick={() => onTickerRemove(ticker)}
                className="ml-1 hover:text-emerald-900"
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}
      {/* Allocation Strategy Selector */}
      {showAllocationSelector && (
        <div className="mb-4">
          <AllocationStrategySelector
            onStrategySelect={handleStrategySelect}
            onCancel={handleStrategyCancel}
            selectedStrategy={selectedStrategy}
          />
        </div>
      )}
      
      {/* Input Area */}
      <div className="flex items-center gap-3">
        <textarea
          ref={textareaRef}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type a ticker or question..."
          className="flex-1 resize-none border border-gray-200 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
          rows={1}
          disabled={isTyping}
        />
        
        <button
          onClick={handleSubmit}
          disabled={!inputValue.trim() || isTyping}
          className="p-3 bg-emerald-600 text-white rounded-xl hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <Send size={20} />
        </button>
      </div>
    </div>
  )
}