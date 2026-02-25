/**
 * RISK COMPARISON NODE UI - Multi-Ticker Risk Analysis
 * 
 * Displays comparative risk analysis for 2+ tickers
 * NO per-ticker donut charts - table/bar format only
 * 
 * Structure:
 * 1. Risk summary comparison (table or bars)
 * 2. Stacked bar visualization (risk drivers per ticker)
 * 3. ONE unified comparative narrative (VEE-ready)
 * 
 * Props:
 * - tickers: array of ticker data with risk metrics
 * - veeNarrative?: optional unified risk explanation
 * - className?: string
 * 
 * Created: Dec 19, 2025 (PHASE 3)
 */

'use client'

import { AlertTriangle, Shield, TrendingDown, Activity } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { DarkTooltip } from '@/components/explainability/tooltips/TooltipLibrary'

export default function RiskComparisonNodeUI({ 
  tickers = [],
  veeNarrative,
  className = '' 
}) {
  if (!tickers || tickers.length < 2) {
    return null
  }

  // Extract risk metrics (volatility_z from numerical_panel)
  const getRiskScore = (ticker) => {
    // Higher volatility_z = higher risk (we invert in display)
    // Risk score: 0-100 scale (100 = highest risk)
    const vola_z = ticker.vola_z || ticker.volatility_z || 0
    
    // Convert z-score to risk score (higher vola = higher risk)
    // z-score range: typically -3 to +3
    // Risk score: 0 (low risk, negative vola_z) to 100 (high risk, positive vola_z)
    const riskScore = Math.min(100, Math.max(0, 50 + (vola_z * 15)))
    
    return {
      overall: riskScore,
      volatility: Math.abs(vola_z),
      dominant_driver: vola_z > 1 ? 'High Volatility' : vola_z < -1 ? 'Low Volatility' : 'Moderate'
    }
  }

  const tickersWithRisk = tickers.map(t => ({
    ticker: t.ticker,
    ...getRiskScore(t),
    raw_vola_z: t.vola_z || t.volatility_z || 0
  }))

  // Sort by risk (highest first)
  const sortedByRisk = [...tickersWithRisk].sort((a, b) => b.overall - a.overall)
  
  // Get risk level label (semitransparent palette)
  const getRiskLevel = (score) => {
    if (score > 70) return { 
      label: 'High Risk', 
      color: 'bg-[rgba(239,68,68,0.12)]', 
      barColor: 'bg-[rgba(239,68,68,0.85)]',
      textColor: 'text-[rgba(220,38,38,1)]',
      borderColor: 'border-[rgba(239,68,68,0.25)]'
    }
    if (score > 40) return { 
      label: 'Moderate Risk', 
      color: 'bg-[rgba(245,158,11,0.12)]', 
      barColor: 'bg-[rgba(245,158,11,0.85)]',
      textColor: 'text-[rgba(217,119,6,1)]',
      borderColor: 'border-[rgba(245,158,11,0.25)]'
    }
    return { 
      label: 'Low Risk', 
      color: 'bg-[rgba(34,197,94,0.12)]', 
      barColor: 'bg-[rgba(34,197,94,0.85)]',
      textColor: 'text-[rgba(22,163,74,1)]',
      borderColor: 'border-[rgba(34,197,94,0.25)]'
    }
  }

  // Calculate max risk for scaling bars
  const maxRisk = Math.max(...tickersWithRisk.map(t => t.overall))

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <Shield className="w-5 h-5 text-purple-600" />
        <h3 className="text-lg font-semibold text-gray-900">Risk Comparison</h3>
      </div>

      {/* 1. Risk Summary Table */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Ticker</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">
                <div className="flex items-center gap-1">
                  Risk Score
                  <DarkTooltip content="Risk score (0-100) derived from volatility z-score. Higher volatility = higher risk. Formula: 50 + (vola_z × 15). Scores >70 = High Risk, 40-70 = Moderate, <40 = Low Risk." />
                </div>
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">
                <div className="flex items-center gap-1">
                  Risk Level
                  <DarkTooltip content="Risk classification based on score: High Risk (>70) suggests significant volatility, Moderate Risk (40-70) indicates average market fluctuations, Low Risk (<40) shows relative stability." />
                </div>
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">
                <div className="flex items-center gap-1">
                  Dominant Driver
                  <DarkTooltip content="Primary factor contributing to risk profile. Derived from volatility z-score: >1 = High Volatility, <-1 = Low Volatility, between = Moderate." />
                </div>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {sortedByRisk.map((t, index) => {
              const riskLevel = getRiskLevel(t.overall)
              return (
                <tr key={t.ticker} className={index === 0 ? 'bg-[rgba(239,68,68,0.05)]' : index === sortedByRisk.length - 1 ? 'bg-[rgba(34,197,94,0.05)]' : 'bg-white'}>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-gray-900">{t.ticker}</span>
                      {index === 0 && <AlertTriangle className="w-4 h-4 text-red-600" />}
                      {index === sortedByRisk.length - 1 && <Shield className="w-4 h-4 text-green-600" />}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-2xl font-bold text-gray-900">{t.overall.toFixed(0)}</span>
                    <span className="text-sm text-gray-500 ml-1">/100</span>
                  </td>
                  <td className="px-4 py-3">
                    <Badge className={`${riskLevel.color} ${riskLevel.textColor} ${riskLevel.borderColor} border text-xs font-medium`}>
                      {riskLevel.label}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-700">
                    {t.dominant_driver}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* 2. Stacked Bar Visualization */}
      <div className="bg-gradient-to-br from-purple-50 to-indigo-50 border border-purple-200 rounded-lg p-4">
        <div className="flex items-center gap-2 mb-4">
          <Activity className="w-4 h-4 text-purple-600" />
          <h4 className="text-sm font-semibold text-gray-900">Risk Distribution</h4>
        </div>
        
        <div className="space-y-3">
          {sortedByRisk.map(t => {
            const riskLevel = getRiskLevel(t.overall)
            const barWidth = maxRisk > 0 ? (t.overall / maxRisk) * 100 : 0
            
            return (
              <div key={t.ticker} className="space-y-1">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-semibold text-gray-900">{t.ticker}</span>
                  <span className="text-gray-600">{t.overall.toFixed(0)}</span>
                </div>
                <div className="w-full bg-[rgba(115,115,115,0.10)] rounded-full h-6 overflow-hidden">
                  <div 
                    className={`h-full ${riskLevel.barColor} transition-all duration-500 flex items-center justify-end pr-2`}
                    style={{ width: `${barWidth}%` }}
                  >
                    <span className="text-xs font-semibold text-white drop-shadow-sm">
                      {barWidth > 20 ? riskLevel.label : ''}
                    </span>
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {/* Legend */}
        <div className="mt-4 flex items-center gap-4 text-xs">
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-[rgba(239,68,68,0.85)] rounded"></div>
            <span className="text-gray-600">High Risk (&gt;70)</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-[rgba(245,158,11,0.85)] rounded"></div>
            <span className="text-gray-600">Moderate (40-70)</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-[rgba(34,197,94,0.85)] rounded"></div>
            <span className="text-gray-600">Low Risk (&lt;40)</span>
          </div>
        </div>
      </div>

      {/* 3. Unified Comparative Narrative (VEE-ready) */}
      {veeNarrative && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <TrendingDown className="w-4 h-4 text-blue-600" />
            <h4 className="text-sm font-semibold text-blue-900">Risk Analysis</h4>
          </div>
          <p className="text-sm text-gray-700 leading-relaxed">
            {veeNarrative}
          </p>
        </div>
      )}

      {/* Default narrative if VEE not provided */}
      {!veeNarrative && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <p className="text-sm text-gray-700 leading-relaxed">
            <strong>{sortedByRisk[0].ticker}</strong> shows the highest risk profile with a score of{' '}
            <strong>{sortedByRisk[0].overall.toFixed(0)}/100</strong>, primarily driven by{' '}
            {sortedByRisk[0].dominant_driver.toLowerCase()}. In comparison,{' '}
            <strong>{sortedByRisk[sortedByRisk.length - 1].ticker}</strong> presents lower risk at{' '}
            <strong>{sortedByRisk[sortedByRisk.length - 1].overall.toFixed(0)}/100</strong>.
            {sortedByRisk.length === 2 && (
              <> The risk differential of <strong>{(sortedByRisk[0].overall - sortedByRisk[1].overall).toFixed(0)} points</strong> suggests different volatility profiles that may impact portfolio allocation decisions.</>
            )}
          </p>
        </div>
      )}
    </div>
  )
}
