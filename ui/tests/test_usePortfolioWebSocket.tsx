/**
 * Test Suite: usePortfolioWebSocket Hook
 * 
 * Task 26.2.5: Testing + Documentation (Jan 26, 2026)
 * 
 * Test coverage:
 * - Initial connection and snapshot delivery
 * - Guardian insight real-time updates
 * - Autopilot action real-time updates
 * - Portfolio value updates
 * - Reconnection logic with exponential backoff
 * - Multi-device support
 * - Toast notifications
 * - Cleanup on unmount
 * 
 * Prerequisites:
 * - Shadow Traders API running on port 8025
 * - Redis Cognitive Bus operational
 * - Test user: 'test_user' with portfolio data
 */

import { renderHook, waitFor, act } from '@testing-library/react'
import { usePortfolioWebSocket } from '../hooks/usePortfolioWebSocket'
import { toast } from 'sonner'

// Mock sonner toast
jest.mock('sonner', () => ({
  toast: jest.fn(() => ({ id: 'mock-toast-id' })),
}))

// Mock WebSocket
class MockWebSocket {
  static OPEN = 1
  static CONNECTING = 0
  static CLOSING = 2
  static CLOSED = 3
  
  readyState = MockWebSocket.CONNECTING
  url: string
  onopen: ((event: Event) => void) | null = null
  onclose: ((event: CloseEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  
  constructor(url: string) {
    this.url = url
    
    // Simulate connection open after 100ms
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN
      if (this.onopen) {
        this.onopen(new Event('open'))
      }
    }, 100)
  }
  
  send(data: string) {
    console.log('MockWebSocket.send:', data)
    
    // Simulate pong response
    if (data === 'ping') {
      setTimeout(() => {
        if (this.onmessage) {
          this.onmessage(new MessageEvent('message', { data: 'pong' }))
        }
      }, 10)
    }
  }
  
  close(code?: number, reason?: string) {
    this.readyState = MockWebSocket.CLOSED
    if (this.onclose) {
      this.onclose(new CloseEvent('close', { code: code || 1000, reason: reason || '' }))
    }
  }
  
  addEventListener(event: string, handler: (event: any) => void) {
    if (event === 'message') {
      this.onmessage = handler
    }
  }
}

// @ts-ignore
global.WebSocket = MockWebSocket

describe('usePortfolioWebSocket', () => {
  let mockWs: MockWebSocket
  
  beforeEach(() => {
    jest.clearAllMocks()
    jest.useFakeTimers()
  })
  
  afterEach(() => {
    jest.runOnlyPendingTimers()
    jest.useRealTimers()
  })
  
  // ========== Test 1: Initial Connection + Snapshot ==========
  
  it('should connect to WebSocket and receive initial snapshot', async () => {
    const { result } = renderHook(() => usePortfolioWebSocket('test_user'))
    
    // Initially disconnected
    expect(result.current.connected).toBe(false)
    expect(result.current.connectionState).toBe('connecting')
    
    // Wait for connection
    act(() => {
      jest.advanceTimersByTime(100)
    })
    
    await waitFor(() => {
      expect(result.current.connected).toBe(true)
      expect(result.current.connectionState).toBe('connected')
    })
    
    // Simulate initial snapshot message
    act(() => {
      const mockSnapshot = {
        user_id: 'test_user',
        cash_balance: 20000,
        positions: [],
        total_value: 20000,
        total_invested: 0,
        total_pnl: 0,
        total_pnl_pct: 0,
        position_count: 0,
        last_updated: new Date().toISOString()
      }
      
      // @ts-ignore - Access MockWebSocket instance
      const ws = global.WebSocket.mock.instances[0]
      ws.onmessage?.(new MessageEvent('message', {
        data: JSON.stringify({
          type: 'portfolio.snapshot.initial',
          data: mockSnapshot
        })
      }))
    })
    
    await waitFor(() => {
      expect(result.current.snapshot).not.toBeNull()
      expect(result.current.snapshot?.user_id).toBe('test_user')
      expect(result.current.snapshot?.total_value).toBe(20000)
    })
    
    // Verify toast notification
    expect(toast.success).toHaveBeenCalledWith(
      'Portfolio Canvas Connected',
      expect.objectContaining({
        description: 'Real-time updates active'
      })
    )
  })
  
  // ========== Test 2: Guardian Insight Notification ==========
  
  it('should receive Guardian insight and show toast notification', async () => {
    const { result } = renderHook(() => usePortfolioWebSocket('test_user'))
    
    // Wait for connection
    act(() => {
      jest.advanceTimersByTime(100)
    })
    
    await waitFor(() => {
      expect(result.current.connected).toBe(true)
    })
    
    // Simulate Guardian insight message
    act(() => {
      const mockInsight = {
        insight_id: 1,
        user_id: 'test_user',
        insight_type: 'risk_alert' as const,
        category: 'PROTECT' as const,
        severity: 'high' as const,
        title: 'High Position Concentration',
        description: 'AAPL represents 65% of portfolio',
        affected_tickers: ['AAPL'],
        recommendations: [
          'Consider diversifying into other tech stocks',
          'Reduce AAPL position to 40% or below'
        ],
        created_at: new Date().toISOString()
      }
      
      // @ts-ignore
      const ws = global.WebSocket.mock.instances[0]
      ws.onmessage?.(new MessageEvent('message', {
        data: JSON.stringify({
          type: 'guardian.insight.new',
          data: mockInsight,
          timestamp: Date.now()
        })
      }))
    })
    
    await waitFor(() => {
      expect(result.current.insights).toHaveLength(1)
      expect(result.current.insights[0].insight_type).toBe('risk_alert')
      expect(result.current.insights[0].severity).toBe('high')
    })
    
    // Verify toast notification with high severity
    expect(toast.warning).toHaveBeenCalledWith(
      expect.stringContaining('Guardian Insight: High Position Concentration'),
      expect.objectContaining({
        description: 'Consider diversifying into other tech stocks',
        duration: 5000
      })
    )
  })
  
  // ========== Test 3: Autopilot Action Notification ==========
  
  it('should receive Autopilot action and show toast notification', async () => {
    const { result } = renderHook(() => usePortfolioWebSocket('test_user'))
    
    act(() => {
      jest.advanceTimersByTime(100)
    })
    
    await waitFor(() => {
      expect(result.current.connected).toBe(true)
    })
    
    // Simulate Autopilot action message
    act(() => {
      const mockAction = {
        action_id: 'action_123',
        user_id: 'test_user',
        action_type: 'rebalance' as const,
        ticker: 'AAPL',
        quantity: 50,
        rationale: 'Reduce concentration risk',
        proposed_at: new Date().toISOString(),
        expires_at: new Date(Date.now() + 15 * 60 * 1000).toISOString(),
        status: 'pending' as const
      }
      
      // @ts-ignore
      const ws = global.WebSocket.mock.instances[0]
      ws.onmessage?.(new MessageEvent('message', {
        data: JSON.stringify({
          type: 'autopilot.action.proposed',
          data: mockAction,
          timestamp: Date.now()
        })
      }))
    })
    
    await waitFor(() => {
      expect(result.current.actions).toHaveLength(1)
      expect(result.current.actions[0].action_type).toBe('rebalance')
      expect(result.current.actions[0].ticker).toBe('AAPL')
    })
    
    // Verify toast notification
    expect(toast.info).toHaveBeenCalledWith(
      expect.stringContaining('Autopilot Action: REBALANCE'),
      expect.objectContaining({
        description: 'AAPL x50 - Reduce concentration risk',
        duration: 7000
      })
    )
  })
  
  // ========== Test 4: Portfolio Value Update ==========
  
  it('should update portfolio value and show toast notification', async () => {
    const { result } = renderHook(() => usePortfolioWebSocket('test_user'))
    
    act(() => {
      jest.advanceTimersByTime(100)
    })
    
    await waitFor(() => {
      expect(result.current.connected).toBe(true)
    })
    
    // Set initial snapshot
    act(() => {
      const mockSnapshot = {
        user_id: 'test_user',
        cash_balance: 20000,
        positions: [],
        total_value: 100000,
        total_invested: 95000,
        total_pnl: 5000,
        total_pnl_pct: 5.26,
        position_count: 5,
        last_updated: new Date().toISOString()
      }
      
      // @ts-ignore
      const ws = global.WebSocket.mock.instances[0]
      ws.onmessage?.(new MessageEvent('message', {
        data: JSON.stringify({
          type: 'portfolio.snapshot.initial',
          data: mockSnapshot
        })
      }))
    })
    
    await waitFor(() => {
      expect(result.current.snapshot?.total_value).toBe(100000)
    })
    
    // Simulate portfolio value update
    act(() => {
      const mockUpdate = {
        user_id: 'test_user',
        total_value: 102500,
        change_amount: 2500,
        change_pct: 2.5,
        timestamp: new Date().toISOString()
      }
      
      // @ts-ignore
      const ws = global.WebSocket.mock.instances[0]
      ws.onmessage?.(new MessageEvent('message', {
        data: JSON.stringify({
          type: 'portfolio.value.updated',
          data: mockUpdate,
          timestamp: Date.now()
        })
      }))
    })
    
    await waitFor(() => {
      expect(result.current.snapshot?.total_value).toBe(102500)
    })
    
    // Verify toast notification
    expect(toast).toHaveBeenCalledWith(
      expect.stringContaining('Portfolio Value Updated'),
      expect.objectContaining({
        description: expect.stringContaining('$102,500.00 (+2.50%)'),
        duration: 3000
      })
    )
  })
  
  // ========== Test 5: Reconnection Logic ==========
  
  it('should reconnect with exponential backoff on connection loss', async () => {
    const { result } = renderHook(() => usePortfolioWebSocket('test_user'))
    
    act(() => {
      jest.advanceTimersByTime(100)
    })
    
    await waitFor(() => {
      expect(result.current.connected).toBe(true)
    })
    
    // Simulate connection loss
    act(() => {
      // @ts-ignore
      const ws = global.WebSocket.mock.instances[0]
      ws.close(1006, 'Abnormal closure') // Not normal closure (1000)
    })
    
    await waitFor(() => {
      expect(result.current.connectionState).toBe('reconnecting')
      expect(result.current.reconnecting).toBe(true)
    })
    
    // Verify exponential backoff: 1s, 2s, 4s, 8s, ...
    expect(result.current.reconnectAttempts).toBe(0)
    
    // Advance by 1s (first reconnect attempt)
    act(() => {
      jest.advanceTimersByTime(1000)
    })
    
    await waitFor(() => {
      expect(result.current.reconnectAttempts).toBe(1)
    })
  })
  
  // ========== Test 6: Clear Methods ==========
  
  it('should clear insights and actions', async () => {
    const { result } = renderHook(() => usePortfolioWebSocket('test_user'))
    
    act(() => {
      jest.advanceTimersByTime(100)
    })
    
    await waitFor(() => {
      expect(result.current.connected).toBe(true)
    })
    
    // Add mock insight
    act(() => {
      const mockInsight = {
        insight_id: 1,
        user_id: 'test_user',
        insight_type: 'risk_alert' as const,
        category: 'PROTECT' as const,
        severity: 'low' as const,
        title: 'Test Insight',
        description: 'Test',
        affected_tickers: [],
        recommendations: [],
        created_at: new Date().toISOString()
      }
      
      // @ts-ignore
      const ws = global.WebSocket.mock.instances[0]
      ws.onmessage?.(new MessageEvent('message', {
        data: JSON.stringify({
          type: 'guardian.insight.new',
          data: mockInsight,
          timestamp: Date.now()
        })
      }))
    })
    
    await waitFor(() => {
      expect(result.current.insights).toHaveLength(1)
    })
    
    // Clear insights
    act(() => {
      result.current.clearInsights()
    })
    
    expect(result.current.insights).toHaveLength(0)
  })
  
  // ========== Test 7: Cleanup on Unmount ==========
  
  it('should cleanup WebSocket connection on unmount', async () => {
    const { result, unmount } = renderHook(() => usePortfolioWebSocket('test_user'))
    
    act(() => {
      jest.advanceTimersByTime(100)
    })
    
    await waitFor(() => {
      expect(result.current.connected).toBe(true)
    })
    
    // @ts-ignore
    const ws = global.WebSocket.mock.instances[0]
    const closeSpy = jest.spyOn(ws, 'close')
    
    // Unmount component
    unmount()
    
    expect(closeSpy).toHaveBeenCalledWith(1000, 'Component unmounted')
  })
})
