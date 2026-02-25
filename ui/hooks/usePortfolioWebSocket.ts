/**
 * usePortfolioWebSocket - Real-Time Portfolio Canvas Integration
 * 
 * WebSocket hook for receiving real-time portfolio updates from Shadow Traders API.
 * 
 * Features:
 * - Initial portfolio snapshot on connection
 * - Real-time Guardian insights (risk alerts, opportunities, rebalancing)
 * - Real-time Autopilot actions (buy/sell proposals)
 * - Real-time portfolio value updates
 * - Multi-device support (multiple connections per user)
 * - Automatic reconnection with exponential backoff
 * - Toast notifications for important events
 * - Ping/pong keep-alive (30s timeout)
 * 
 * Task 26.2: Frontend WebSocket Client (Jan 26, 2026)
 * Backend: vitruvyan_shadow_traders:8020 (exposed on port 8025)
 * 
 * Usage:
 * ```tsx
 * const { snapshot, insights, actions, connected, reconnecting } = usePortfolioWebSocket('user_123')
 * 
 * if (!connected) return <LoadingSpinner />
 * 
 * return (
 *   <div>
 *     <PortfolioValue value={snapshot?.total_value} />
 *     <GuardianTimeline insights={insights} />
 *     <AutopilotActions actions={actions} />
 *   </div>
 * )
 * ```
 */

import { useEffect, useState, useRef, useCallback } from 'react'
import { toast } from 'sonner'

// ============================================================================
// TypeScript Interfaces (Task 26.2.1)
// ============================================================================

/**
 * Portfolio Position
 */
export interface PortfolioPosition {
  ticker: string
  company_name?: string
  quantity: number
  avg_cost: number
  current_price: number
  market_value: number
  unrealized_pnl: number
  unrealized_pnl_pct: number
  weight: number
}

/**
 * Portfolio Snapshot (initial state on WebSocket connect)
 */
export interface PortfolioSnapshot {
  user_id: string
  cash_balance: number
  positions: PortfolioPosition[]
  total_value: number
  total_invested: number
  total_pnl: number
  total_pnl_pct: number
  position_count: number
  last_updated: string
}

/**
 * Guardian Insight (risk alerts, opportunities, rebalancing suggestions)
 */
export interface GuardianInsight {
  insight_id: number
  user_id: string
  insight_type: 'risk_alert' | 'opportunity' | 'rebalance' | 'concentration' | 'correlation'
  category: 'PROTECT' | 'IMPROVE' | 'UNDERSTAND'
  severity: 'critical' | 'high' | 'medium' | 'low'
  title: string
  description: string
  affected_tickers: string[]
  recommendations: string[]
  vee_explanation?: string
  created_at: string
  expires_at?: string
}

/**
 * Autopilot Action (buy/sell proposal)
 */
export interface AutopilotAction {
  action_id: string
  user_id: string
  action_type: 'buy' | 'sell' | 'rebalance' | 'hedge'
  ticker: string
  quantity: number
  price_limit?: number
  rationale: string
  vee_explanation?: string
  guardian_insight_id?: number
  proposed_at: string
  expires_at: string
  status: 'pending' | 'approved' | 'rejected' | 'expired'
}

/**
 * Portfolio Value Update (real-time market value changes)
 */
export interface PortfolioValueUpdate {
  user_id: string
  total_value: number
  change_amount: number
  change_pct: number
  timestamp: string
}

/**
 * WebSocket Message Types (Server → Client)
 */
export type WebSocketMessage =
  | { type: 'portfolio.snapshot.initial'; data: PortfolioSnapshot }
  | { type: 'guardian.insight.new'; data: GuardianInsight; timestamp: number }
  | { type: 'autopilot.action.proposed'; data: AutopilotAction; timestamp: number }
  | { type: 'portfolio.value.updated'; data: PortfolioValueUpdate; timestamp: number }
  | { type: 'heartbeat'; timestamp: number }

/**
 * Connection State
 */
export type ConnectionState = 'connecting' | 'connected' | 'disconnected' | 'reconnecting'

/**
 * Hook Return Type
 */
export interface UsePortfolioWebSocketReturn {
  // State
  snapshot: PortfolioSnapshot | null
  insights: GuardianInsight[]
  actions: AutopilotAction[]
  
  // Connection
  connected: boolean
  connectionState: ConnectionState
  reconnecting: boolean
  reconnectAttempts: number
  
  // Methods
  clearInsights: () => void
  clearActions: () => void
  manualReconnect: () => void
}

// ============================================================================
// Configuration
// ============================================================================

const WEBSOCKET_URL = process.env.NEXT_PUBLIC_SHADOW_TRADERS_WS_URL || 'ws://localhost:8025'
const PING_INTERVAL = 30000 // 30s (matches backend timeout)
const MAX_RECONNECT_ATTEMPTS = 10
const INITIAL_RECONNECT_DELAY = 1000 // 1s
const MAX_RECONNECT_DELAY = 30000 // 30s

// ============================================================================
// Hook Implementation (Task 26.2.2)
// ============================================================================

export function usePortfolioWebSocket(userId: string): UsePortfolioWebSocketReturn {
  // ========== State ==========
  const [snapshot, setSnapshot] = useState<PortfolioSnapshot | null>(null)
  const [insights, setInsights] = useState<GuardianInsight[]>([])
  const [actions, setActions] = useState<AutopilotAction[]>([])
  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected')
  const [reconnectAttempts, setReconnectAttempts] = useState(0)
  
  // ========== Refs (Task 26.2.3 - Reconnection Logic) ==========
  const wsRef = useRef<WebSocket | null>(null)
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectDelayRef = useRef<number>(INITIAL_RECONNECT_DELAY)
  const isMountedRef = useRef<boolean>(true)
  
  // ========== Helper: Calculate Exponential Backoff ==========
  const calculateReconnectDelay = useCallback((attempt: number): number => {
    // Exponential backoff: 1s, 2s, 4s, 8s, 16s, 30s (max)
    const delay = Math.min(
      INITIAL_RECONNECT_DELAY * Math.pow(2, attempt),
      MAX_RECONNECT_DELAY
    )
    return delay
  }, [])
  
  // ========== Helper: Clear Timers ==========
  const clearTimers = useCallback(() => {
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current)
      pingIntervalRef.current = null
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
  }, [])
  
  // ========== Helper: Start Ping Interval ==========
  const startPingInterval = useCallback(() => {
    clearTimers()
    
    pingIntervalRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send('ping')
      }
    }, PING_INTERVAL)
  }, [clearTimers])
  
  // ========== Helper: Schedule Reconnect (Task 26.2.3) ==========
  const scheduleReconnect = useCallback((attempt: number) => {
    if (!isMountedRef.current || attempt >= MAX_RECONNECT_ATTEMPTS) {
      if (attempt >= MAX_RECONNECT_ATTEMPTS) {
        toast.error('Portfolio WebSocket', {
          description: 'Maximum reconnection attempts reached. Please refresh the page.',
          duration: 10000,
          action: {
            label: 'Refresh',
            onClick: () => window.location.reload()
          }
        })
        setConnectionState('disconnected')
      }
      return
    }
    
    const delay = calculateReconnectDelay(attempt)
    reconnectDelayRef.current = delay
    
    console.log(`🔄 Scheduling reconnect attempt ${attempt + 1}/${MAX_RECONNECT_ATTEMPTS} in ${delay}ms`)
    setConnectionState('reconnecting')
    
    reconnectTimeoutRef.current = setTimeout(() => {
      if (isMountedRef.current) {
        setReconnectAttempts(attempt + 1)
        connect()
      }
    }, delay)
  }, [calculateReconnectDelay])
  
  // ========== Message Handlers (Task 26.2.4 - Toast Notifications) ==========
  
  const handleInitialSnapshot = useCallback((data: PortfolioSnapshot) => {
    setSnapshot(data)
    console.log('✅ Received initial portfolio snapshot:', {
      user_id: data.user_id,
      total_value: data.total_value,
      positions: data.position_count,
      cash: data.cash_balance
    })
  }, [])
  
  const handleGuardianInsight = useCallback((data: GuardianInsight) => {
    setInsights(prev => [data, ...prev])
    
    // Toast notification with severity-based styling (Task 26.2.4)
    const severityEmoji = {
      critical: '🚨',
      high: '⚠️',
      medium: '💡',
      low: 'ℹ️'
    }[data.severity]
    
    const severityToast = {
      critical: toast.error,
      high: toast.warning,
      medium: toast.info,
      low: toast
    }[data.severity] || toast
    
    severityToast(`${severityEmoji} Guardian Insight: ${data.title}`, {
      description: data.recommendations[0] || data.description,
      duration: data.severity === 'critical' ? 10000 : 5000,
      action: data.severity === 'critical' ? {
        label: 'View Details',
        onClick: () => {
          // TODO: Navigate to insight detail view
          console.log('Navigate to insight:', data.insight_id)
        }
      } : undefined
    })
    
    console.log(`🛡️ New Guardian insight: ${data.insight_type} (${data.severity})`, data)
  }, [])
  
  const handleAutopilotAction = useCallback((data: AutopilotAction) => {
    setActions(prev => [data, ...prev])
    
    // Toast notification (Task 26.2.4)
    const actionEmoji = {
      buy: '📈',
      sell: '📉',
      rebalance: '⚖️',
      hedge: '🛡️'
    }[data.action_type] || '🤖'
    
    toast.info(`${actionEmoji} Autopilot Action: ${data.action_type.toUpperCase()}`, {
      description: `${data.ticker} x${data.quantity} - ${data.rationale}`,
      duration: 7000,
      action: {
        label: 'Review',
        onClick: () => {
          // TODO: Navigate to action review modal
          console.log('Review action:', data.action_id)
        }
      }
    })
    
    console.log(`🤖 Autopilot action proposed: ${data.action_type} ${data.ticker}`, data)
  }, [])
  
  const handlePortfolioValueUpdate = useCallback((data: PortfolioValueUpdate) => {
    // Update total_value in snapshot
    setSnapshot(prev => prev ? { ...prev, total_value: data.total_value } : null)
    
    // Toast notification (Task 26.2.4)
    const changeSign = data.change_pct >= 0 ? '+' : ''
    const changeEmoji = data.change_pct >= 0 ? '📈' : '📉'
    
    toast(`${changeEmoji} Portfolio Value Updated`, {
      description: `$${data.total_value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} (${changeSign}${data.change_pct.toFixed(2)}%)`,
      duration: 3000
    })
    
    console.log(`💰 Portfolio value updated: $${data.total_value} (${changeSign}${data.change_pct}%)`)
  }, [])
  
  // ========== WebSocket Connection (Task 26.2.2 + 26.2.3) ==========
  
  const connect = useCallback(() => {
    // Prevent duplicate connections
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('⚠️ WebSocket already connected, skipping reconnection')
      return
    }
    
    try {
      setConnectionState('connecting')
      
      const url = `${WEBSOCKET_URL}/ws/portfolio/${userId}`
      console.log(`🔌 Connecting to WebSocket: ${url}`)
      
      const ws = new WebSocket(url)
      wsRef.current = ws
      
      // ========== Event: Open ==========
      ws.onopen = () => {
        if (!isMountedRef.current) return
        
        console.log('✅ WebSocket connected')
        setConnectionState('connected')
        setReconnectAttempts(0)
        reconnectDelayRef.current = INITIAL_RECONNECT_DELAY
        
        // Start ping/pong keep-alive
        startPingInterval()
        
        toast.success('Portfolio Canvas Connected', {
          description: 'Real-time updates active',
          duration: 2000
        })
      }
      
      // ========== Event: Message ==========
      ws.onmessage = (event) => {
        if (!isMountedRef.current) return
        
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          
          switch (message.type) {
            case 'portfolio.snapshot.initial':
              handleInitialSnapshot(message.data)
              break
            
            case 'guardian.insight.new':
              handleGuardianInsight(message.data)
              break
            
            case 'autopilot.action.proposed':
              handleAutopilotAction(message.data)
              break
            
            case 'portfolio.value.updated':
              handlePortfolioValueUpdate(message.data)
              break
            
            case 'heartbeat':
              // Silent keep-alive
              break
            
            default:
              console.warn('⚠️ Unknown WebSocket message type:', message)
          }
        } catch (error) {
          console.error('❌ Failed to parse WebSocket message:', error, event.data)
        }
      }
      
      // ========== Event: Error ==========
      ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error)
        setConnectionState('disconnected')
        
        toast.error('Portfolio WebSocket Error', {
          description: 'Connection failed. Retrying...',
          duration: 3000
        })
      }
      
      // ========== Event: Close (Task 26.2.3 - Reconnection) ==========
      ws.onclose = (event) => {
        if (!isMountedRef.current) return
        
        console.log(`🔌 WebSocket disconnected (code: ${event.code}, reason: ${event.reason || 'none'})`)
        clearTimers()
        setConnectionState('disconnected')
        
        // Schedule reconnection (if not intentional close)
        if (event.code !== 1000) { // 1000 = normal closure
          scheduleReconnect(reconnectAttempts)
        }
      }
      
      // ========== Handle "pong" responses ==========
      ws.addEventListener('message', (event) => {
        if (event.data === 'pong') {
          // Silent acknowledgment of ping/pong
        }
      })
      
    } catch (error) {
      console.error('❌ Failed to create WebSocket connection:', error)
      setConnectionState('disconnected')
      scheduleReconnect(reconnectAttempts)
    }
  }, [
    userId,
    reconnectAttempts,
    startPingInterval,
    scheduleReconnect,
    handleInitialSnapshot,
    handleGuardianInsight,
    handleAutopilotAction,
    handlePortfolioValueUpdate,
    clearTimers
  ])
  
  // ========== Public Methods ==========
  
  const clearInsights = useCallback(() => {
    setInsights([])
    console.log('🗑️ Cleared Guardian insights')
  }, [])
  
  const clearActions = useCallback(() => {
    setActions([])
    console.log('🗑️ Cleared Autopilot actions')
  }, [])
  
  const manualReconnect = useCallback(() => {
    console.log('🔄 Manual reconnection triggered')
    setReconnectAttempts(0)
    reconnectDelayRef.current = INITIAL_RECONNECT_DELAY
    
    if (wsRef.current) {
      wsRef.current.close()
    }
    
    connect()
  }, [connect])
  
  // ========== Effect: Mount/Unmount ==========
  
  useEffect(() => {
    isMountedRef.current = true
    
    if (userId) {
      connect()
    }
    
    return () => {
      isMountedRef.current = false
      clearTimers()
      
      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmounted')
        wsRef.current = null
      }
    }
  }, [userId, connect, clearTimers])
  
  // ========== Return ==========
  
  return {
    // State
    snapshot,
    insights,
    actions,
    
    // Connection
    connected: connectionState === 'connected',
    connectionState,
    reconnecting: connectionState === 'reconnecting',
    reconnectAttempts,
    
    // Methods
    clearInsights,
    clearActions,
    manualReconnect
  }
}
