/**
 * PORTFOLIO NODE UI
 * 
 * Displays portfolio analysis from PortfolioAnalysisNode
 * Shows portfolio value, holdings, concentration risk, diversification, and sector breakdown
 * 
 * Backend Node: portfolio_analysis_node.py
 * State Keys: state.portfolio_state
 * 
 * Props:
 * - portfolioState: object with { portfolio_value, holdings, largest_position_pct, concentration_risk, diversification_score, sector_breakdown, top_3_holdings }
 * - className?: string
 */

'use client'

import { Wallet, PieChart, Shield, TrendingUp, AlertTriangle } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion'
import VEEAccordions from '../explainability/vee/VEEAccordions'

export default function PortfolioNodeUI({ 
  portfolioData,
  portfolioState, 
  narrative,
  veeExplanations,
  numericalPanel,
  className = '' 
}) {
  // Backward compatibility: Support both old portfolioState and new portfolioData
  const dataSource = portfolioData || portfolioState || {}
  
  // Guard: Don't render if no portfolio data
  if (!dataSource || (dataSource.count === 0 && dataSource.num_holdings === 0)) {
    return (
      <div className={`bg-yellow-50 border border-yellow-200 p-4 rounded-lg ${className}`}>
        <p className="text-sm text-yellow-800">⚠️ No portfolio data available</p>
      </div>
    )
  }

  const {
    total_value = 0,
    tickers = [],
    holdings = [],
    weights = {},
    num_holdings = 0,
    count = 0,
    average_composite = 0,
    top_performer = null,
    positions = {},
    concentration_risk = 'unknown',
    diversification_score = 0,
    sector_breakdown = {},
    factor_summary = {},
    portfolio_score = 0,
    ne_ranking = null
  } = dataSource
  
  // Use count if available (new backend), otherwise num_holdings (old backend)
  const holdingsCount = count || num_holdings || (holdings && holdings.length) || tickers.length

  // Build holdings array from weights and NE ranking or use backend positions
  const holdingsArray = holdings.length > 0 ? holdings : (tickers || []).map((ticker) => {
    const weight = weights[ticker] || 0
    const value = total_value * weight
    const stock = ne_ranking?.ranking?.stocks?.find(s => s.ticker === ticker)
    const position = positions?.[ticker] || {}
    
    return {
      ticker,
      shares: stock?.shares || 0,
      weight_pct: weight * 100,
      value: value,
      composite_score: position.composite_score || stock?.composite_score || 0
    }
  })

  // Get largest position percentage
  const largest_position_pct = Math.max(...Object.values(weights).map(w => w * 100), 0)

  // Get top 3 holdings
  const top_3_holdings = [...holdingsArray]
    .sort((a, b) => b.weight_pct - a.weight_pct)
    .slice(0, 3)

  // Helper: Get risk badge style
  const getRiskBadgeStyle = (risk) => {
    const styles = {
      critical: 'bg-red-500 text-white',
      high: 'bg-orange-500 text-white',
      medium: 'bg-yellow-100 text-yellow-700',
      low: 'bg-green-100 text-green-700',
      unknown: 'bg-gray-100 text-gray-700'
    }
    return styles[risk] || styles.unknown
  }

  // Helper: Get diversification badge style
  const getDiversificationBadgeStyle = (score) => {
    if (score >= 0.7) return 'bg-green-100 text-green-700'
    if (score >= 0.4) return 'bg-yellow-100 text-yellow-700'
    return 'bg-red-100 text-red-700'
  }

  // Helper: Format currency
  const formatCurrency = (value) => {
    if (typeof value !== 'number') return '$0.00'
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value)
  }

  // Helper: Format percentage
  const formatPercent = (value) => {
    if (typeof value !== 'number') return '0.0%'
    return `${value.toFixed(1)}%`
  }

  // Helper: Get concentration risk label
  const getConcentrationLabel = (risk) => {
    const labels = {
      critical: 'Critical Risk',
      high: 'High Risk',
      medium: 'Moderate',
      low: 'Well Diversified',
      unknown: 'Unknown'
    }
    return labels[risk] || 'Unknown'
  }

  return (
    <>
    <Card className={`border-l-4 border-l-blue-500 ${className}`}>
      <CardHeader className="bg-gradient-to-r from-blue-50 to-cyan-50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Wallet className="w-5 h-5 text-blue-600" />
            <CardTitle className="text-base font-semibold text-gray-900">
              Portfolio Analysis
            </CardTitle>
          </div>
          <Badge variant="outline" className="text-xs">
            {holdingsCount} positions
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="p-4 space-y-4">
        {/* Portfolio Value */}
        <div className="p-4 rounded-lg bg-gradient-to-r from-blue-50 to-cyan-50 border border-blue-100">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Total Portfolio Value</span>
            <span className="text-2xl font-bold text-gray-900">
              {formatCurrency(total_value)}
            </span>
          </div>
          {portfolio_score > 0 && (
            <div className="mt-2 flex items-center gap-2">
              <span className="text-xs text-gray-600">Portfolio Score:</span>
              <Badge variant="outline" className="text-xs">
                {portfolio_score.toFixed(2)}
              </Badge>
            </div>
          )}
        </div>

        <Accordion type="single" collapsible defaultValue="risk" className="w-full">
          {/* Concentration Risk */}
          <AccordionItem value="risk">
            <AccordionTrigger className="text-sm font-medium hover:no-underline">
              <div className="flex items-center gap-2">
                <Shield className="w-4 h-4 text-blue-600" />
                <span>Concentration Risk</span>
              </div>
            </AccordionTrigger>
            <AccordionContent>
              <div className="space-y-3 pt-2">
                <div className="flex items-center justify-between p-3 rounded-lg bg-gray-50">
                  <span className="text-sm text-gray-600">Largest Position</span>
                  <span className="text-sm font-semibold text-gray-900">
                    {formatPercent(largest_position_pct)}
                  </span>
                </div>
                <div className="flex items-center justify-between p-3 rounded-lg bg-gray-50">
                  <span className="text-sm text-gray-600">Risk Level</span>
                  <Badge className={`text-xs ${getRiskBadgeStyle(concentration_risk)}`}>
                    {getConcentrationLabel(concentration_risk)}
                  </Badge>
                </div>
                <div className="p-2 bg-yellow-50 rounded-lg border border-yellow-100">
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 text-yellow-600 mt-0.5" />
                    <p className="text-xs text-yellow-800">
                      {concentration_risk === 'critical' || concentration_risk === 'high'
                        ? 'Your portfolio is heavily concentrated in a few positions. Consider diversifying to reduce risk.'
                        : concentration_risk === 'medium'
                        ? 'Moderate concentration detected. Monitor your largest positions closely.'
                        : 'Your portfolio shows healthy diversification across positions.'}
                    </p>
                  </div>
                </div>
              </div>
            </AccordionContent>
          </AccordionItem>

          {/* Diversification Score */}
          <AccordionItem value="diversification">
            <AccordionTrigger className="text-sm font-medium hover:no-underline">
              <div className="flex items-center gap-2">
                <PieChart className="w-4 h-4 text-blue-600" />
                <span>Diversification</span>
              </div>
            </AccordionTrigger>
            <AccordionContent>
              <div className="space-y-3 pt-2">
                <div className="flex items-center justify-between p-3 rounded-lg bg-gray-50">
                  <span className="text-sm text-gray-600">Diversification Score</span>
                  <Badge className={`text-xs ${getDiversificationBadgeStyle(diversification_score)}`}>
                    {typeof diversification_score === 'number' 
                      ? `${(diversification_score * 100).toFixed(0)}%`
                      : 'N/A'}
                  </Badge>
                </div>
                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className={`h-full transition-all ${
                      diversification_score >= 0.7
                        ? 'bg-green-500'
                        : diversification_score >= 0.4
                        ? 'bg-yellow-500'
                        : 'bg-red-500'
                    }`}
                    style={{ width: `${(diversification_score * 100).toFixed(0)}%` }}
                  />
                </div>
                <p className="text-xs text-gray-600">
                  {diversification_score >= 0.7
                    ? 'Excellent diversification across sectors and positions.'
                    : diversification_score >= 0.4
                    ? 'Adequate diversification, but room for improvement.'
                    : 'Low diversification. Consider adding more positions to reduce risk.'}
                </p>
              </div>
            </AccordionContent>
          </AccordionItem>

          {/* Sector Breakdown */}
          <AccordionItem value="sectors">
            <AccordionTrigger className="text-sm font-medium hover:no-underline">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-blue-600" />
                <span>Sector Breakdown</span>
              </div>
            </AccordionTrigger>
            <AccordionContent>
              <div className="space-y-2 pt-2">
                {Object.entries(sector_breakdown).length > 0 ? (
                  Object.entries(sector_breakdown)
                    .sort(([, a], [, b]) => b - a)
                    .map(([sector, weight]) => {
                      const weightPct = weight * 100  // Convert from 0-1 to 0-100
                      return (
                        <div key={sector} className="space-y-1">
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-gray-700">{sector}</span>
                            <span className="font-semibold text-gray-900">
                              {formatPercent(weightPct)}
                            </span>
                          </div>
                          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-blue-500 transition-all"
                              style={{ width: `${weightPct}%` }}
                            />
                          </div>
                        </div>
                      )
                    })
                ) : (
                  <p className="text-xs text-gray-500 italic">No sector data available</p>
                )}
              </div>
            </AccordionContent>
          </AccordionItem>

          {/* Holdings List */}
          <AccordionItem value="holdings">
            <AccordionTrigger className="text-sm font-medium hover:no-underline">
              <div className="flex items-center gap-2">
                <Wallet className="w-4 h-4 text-blue-600" />
                <span>Holdings ({holdingsCount})</span>
              </div>
            </AccordionTrigger>
            <AccordionContent>
              <div className="space-y-2 pt-2">
                {holdingsArray.length > 0 ? (
                  <div className="space-y-2">
                    {holdingsArray.map((holding, index) => (
                      <div
                        key={`${holding.ticker}-${index}`}
                        className="flex items-center justify-between p-2 rounded-lg border border-gray-200 bg-white hover:bg-gray-50 transition-colors"
                      >
                        <div className="flex-1">
                          <div className="font-semibold text-sm text-gray-900">
                            {holding.ticker}
                          </div>
                          <div className="text-xs text-gray-500">
                            {formatPercent(holding.weight_pct)} of portfolio
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm font-semibold text-gray-900">
                            {formatCurrency(holding.value)}
                          </div>
                          {holding.composite_score > 0 && (
                            <Badge variant="outline" className="text-xs">
                              Score: {holding.composite_score.toFixed(2)}
                            </Badge>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-gray-500 italic">No holdings data available</p>
                )}
              </div>
            </AccordionContent>
          </AccordionItem>

          {/* Top 3 Holdings */}
          {top_3_holdings && top_3_holdings.length > 0 && (
            <AccordionItem value="top3">
              <AccordionTrigger className="text-sm font-medium hover:no-underline">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-blue-600" />
                  <span>Top 3 Positions</span>
                </div>
              </AccordionTrigger>
              <AccordionContent>
                <div className="space-y-2 pt-2">
                  {top_3_holdings.map((holding, index) => (
                    <div
                      key={`${holding.ticker}-top${index}`}
                      className="flex items-center gap-3 p-3 rounded-lg bg-gradient-to-r from-blue-50 to-cyan-50 border border-blue-100"
                    >
                      <span className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-600 text-white text-xs font-bold flex items-center justify-center">
                        {index + 1}
                      </span>
                      <div className="flex-1">
                        <div className="font-semibold text-sm text-gray-900">
                          {holding.ticker}
                        </div>
                        <div className="text-xs text-gray-600">
                          {formatPercent(holding.weight_pct)} of portfolio
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-semibold text-gray-900">
                          {formatCurrency(holding.value)}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </AccordionContent>
            </AccordionItem>
          )}
        </Accordion>

        <Separator />

        <div className="text-xs text-gray-500 italic">
          💼 Portfolio analysis based on current holdings. Data updated in real-time.
        </div>
      </CardContent>
    </Card>

    {/* VEE Multi-Level Accordions (like single ticker) */}
    <VEEAccordions
      veeExplanations={veeExplanations}
      explainability={{}}
      numericalPanel={numericalPanel}
      className="mt-6"
    />
    </>
  )
}
