/**
 * @deprecated This component is deprecated.
 * Use the replacement indicated below.
 * Will be removed in v2.0
 *
 * FundamentalsDisplay → analytics/panels/FundamentalsPanel
 * MetricDisplay → cards/MetricCard
 * RiskDisplay → analytics/panels/RiskPanel
 */

'use client'

import { Shield, AlertTriangle } from 'lucide-react'

export function RiskDisplay({ riskData }) {
  if (!riskData || !riskData.vare_risk_score) return null
  
  const { vare_risk_score, vare_risk_category, market_risk, volatility_risk, liquidity_risk, correlation_risk } = riskData
  
  const categoryColors = {
    low: 'bg-green-100 text-green-700 border-green-200',
    medium: 'bg-yellow-100 text-yellow-700 border-yellow-200',
    high: 'bg-orange-100 text-orange-700 border-orange-200',
    critical: 'bg-red-100 text-red-700 border-red-200'
  }
  
  const dimensions = [
    { key: 'market_risk', label: 'Market' },
    { key: 'volatility_risk', label: 'Volatility' },
    { key: 'liquidity_risk', label: 'Liquidity' },
    { key: 'correlation_risk', label: 'Correlation' }
  ].filter(d => riskData[d.key] !== undefined)
  
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h4 className="text-xs font-semibold text-gray-600 uppercase flex items-center gap-1.5">
          <Shield size={14} />
          Risk Assessment
        </h4>
        <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${categoryColors[vare_risk_category] || categoryColors.medium}`}>
          {vare_risk_category?.toUpperCase()} ({vare_risk_score?.toFixed(0)})
        </span>
      </div>
      
      {dimensions.length > 0 && (
        <div className="grid grid-cols-4 gap-1">
          {dimensions.map(({ key, label }) => (
            <div key={key} className="text-center p-1.5 bg-gray-50 rounded">
              <div className="text-[10px] text-gray-500">{label}</div>
              <div className="text-xs font-medium">{riskData[key]?.toFixed(0)}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}