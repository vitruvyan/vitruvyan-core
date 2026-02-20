'use client'

import { useRef, useEffect } from 'react'
import { ChatMessage } from './ChatMessage'

export function ChatMessages({ 
  messages, 
  onFollowUpClick, 
  onTickerClick, 
  onOpenPortfolio,
  isPortfolioOpen,
  portfolioData,
  portfolioLoading,
  portfolioError,
  onClosePortfolio,
  onPortfolioTickerClick,
  currentAnalyzedTicker,
  onOrderExecuted, // Trading order callback (Feb 1, 2026)
  onViewPortfolio // Portfolio navigation callback (Feb 4, 2026)
}) {
  const containerRef = useRef(null)
  
  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight
    }
  }, [messages.length])
  
  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <p className="text-gray-400 text-center">
          Ask me about any stock.<br />
          Try: "Analyze AAPL" or "Compare NVDA vs AMD"
        </p>
      </div>
    )
  }
  
  // Find index of last user message (for portfolio expansion)
  const lastUserMessageIndex = messages.reduce((lastIndex, msg, index) => {
    return msg.sender === 'user' ? index : lastIndex
  }, -1)
  
  return (
    <div ref={containerRef} className="flex-1 p-4 space-y-4">
      {messages.map((msg, index) => (
        <ChatMessage
          key={msg.id}
          message={msg}
          onFollowUpClick={onFollowUpClick}
          onTickerClick={onTickerClick}
          onOpenPortfolio={onOpenPortfolio}
          isPortfolioOpen={isPortfolioOpen}
          portfolioData={portfolioData}
          portfolioLoading={portfolioLoading}
          portfolioError={portfolioError}
          onClosePortfolio={onClosePortfolio}
          onPortfolioTickerClick={onPortfolioTickerClick}
          currentAnalyzedTicker={currentAnalyzedTicker}
          isLastUserMessage={index === lastUserMessageIndex}
          onOrderExecuted={onOrderExecuted}
          onViewPortfolio={onViewPortfolio}
        />
      ))}
    </div>
  )
}