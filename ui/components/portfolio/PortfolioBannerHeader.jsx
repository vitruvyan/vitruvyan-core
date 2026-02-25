/**
 * PortfolioBannerHeader Component
 * 
 * Row 1 of Portfolio Banner: Title, Total Value, Alerts, Controls
 * 
 * Props:
 * - totalValue: number (USD)
 * - pnlPercent: number (percentage)
 * - alertsCount: number
 * - onClose: function
 * - onViewFull: function (navigate to /portfolio page)
 * 
 * Created: January 20, 2026
 */

'use client'

import { X, AlertTriangle, DollarSign, ExternalLink } from 'lucide-react'
import Link from 'next/link'

export default function PortfolioBannerHeader({
  totalValue = 0,
  pnlPercent = 0,
  alertsCount = 0,
  onClose
}) {
  const isProfitable = pnlPercent >= 0
  const pnlColor = isProfitable ? 'text-green-600' : 'text-red-600'
  const pnlBgColor = isProfitable ? 'bg-green-50' : 'bg-red-50'

  return (
    <div className="flex items-center justify-between px-6 py-3 border-b border-gray-200">
      {/* Left: Title + Total Value */}
      <div className="flex items-center gap-6">
        <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <DollarSign size={20} className="text-emerald-600" />
          Portfolio Overview
        </h2>
        
        <div className="flex items-center gap-3">
          <div className="text-2xl font-bold text-gray-900">
            ${totalValue.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
          </div>
          
          <div className={`px-3 py-1 rounded-full ${pnlBgColor} ${pnlColor} text-sm font-medium`}>
            {isProfitable ? '+' : ''}{pnlPercent.toFixed(2)}%
          </div>
        </div>

        {/* Alerts Badge */}
        {alertsCount > 0 && (
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-orange-50 border border-orange-200">
            <AlertTriangle size={14} className="text-orange-600" />
            <span className="text-xs font-medium text-orange-700">
              {alertsCount} alert{alertsCount !== 1 ? 's' : ''}
            </span>
          </div>
        )}
      </div>

      {/* Right: Controls */}
      <div className="flex items-center gap-3">
        {/* Full View Link */}
        <Link
          href="/portfolio"
          className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-emerald-50 hover:bg-emerald-100 text-emerald-700 text-sm font-medium transition-colors"
        >
          <span>Full View</span>
          <ExternalLink size={14} />
        </Link>

        {/* Close Button */}
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-500 hover:text-gray-700 transition-colors"
          aria-label="Close portfolio"
        >
          <X size={20} />
        </button>
      </div>
    </div>
  )
}
