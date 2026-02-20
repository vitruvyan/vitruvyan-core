'use client'

import { useEffect, useRef, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useKeycloak } from '@/contexts/KeycloakContext'
import { useChat } from './hooks'
import { ChatMessages } from './ChatMessages'
import { ChatInput } from './ChatInput'
import { usePortfolioCanvas } from '@/hooks/usePortfolioCanvas'
import { useTradingOrder } from '@/hooks/useTradingOrder'

export default function Chat({ 
  initialQuestion = '', 
  initialTickers = [],
  isVisible = true,
  isSidebar = false,
  onAnalysisComplete = null 
}) {
  const { authenticated, userInfo } = useKeycloak()
  const router = useRouter()
  
  // Trading order hook (Feb 4, 2026 - Refactored from component)
  const { executeOrder: executeOrderBase } = useTradingOrder()
  
  const {
    messages,
    isTyping,
    confirmedTickers,
    sendMessage,
    setConfirmedTickers,
    thinkingSteps,
    isStreaming
  } = useChat()
  
  // ✅ REAL USER ID from Keycloak (Feb 4, 2026 - Fixed async loading)
  // Wait for Keycloak to load, then use UUID (sub claim)
  const [userId, setUserId] = useState(null)
  
  useEffect(() => {
    if (authenticated && userInfo?.sub) {
      setUserId(userInfo.sub)
      console.log('[Chat] User authenticated:', { sub: userInfo.sub, username: userInfo.preferred_username })
    } else if (!authenticated) {
      // Anonymous users not allowed for portfolio
      setUserId(null)
      console.log('[Chat] User not authenticated - portfolio disabled')
    }
  }, [authenticated, userInfo])
  
  // Portfolio canvas state
  const {
    isOpen: isPortfolioOpen,
    portfolioData,
    loading: portfolioLoading,
    error: portfolioError,
    openCanvas,
    closeCanvas,
    updateCurrentTicker
  } = usePortfolioCanvas(userId)
  
  // Track currently analyzed ticker for highlighting
  const [currentAnalyzedTicker, setCurrentAnalyzedTicker] = useState(null)
  
  // Auto-submit initial question on mount
  const hasSubmittedInitial = useRef(false)
  
  useEffect(() => {
    if (initialQuestion && !hasSubmittedInitial.current && isVisible) {
      hasSubmittedInitial.current = true
      // Set initial tickers if provided
      if (initialTickers.length > 0) {
        setConfirmedTickers(initialTickers)
      }
      // Submit the initial question
      sendMessage(initialQuestion, initialTickers)
    }
  }, [initialQuestion, initialTickers, isVisible, sendMessage, setConfirmedTickers])
  
  // Notify parent when analysis completes
  useEffect(() => {
    if (onAnalysisComplete && messages.length > 0) {
      const lastMessage = messages[messages.length - 1]
      if (lastMessage.sender === 'ai' && lastMessage.finalState) {
        onAnalysisComplete(lastMessage.finalState)
      }
    }
  }, [messages, onAnalysisComplete])
  
  // Update current analyzed ticker for portfolio highlighting
  useEffect(() => {
    if (messages.length > 0) {
      const lastMessage = messages[messages.length - 1]
      if (lastMessage.sender === 'ai' && lastMessage.finalState?.tickers) {
        const tickers = lastMessage.finalState.tickers
        // Highlight first ticker if single analysis, or first ticker in comparison
        setCurrentAnalyzedTicker(tickers[0] || null)
        updateCurrentTicker(tickers[0] || null)
      }
    }
  }, [messages, updateCurrentTicker])
  
  const handleSend = (text, tickers, options = {}) => {
    sendMessage(text, tickers, options)
  }
  
  const handleFollowUpClick = (question) => {
    sendMessage(question, confirmedTickers)
  }
  
  const handleTickerClick = (ticker) => {
    // Navigate to single ticker analysis
    sendMessage(`Analyze ${ticker}`, [ticker])
  }
  
  const handleTickerConfirm = (ticker) => {
    if (!confirmedTickers.includes(ticker)) {
      setConfirmedTickers([...confirmedTickers, ticker])
    }
  }
  
  const handleTickerRemove = (ticker) => {
    setConfirmedTickers(confirmedTickers.filter(t => t !== ticker))
  }
  
  const handlePortfolioTickerClick = (ticker) => {
    // Close portfolio banner and analyze ticker
    closeCanvas()
    sendMessage(`Analyze ${ticker}`, [ticker])
  }
  
  const handleViewPortfolio = () => {
    // Navigate to full portfolio page (Feb 4, 2026)
    router.push('/portfolio')
  }
  
  // Wrapper for executeOrder that opens portfolio bubble on success
  const executeOrder = async (orderData) => {
    const result = await executeOrderBase(orderData)
    
    // Open portfolio bubble after successful order (Feb 4, 2026)
    if (result?.success) {
      console.log('[Chat] Order successful, opening portfolio bubble')
      openCanvas()
    }
    
    return result
  }

  return (
    <div className="flex flex-col min-h-screen bg-white">
      {/* Messages Area */}
      <div className="flex-1">
        <div className="max-w-7xl mx-auto">
          <ChatMessages 
            messages={messages}
            onFollowUpClick={handleFollowUpClick}
            onTickerClick={handleTickerClick}
            onOpenPortfolio={openCanvas}
            isPortfolioOpen={isPortfolioOpen}
            portfolioData={portfolioData}
            portfolioLoading={portfolioLoading}
            portfolioError={portfolioError}
            onClosePortfolio={closeCanvas}
            onPortfolioTickerClick={handlePortfolioTickerClick}
            currentAnalyzedTicker={currentAnalyzedTicker}
            onOrderExecuted={executeOrder}
            onViewPortfolio={handleViewPortfolio}
          />
        </div>
      </div>
      
      {/* Input Area */}
      <div className="max-w-7xl mx-auto w-full">
        <ChatInput
          onSend={handleSend}
          isTyping={isTyping}
          confirmedTickers={confirmedTickers}
          onTickerConfirm={handleTickerConfirm}
          onTickerRemove={handleTickerRemove}
        />
      </div>
    </div>
  )
}