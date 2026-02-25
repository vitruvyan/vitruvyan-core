"use client"

import { useEffect, useState } from "react"
import { RefreshCw, Settings, TrendingDown, TrendingUp, Minus } from "lucide-react"
import HealthGauge from "@/components/admin/HealthGauge"
import MetricBar from "@/components/admin/MetricBar"
import Link from "next/link"

/**
 * Plasticity Health Dashboard
 * 
 * Main admin dashboard for Vitruvyan's bounded learning system.
 * Displays:
 * - Overall health score (3 gauges: health, stability, success)
 * - Metrics overview (4 bars: stability index, success rate, coverage, diversity)
 * - Recent anomalies (top 3)
 * - Consumer health (top 3)
 * 
 * Phase 2: Admin UI Shell (Jan 27, 2026)
 */
export default function PlasticityDashboard() {
  const [healthData, setHealthData] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [error, setError] = useState(null)
  const [lastUpdated, setLastUpdated] = useState(null)

  // Fetch health data
  const fetchHealth = async (silent = false) => {
    if (!silent) setIsRefreshing(true)
    
    try {
      const response = await fetch("/api/admin/plasticity/health")
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`)
      }
      
      const data = await response.json()
      setHealthData(data)
      setLastUpdated(new Date())
      setError(null)
    } catch (err) {
      console.error("Failed to fetch health data:", err)
      setError(err.message)
      
      // Fallback to mock data for Phase 2 testing
      setHealthData({
        health_score: 0.76,
        overall_health: "degraded",
        consumers_analyzed: 3,
        parameters_tracked: 6,
        adjustments_24h: 12,
        adjustments_7d: 48,
        anomaly_count: 2,
        metrics: {
          stability_index: 1.0,
          success_rate: 0.35,
          coverage: 1.0,
          consumer_diversity: 0.75
        },
        recent_anomalies: [
          {
            id: "anom_001",
            type: "OSCILLATION",
            consumer: "NarrativeEngine",
            parameter: "confidence_threshold",
            severity: 0.6,
            timestamp: "2h ago"
          },
          {
            id: "anom_002",
            type: "DRIFT",
            consumer: "RiskGuardian",
            parameter: "threshold",
            severity: 0.4,
            timestamp: "1d ago"
          }
        ],
        consumer_health: [
          { name: "NarrativeEngine", health: 0.78, parameter_count: 3, trend: "down" },
          { name: "RiskGuardian", health: 0.95, parameter_count: 2, trend: "stable" },
          { name: "OrthodoxyWarden", health: 0.91, parameter_count: 1, trend: "up" }
        ]
      })
      setLastUpdated(new Date())
    } finally {
      setIsLoading(false)
      setIsRefreshing(false)
    }
  }

  // Initial load
  useEffect(() => {
    fetchHealth()
  }, [])

  // Auto-refresh every 30s
  useEffect(() => {
    const interval = setInterval(() => {
      fetchHealth(true)
    }, 30000)
    
    return () => clearInterval(interval)
  }, [])

  if (isLoading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="text-center">
          <div className="mb-4 inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-cyan-500 border-r-transparent"></div>
          <p className="font-mono text-sm text-slate-400">Loading health data...</p>
        </div>
      </div>
    )
  }

  const getTrendIcon = (trend) => {
    if (trend === "up") return <TrendingUp className="h-4 w-4 text-emerald-400" />
    if (trend === "down") return <TrendingDown className="h-4 w-4 text-red-400" />
    return <Minus className="h-4 w-4 text-slate-400" />
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-mono text-2xl font-bold text-slate-100">
            Plasticity Health Dashboard
          </h1>
          <p className="mt-1 font-mono text-sm text-slate-500">
            Bounded learning system monitoring
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          {lastUpdated && (
            <span className="font-mono text-xs text-slate-500">
              Updated {lastUpdated.toLocaleTimeString()}
            </span>
          )}
          
          <button
            onClick={() => fetchHealth()}
            disabled={isRefreshing}
            className="flex items-center gap-2 rounded-md bg-slate-800 px-4 py-2 font-mono text-sm text-slate-200 hover:bg-slate-700 disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`} />
            Refresh
          </button>
          
          <button className="flex items-center gap-2 rounded-md bg-slate-800 px-4 py-2 font-mono text-sm text-slate-200 hover:bg-slate-700">
            <Settings className="h-4 w-4" />
            Settings
          </button>
        </div>
      </div>

      {/* Health Gauges */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <div className="rounded-lg border border-slate-800 bg-slate-900 p-6">
          <HealthGauge 
            score={healthData.health_score} 
            label="HEALTH" 
          />
        </div>
        
        <div className="rounded-lg border border-slate-800 bg-slate-900 p-6">
          <HealthGauge 
            score={healthData.metrics.stability_index} 
            label="STABILITY" 
          />
        </div>
        
        <div className="rounded-lg border border-slate-800 bg-slate-900 p-6">
          <HealthGauge 
            score={healthData.metrics.success_rate} 
            label="SUCCESS RATE" 
          />
        </div>
      </div>

      {/* Metrics Overview */}
      <div className="rounded-lg border border-slate-800 bg-slate-900 p-6">
        <h2 className="mb-4 font-mono text-lg font-semibold text-slate-100">
          Metrics Overview
        </h2>
        
        <div className="space-y-4">
          <MetricBar 
            label="Stability Index" 
            value={healthData.metrics.stability_index} 
            colorScheme="cyan"
          />
          <MetricBar 
            label="Success Rate" 
            value={healthData.metrics.success_rate} 
            colorScheme={healthData.metrics.success_rate >= 0.5 ? "green" : "red"}
          />
          <MetricBar 
            label="Coverage" 
            value={healthData.metrics.coverage} 
            colorScheme="cyan"
          />
          <MetricBar 
            label="Consumer Diversity" 
            value={healthData.metrics.consumer_diversity} 
            colorScheme="cyan"
          />
        </div>
      </div>

      {/* Recent Anomalies */}
      <div className="rounded-lg border border-slate-800 bg-slate-900 p-6">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="font-mono text-lg font-semibold text-slate-100">
            Recent Anomalies
          </h2>
          <Link 
            href="/admin/plasticity/anomalies"
            className="font-mono text-sm text-cyan-400 hover:text-cyan-300"
          >
            View All →
          </Link>
        </div>
        
        <div className="space-y-3">
          {healthData.recent_anomalies.map((anomaly) => (
            <div
              key={anomaly.id}
              className="flex items-center justify-between rounded-md border border-slate-800 bg-slate-950 p-4"
            >
              <div className="flex items-center gap-3">
                <span className="font-mono text-sm font-semibold text-yellow-400">
                  {anomaly.type === "OSCILLATION" ? "🔄" : "➡️"}
                </span>
                <div>
                  <p className="font-mono text-sm text-slate-300">
                    {anomaly.consumer}/{anomaly.parameter}
                  </p>
                  <p className="font-mono text-xs text-slate-500">
                    {anomaly.type}
                  </p>
                </div>
              </div>
              
              <div className="flex items-center gap-4">
                <span className="font-mono text-xs text-slate-500">
                  {anomaly.timestamp}
                </span>
                <span className="font-mono text-sm font-semibold text-slate-300">
                  {anomaly.severity.toFixed(1)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Consumer Health */}
      <div className="rounded-lg border border-slate-800 bg-slate-900 p-6">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="font-mono text-lg font-semibold text-slate-100">
            Consumer Health
          </h2>
          <Link 
            href="/admin/plasticity/consumers"
            className="font-mono text-sm text-cyan-400 hover:text-cyan-300"
          >
            View All →
          </Link>
        </div>
        
        <div className="space-y-3">
          {healthData.consumer_health.map((consumer) => (
            <Link
              key={consumer.name}
              href={`/admin/plasticity/consumers/${consumer.name}`}
              className="flex items-center gap-4 rounded-md border border-slate-800 bg-slate-950 p-4 hover:bg-slate-900 hover:border-cyan-600 transition-all cursor-pointer"
            >
              <div className="flex-1">
                <p className="font-mono text-sm font-semibold text-slate-300">
                  {consumer.name}
                </p>
                <p className="font-mono text-xs text-slate-500">
                  {consumer.parameter_count} parameters
                </p>
              </div>
              
              <div className="w-48">
                <MetricBar 
                  label="" 
                  value={consumer.health} 
                  showPercentage={true}
                  colorScheme={consumer.health >= 0.8 ? "green" : consumer.health >= 0.5 ? "yellow" : "red"}
                />
              </div>
              
              <div className="flex items-center gap-2">
                {getTrendIcon(consumer.trend)}
                <span className="font-mono text-xs text-slate-500">
                  {consumer.trend}
                </span>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
