/**
 * FUNDAMENTALS PANEL COMPONENT
 * 
 * Displays 7 fundamental z-scores in visual card format with color coding.
 * 
 * Data Source: stock.factors from Neural Engine API
 * Backend: engine_core.py get_fundamentals_z() (Function E)
 * Created: Dec 7, 2025
 * 
 * Features:
 * - 7 metric cards (6 individual + 1 composite)
 * - Color coding: Green (z>1), Yellow (0.5-1), Red (<-1), Gray (null)
 * - Icons from lucide-react
 * - Tooltips on hover
 * - Responsive grid (3 cols desktop, 2 mobile)
 * - Null handling (e.g., GOOGL missing revenue)
 * 
 * @typedef {Object} StockFactors
 * @property {number|null} fundamentals_z - Composite fundamentals z-score
 * @property {number|null} revenue_growth_yoy_z - Revenue growth YoY z-score
 * @property {number|null} eps_growth_yoy_z - EPS growth YoY z-score
 * @property {number|null} net_margin_z - Net margin z-score
 * @property {number|null} debt_to_equity_z - Debt-to-equity z-score (inverted)
 * @property {number|null} free_cash_flow_z - Free cash flow z-score
 * @property {number|null} dividend_yield_z - Dividend yield z-score
 */

'use client'

import { TrendingUp, DollarSign, Percent, Scale, Droplets, Gift, BarChart3 } from 'lucide-react'
import VeeBadge from '@/components/explainability/badges/VeeBadge'
import { ZScoreCard } from '@/components/cards/CardLibrary'

/**
 * Generate simplified VEE explanations for fundamental metrics
 * Delegates to VEE engine when available, otherwise provides basic interpretation
 * @param {string} metricKey - Metric key (e.g., "revenue_growth_yoy_z")
 * @param {number|null} value - Z-score value
 * @param {Object} explainability - VEE explainability object from API
 * @returns {{simple: string, technical: string}} VEE explanations
 */
const getVeeExplanations = (metricKey, value, explainability) => {
  // Try to extract from explainability object (VEE Engine 2.0) first
  if (explainability?.detailed?.ranking?.stocks?.[0]?.explainability?.fundamentals?.[metricKey]) {
    const veeData = explainability.detailed.ranking.stocks[0].explainability.fundamentals[metricKey]
    return {
      simple: veeData.simple || `${metricKey}: VEE analysis available`,
      technical: veeData.technical || `${metricKey}: Detailed VEE explanation from engine`
    }
  }

  // Fallback: Basic interpretation only
  const metricNames = {
    'revenue_growth_yoy_z': 'Revenue Growth',
    'eps_growth_yoy_z': 'EPS Growth',
    'net_margin_z': 'Net Margin',
    'debt_to_equity_z': 'Debt/Equity',
    'free_cash_flow_z': 'Free Cash Flow',
    'dividend_yield_z': 'Dividend Yield'
  }

  const metricName = metricNames[metricKey] || metricKey
  let simple = `${metricName}: `

  if (value === null || value === undefined) {
    simple += 'No data available'
  } else if (value > 1.0) {
    simple += 'Strong performance'
  } else if (value > 0.5) {
    simple += 'Above average'
  } else if (value > -0.5) {
    simple += 'Average performance'
  } else {
    simple += 'Below average'
  }

  return {
    simple,
    technical: `${metricName} z-score: ${value?.toFixed(2) || 'N/A'}. Analysis provided by VEE engine.`
  }
}

/**
 * Main FundamentalsPanel component with VEE explainability
 * @param {Object} props
 * @param {StockFactors} props.factors - Stock factors from Neural Engine API
 * @param {Object} [props.explainability] - VEE explainability object
 * @param {string} [props.className] - Optional Tailwind classes
 */
export default function FundamentalsPanel({ factors, explainability, className = '' }) {
  // Guard: Don't render if no factors data
  if (!factors) {
    return null
  }

  // Define 6 individual metrics with VEE generation
  const fundamentalMetrics = [
    {
      key: 'revenue_growth_yoy_z',
      label: 'Revenue Growth',
      icon: TrendingUp
    },
    {
      key: 'eps_growth_yoy_z',
      label: 'EPS Growth',
      icon: DollarSign
    },
    {
      key: 'net_margin_z',
      label: 'Net Margin',
      icon: Percent
    },
    {
      key: 'debt_to_equity_z',
      label: 'Debt/Equity',
      icon: Scale
    },
    {
      key: 'free_cash_flow_z',
      label: 'Free Cash Flow',
      icon: Droplets
    },
    {
      key: 'dividend_yield_z',
      label: 'Dividend Yield',
      icon: Gift
    }
  ].map(m => ({
    ...m,
    vee: getVeeExplanations(m.key, factors[m.key], explainability)
  }))

  // Check if at least one fundamental is non-null (otherwise don't render)
  const hasData = fundamentalMetrics.some(m => factors[m.key] !== null && factors[m.key] !== undefined)
  if (!hasData && !factors.fundamentals_z) {
    return null
  }

  return (
    <div className={`space-y-2 ${className}`}>
      {/* Header */}
      <div className="flex items-center gap-2 text-xs font-semibold text-gray-800">
        <BarChart3 className="w-3 h-3" />
        <span>Fundamental Analysis</span>
      </div>

      {/* 6 Individual Metrics Grid - Now using ZScoreCard from CardLibrary */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
        {fundamentalMetrics.map(metric => (
          <ZScoreCard
            key={metric.key}
            label={metric.label}
            value={factors[metric.key]}
            icon={metric.icon}
            veeSimple={metric.vee.simple}
            veeTechnical={metric.vee.technical}
          />
        ))}
      </div>

      {/* Composite Fundamentals Score */}
      {factors.fundamentals_z !== null && factors.fundamentals_z !== undefined && (
        <ZScoreCard
          label="Composite Fundamentals"
          value={factors.fundamentals_z}
          icon={BarChart3}
          veeSimple={`Composite fundamentals score combining growth, profitability, and financial health metrics.`}
          veeTechnical={`Weighted formula: Growth 50% (Revenue + EPS), Profitability 30% (Net Margin), Financial Health 20% (Debt/Equity + FCF + Dividend). Z-score: ${factors.fundamentals_z?.toFixed(2) || 'N/A'}`}
        />
      )}
    </div>
  )
}
