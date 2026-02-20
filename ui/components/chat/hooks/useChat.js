import { useState, useCallback } from 'react'
import { useMessages } from './useMessages'
import { useTickerSearch } from './useTickerSearch'
import { useStreamingAnalysis } from '@/hooks/useStreamingAnalysis'
import { runGraph } from '@/lib/utils/apiClient'

const HORIZON_PROFILES = {
  short: "short_spec",
  medium: "balanced_mid",
  long: "trend_follow"
}

const STREAMING_ENABLED = process.env.NEXT_PUBLIC_STREAMING_ENABLED !== 'false' // Default true

export function useChat() {
  const { messages, isTyping, setIsTyping, addUserMessage, addAIMessage, updateLastMessage } = useMessages()
  const { searchTickers, validateTicker, searchResults, isSearching } = useTickerSearch()
  const { thinkingSteps, isStreaming, streamError, startStreaming } = useStreamingAnalysis()
  
  const [activeHorizon, setActiveHorizon] = useState('short')
  const [confirmedTickers, setConfirmedTickers] = useState([])
  
  const sendMessage = useCallback(async (text, tickers = [], options = {}) => {
    if (!text.trim()) return
    
    // Add user message
    addUserMessage(text, tickers)
    
    // Add placeholder AI message with streaming capability
    setIsTyping(true)
    const messageIndex = messages.length + 1 // Track which message to update
    addAIMessage('', null, { isStreaming: true, thinkingSteps: [] })
    
    // Set up listener for thinking steps updates
    const updateThinkingSteps = (steps) => {
      updateLastMessage({
        thinkingSteps: steps,
        isStreaming: true
      })
    }
    
    // Simulate thinking steps for non-streaming mode
    // Vitruvian-inspired geometric Unicode icons (divine proportions)
    const simulateThinkingSteps = async () => {
      const steps = [
        { id: 1, emoji: '◈', label: 'Parsing intent & context', status: 'active', duration: 600 },
        { id: 2, emoji: '⊕', label: 'Resolving tickers', status: 'pending', duration: 700 },
        { id: 3, emoji: '◉', label: 'Retrieving market data', status: 'pending', duration: 900 },
        { id: 4, emoji: '△', label: 'Computing z-scores', status: 'pending', duration: 1100 },
        { id: 5, emoji: '◆', label: 'Running Neural Engine', status: 'pending', duration: 1300 },
        { id: 6, emoji: '⬡', label: 'Generating VEE narrative', status: 'pending', duration: 1000 },
        { id: 7, emoji: '⊞', label: 'Finalizing response', status: 'pending', duration: 800 }
      ]
      
      for (let i = 0; i < steps.length; i++) {
        const updatedSteps = steps.map((step, idx) => ({
          ...step,
          status: idx < i ? 'complete' : idx === i ? 'active' : 'pending'
        }))
        updateThinkingSteps(updatedSteps)
        
        // Variable realistic timing per step
        await new Promise(resolve => setTimeout(resolve, steps[i].duration))
        
        // Last step: show sub-states for entertainment
        if (i === steps.length - 1) {
          const finalSubStates = [
            'Synthesizing insights',
            'Polishing narrative',
            'Almost there'
          ]
          for (const subLabel of finalSubStates) {
            updatedSteps[i] = { ...updatedSteps[i], label: subLabel }
            updateThinkingSteps(updatedSteps)
            await new Promise(resolve => setTimeout(resolve, 400))
          }
        }
      }
    }
    
    try {
      if (STREAMING_ENABLED) {
        // Start simulated steps immediately
        simulateThinkingSteps()
        
        // Try streaming endpoint
        const result = await startStreaming(text, 'user_1', tickers, options, updateThinkingSteps)
        
        if (result) {
          updateLastMessage({
            text: result.narrative || 'Analysis complete',
            finalState: result,
            isComplete: true,
            isStreaming: false,
            thinkingSteps: []
          })
        } else {
          // Streaming completed without final state (fallback to regular)
          const result = await runGraph(text, 'user_1', tickers, undefined, options)
          updateLastMessage({
            text: result.narrative || 'Analysis complete',
            finalState: result,
            isComplete: true,
            isStreaming: false,
            thinkingSteps: []
          })
        }
      } else {
        // Use regular endpoint (no streaming)
        const result = await runGraph(text, 'user_1', tickers, undefined, options)
        updateLastMessage({
          text: result.narrative || 'Analysis complete',
          finalState: result,
          isComplete: true,
          isStreaming: false,
          thinkingSteps: []
        })
      }
    } catch (error) {
      updateLastMessage({
        text: 'Sorry, something went wrong.',
        error: error,
        isComplete: true,
        isStreaming: false,
        thinkingSteps: []
      })
    } finally {
      setIsTyping(false)
    }
  }, [activeHorizon, addUserMessage, addAIMessage, updateLastMessage, setIsTyping, startStreaming, messages.length])
  
  return {
    // State
    messages,
    isTyping,
    activeHorizon,
    confirmedTickers,
    searchResults,
    isSearching,
    thinkingSteps,
    isStreaming,
    streamError,
    
    // Actions
    sendMessage,
    setActiveHorizon,
    setConfirmedTickers,
    searchTickers,
    validateTicker
  }
}