/**
 * GuardianAutopilotAdapter - Real-Time Insights & Automation Control
 * 
 * Task 26.3: Guardian Timeline UI (Jan 26, 2026)
 * 
 * Integrates:
 * - usePortfolioWebSocket hook (Task 26.2)
 * - GuardianTimeline component with real-time insights
 * - Autopilot control panel with settings
 * 
 * Features:
 * - Real-time WebSocket connection status
 * - Guardian insights timeline (PROTECT/IMPROVE/UNDERSTAND)
 * - Autopilot toggle and risk tolerance settings
 * - Recent actions history
 */

'use client'

import { useState } from 'react'
import { Shield, Zap, PlayCircle, PauseCircle, Clock, AlertCircle, Wifi, WifiOff } from 'lucide-react'
import { usePortfolioWebSocket } from '@/hooks/usePortfolioWebSocket'
import { GuardianTimeline } from '@/components/portfolio-canvas'

export function GuardianAutopilotAdapter({ userId }) {
  const [activeTab, setActiveTab] = useState("guardian")
  const [autopilotEnabled, setAutopilotEnabled] = useState(false)
  const [riskTolerance, setRiskTolerance] = useState(5)
  
  // ✅ WebSocket Integration (Task 26.2)
  const { 
    insights, 
    actions, 
    connected, 
    connectionState,
    reconnecting,
    reconnectAttempts 
  } = usePortfolioWebSocket(userId)
  
  return (
    <section>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-900">Guardian & Autopilot</h2>
        
        {/* WebSocket Connection Status */}
        <div className="flex items-center gap-2">
          {reconnecting ? (
            <div className="flex items-center gap-2 text-orange-600 text-sm">
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-orange-600 border-t-transparent" />
              <span>Reconnecting... (Attempt {reconnectAttempts}/10)</span>
            </div>
          ) : connected ? (
            <div className="flex items-center gap-2 text-green-600 text-sm">
              <Wifi className="w-4 h-4" />
              <span>Real-time updates active</span>
            </div>
          ) : (
            <div className="flex items-center gap-2 text-red-600 text-sm">
              <WifiOff className="w-4 h-4" />
              <span>Disconnected</span>
            </div>
          )}
        </div>
      </div>
      
      {/* Tab Navigation */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="border-b border-gray-200">
          <div className="flex">
            <button
              onClick={() => setActiveTab("guardian")}
              className={`flex-1 px-6 py-4 text-sm font-medium transition-colors ${
                activeTab === "guardian"
                  ? 'bg-blue-50 text-blue-700 border-b-2 border-blue-700'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <Shield className="w-5 h-5 inline-block mr-2" />
              Guardian Insights
              {insights.length > 0 && (
                <span className="ml-2 px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full text-xs font-semibold">
                  {insights.length}
                </span>
              )}
            </button>
            <button
              onClick={() => setActiveTab("autopilot")}
              className={`flex-1 px-6 py-4 text-sm font-medium transition-colors ${
                activeTab === "autopilot"
                  ? 'bg-blue-50 text-blue-700 border-b-2 border-blue-700'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <Zap className="w-5 h-5 inline-block mr-2" />
              Autopilot Control
              {actions.length > 0 && (
                <span className="ml-2 px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full text-xs font-semibold">
                  {actions.length}
                </span>
              )}
            </button>
          </div>
        </div>

        <div className="p-6">
          {activeTab === "guardian" ? (
            /* Guardian Insights Timeline (Task 26.3) */
            connected ? (
              <GuardianTimeline insights={insights} />
            ) : (
              /* Disconnected State */
              <div className="text-center py-12">
                <WifiOff className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  WebSocket Disconnected
                </h3>
                <p className="text-sm text-gray-600 mb-4">
                  Real-time Guardian insights require an active connection.
                </p>
                <button
                  onClick={() => window.location.reload()}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Reconnect
                </button>
              </div>
            )
          ) : (
            /* Autopilot Control Panel */
            <div className="space-y-6">
              {/* Autopilot Toggle */}
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-200">
                <div>
                  <h4 className="font-semibold text-gray-900">Autopilot Status</h4>
                  <p className="text-sm text-gray-600 mt-1">
                    {autopilotEnabled ? 'Leonardo is actively managing your portfolio' : 'Manual portfolio management'}
                  </p>
                </div>
                <button
                  onClick={() => setAutopilotEnabled(!autopilotEnabled)}
                  className={`flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-colors ${
                    autopilotEnabled
                      ? 'bg-green-600 hover:bg-green-700 text-white'
                      : 'bg-gray-300 hover:bg-gray-400 text-gray-700'
                  }`}
                >
                  {autopilotEnabled ? (
                    <>
                      <PlayCircle className="w-5 h-5" />
                      <span>Active</span>
                    </>
                  ) : (
                    <>
                      <PauseCircle className="w-5 h-5" />
                      <span>Paused</span>
                    </>
                  )}
                </button>
              </div>

              {/* Risk Tolerance Slider */}
              <div className="p-4 bg-white border border-gray-200 rounded-lg">
                <label className="block text-sm font-medium text-gray-900 mb-3">
                  Risk Tolerance: {riskTolerance}/10
                </label>
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={riskTolerance}
                  onChange={(e) => setRiskTolerance(Number(e.target.value))}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                />
                <div className="flex justify-between text-xs text-gray-600 mt-2">
                  <span>Conservative</span>
                  <span>Moderate</span>
                  <span>Aggressive</span>
                </div>
              </div>

              {/* Recent Actions (Real-time from WebSocket) */}
              <div className="border-t border-gray-200 pt-4">
                <h4 className="font-semibold text-gray-900 mb-3">
                  Recent Autopilot Actions
                  {!connected && (
                    <span className="ml-2 text-xs text-orange-600">(Offline - showing cached)</span>
                  )}
                </h4>
                
                {actions.length > 0 ? (
                  <div className="space-y-2">
                    {actions.slice(0, 5).map((action) => (
                      <div key={action.action_id} className="flex items-center justify-between text-sm p-3 bg-gray-50 rounded-lg border border-gray-200">
                        <div className="flex items-center gap-3">
                          <Clock className="w-4 h-4 text-gray-500" />
                          <div>
                            <span className="font-medium text-gray-900">
                              {action.action_type.toUpperCase()}
                            </span>
                            <span className="text-gray-700 ml-2">
                              {action.ticker} x{action.quantity}
                            </span>
                            <p className="text-xs text-gray-600 mt-1">{action.rationale}</p>
                          </div>
                        </div>
                        <span className="text-xs text-gray-500">
                          {new Date(action.proposed_at).toLocaleTimeString()}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500 text-sm">
                    <AlertCircle className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                    <p>No autopilot actions yet</p>
                    <p className="text-xs mt-1">Actions will appear here as Leonardo optimizes your portfolio</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
