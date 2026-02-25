/**
 * useStreamingAnalysis Hook
 * 
 * Manages Server-Sent Events (SSE) connection for real-time analysis streaming.
 * Shows Vitruvyan's "thinking process" step-by-step:
 * - Fetching ticker data
 * - Analyzing signals
 * - Computing rankings
 * - Writing compelling narrative
 */

import { useState, useCallback, useRef, useEffect } from 'react'

const STREAMING_STEPS = {
  intent_detection: { emoji: '◈', label: 'Parsing intent & context' },
  babel_emotion: { emoji: '◇', label: 'Analyzing sentiment' },
  semantic_grounding: { emoji: '◉', label: 'Retrieving semantic context' },
  weaver: { emoji: '⬡', label: 'Pattern weaving' },
  ticker_resolver: { emoji: '⊕', label: 'Resolving tickers' },
  sentiment_node: { emoji: '△', label: 'Scoring sentiment' },
  exec_node: { emoji: '◆', label: 'Neural Engine execution' },
  vee_engine: { emoji: '⬢', label: 'Generating VEE narrative' },
  compose: { emoji: '⊞', label: 'Composing final response' },
  comparison: { emoji: '⊜', label: 'Comparative analysis' },
  portfolio_analysis: { emoji: '⊠', label: 'Portfolio analysis' }
}

export function useStreamingAnalysis() {
  const [thinkingSteps, setThinkingSteps] = useState([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamError, setStreamError] = useState(null)
  const eventSourceRef = useRef(null)
  const abortControllerRef = useRef(null)

  const startStreaming = useCallback(async (inputText, userId, validatedTickers = [], options = {}, onStepsUpdate = null) => {
    // Close any existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
    }
    
    // Reset state
    setThinkingSteps([])
    setIsStreaming(true)
    setStreamError(null)
    
    // Create AbortController for fetch
    abortControllerRef.current = new AbortController()
    
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://161.97.140.157:8004'
      const response = await fetch(`${apiUrl}/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream'
        },
        body: JSON.stringify({
          input_text: inputText,
          user_id: userId,
          validated_tickers: validatedTickers,
          ...options
        }),
        signal: abortControllerRef.current.signal
      })

      if (!response.ok) {
        throw new Error(`Stream failed: ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let currentSteps = []

      while (true) {
        const { done, value } = await reader.read()
        
        if (done) {
          setIsStreaming(false)
          break
        }

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            
            if (data === '[DONE]') {
              setIsStreaming(false)
              break
            }

            try {
              const event = JSON.parse(data)
              
              if (event.type === 'node_start') {
                const stepConfig = STREAMING_STEPS[event.node] || {
                  emoji: '⚙️',
                  label: event.node.replace(/_/g, ' ')
                }
                
                const newStep = {
                  id: event.node + '_' + Date.now(),
                  node: event.node,
                  emoji: stepConfig.emoji,
                  label: stepConfig.label,
                  status: 'active',
                  timestamp: new Date().toISOString()
                }
                
                currentSteps = [...currentSteps, newStep]
                setThinkingSteps(currentSteps)
                
                // Notify callback
                if (onStepsUpdate) {
                  onStepsUpdate(currentSteps)
                }
              } else if (event.type === 'node_complete') {
                currentSteps = currentSteps.map(step => 
                  step.node === event.node && step.status === 'active'
                    ? { ...step, status: 'complete' }
                    : step
                )
                setThinkingSteps(currentSteps)
                
                // Notify callback
                if (onStepsUpdate) {
                  onStepsUpdate(currentSteps)
                }
              } else if (event.type === 'error') {
                setStreamError(event.message)
                setIsStreaming(false)
              } else if (event.type === 'final_state') {
                // Return final state for processing
                return event.data
              }
            } catch (parseError) {
              console.error('[useStreamingAnalysis] Parse error:', parseError)
            }
          }
        }
      }
    } catch (error) {
      if (error.name !== 'AbortError') {
        console.error('[useStreamingAnalysis] Stream error:', error)
        setStreamError(error.message)
      }
      setIsStreaming(false)
    }
    
    return null
  }, [])

  const stopStreaming = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }
    setIsStreaming(false)
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopStreaming()
    }
  }, [stopStreaming])

  return {
    thinkingSteps,
    isStreaming,
    streamError,
    startStreaming,
    stopStreaming
  }
}
