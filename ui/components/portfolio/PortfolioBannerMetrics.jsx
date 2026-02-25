/**
 * PortfolioBannerMetrics Component
 * 
 * Row 3 of Portfolio Banner: Key metrics cards (P&L, Risk, Diversification)
 * 
 * Props:
 * - pnlAbsolute: number (USD)
 * - pnlPercent: number (percentage)
 * - riskScore: number (0-100)
 * - diversificationScore: number
 * - sectorsCount: number
 * 
 * Created: January 20, 2026
 */

'use client'

import { TrendingUp, TrendingDown, Shield, Activity } from 'lucide-react'

export default function PortfolioBannerMetrics({
  pnlAbsolute = 0,
  pnlPercent = 0,
  riskScore = 0,
  diversificationScore = 0,
  sectorsCount = 0
}) {
  const isProfitable = pnlPercent >= 0

  // Risk level interpretation
  const getRiskLevel = (score) => {
    if (score < 30) return { label: 'LOW', color: 'text-green-600', bg: 'bg-green-50' }
    if (score < 60) return { label: 'MODERATE', color: 'text-yellow-600', bg: 'bg-yellow-50' }
    return { label: 'HIGH', color: 'text-red-600', bg: 'bg-red-50' }
  }

  const riskLevel = getRiskLevel(riskScore)

  return (
    <div className="px-6 py-3 flex items-center gap-8">
      {/* P&L Metric */}
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${isProfitable ? 'bg-green-50' : 'bg-red-50'}`}>
          {isProfitable ? (
            <TrendingUp size={18} className="text-green-600" />
          ) : (
            <TrendingDown size={18} className="text-red-600" />
          )}
        </div>
        <div>
          <div className="text-xs text-gray-500 font-medium">Total P&L</div>
          <div className={`text-lg font-bold ${isProfitable ? 'text-green-600' : 'text-red-600'}`}>
            {isProfitable ? '+' : ''}${pnlAbsolute.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
          </div>
        </div>
      </div>

      {/* Separator */}
      <div className="h-8 w-px bg-gray-200" />

      {/* Risk Score Metric */}
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${riskLevel.bg}`}>
          <Shield size={18} className={riskLevel.color} />
        </div>
        <div>
          <div className="text-xs text-gray-500 font-medium">Risk Score</div>
          <div className="flex items-center gap-2">
            <span className="text-lg font-bold text-gray-900">{riskScore.toFixed(0)}</span>
            <span className={`text-xs font-semibold px-2 py-0.5 rounded ${riskLevel.bg} ${riskLevel.color}`}>
              {riskLevel.label}
            </span>
          </div>
        </div>
      </div>

      {/* Separator */}
      <div className="h-8 w-px bg-gray-200" />

      {/* Diversification Metric */}
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-blue-50">
          <Activity size={18} className="text-blue-600" />
        </div>
        <div>
          <div className="text-xs text-gray-500 font-medium">Diversification</div>
          <div className="flex items-center gap-1.5">
            <span className="text-lg font-bold text-gray-900">{diversificationScore.toFixed(1)}</span>
            <span className="text-xs text-gray-500">
              ({sectorsCount} sector{sectorsCount !== 1 ? 's' : ''})
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
