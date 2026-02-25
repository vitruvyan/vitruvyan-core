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

import { TrendingUp, DollarSign, PieChart, CreditCard, Banknote, Gift } from 'lucide-react'

export function FundamentalsDisplay({ fundamentals }) {
  if (!fundamentals) return null
  
  const metrics = [
    { key: 'revenue_growth_yoy_z', label: 'Revenue Growth', icon: TrendingUp },
    { key: 'eps_growth_yoy_z', label: 'EPS Growth', icon: DollarSign },
    { key: 'net_margin_z', label: 'Net Margin', icon: PieChart },
    { key: 'debt_to_equity_z', label: 'Debt/Equity', icon: CreditCard },
    { key: 'free_cash_flow_z', label: 'Free Cash Flow', icon: Banknote },
    { key: 'dividend_yield_z', label: 'Dividend Yield', icon: Gift }
  ].filter(m => fundamentals[m.key] !== null && fundamentals[m.key] !== undefined)
  
  if (metrics.length === 0) return null
  
  return (
    <div className="space-y-2">
      <h4 className="text-xs font-semibold text-gray-600 uppercase">Fundamentals</h4>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
        {metrics.map(({ key, label, icon: Icon }) => (
          <div key={key} className={`p-2 rounded-lg border ${getZScoreColor(fundamentals[key])}`}>
            <div className="flex items-center gap-1.5">
              <Icon size={12} className="text-gray-500" />
              <span className="text-xs text-gray-500">{label}</span>
            </div>
            <div className="font-mono font-medium mt-1">{fundamentals[key]?.toFixed(2)}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

function getZScoreColor(z) {
  if (z === null || z === undefined) return 'bg-gray-50 border-gray-200'
  if (z > 1.0) return 'bg-green-50 border-green-200 text-green-900'
  if (z > 0.5) return 'bg-emerald-50 border-emerald-200 text-emerald-900'
  if (z > -0.5) return 'bg-blue-50 border-blue-200 text-blue-900'
  if (z > -1.0) return 'bg-orange-50 border-orange-200 text-orange-900'
  return 'bg-red-50 border-red-200 text-red-900'
}