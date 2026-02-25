/**
 * COMPARISON NODE UI - UNIFIED DESIGN
 * 
 * Displays multi-ticker comparative analysis from ComparisonNode
 * Shows factor winners, deltas, ranking, and range dispersion
 * 
 * UPDATED: Dec 2, 2025 - Unified with single ticker UX design pattern
 * - Added UnifiedLayout wrapper
 * - Added FactorRadarChart visualization
 * - Added MetricCard components
 * - Added DarkTooltip for metrics
 * 
 * Backend Node: comparison_node.py
 * State Keys: state.comparison_state
 * 
 * Props:
 * - comparisonState: object with { tickers, ranking_order, winner_by_factor, factor_deltas, range, range_pct }
 * - className?: string
 */

'use client'

import { TrendingUp, Activity, AlertTriangle, MessageCircle, Award, BarChart3, Target, Zap, BookOpen, Gift } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion'
import FactorRadarChart from '../analytics/charts/FactorRadarChart'
import ComparativeRadarChart from '../analytics/charts/ComparativeRadarChart'
import UnifiedLayout from '../layouts/UnifiedLayout'
import { MetricCard, ZScoreCardMulti } from '../cards/CardLibrary'
import { FactorDeltaTooltip, RankingTooltip, DispersionTooltip, DarkTooltip } from '../explainability/tooltips/TooltipLibrary'
import BlockchainLedgerBadge from '../blockchain/BlockchainLedgerBadge'
import ComparisonSentimentCard from '../comparison/ComparisonSentimentCard'
import ComparisonCompositeScoreCard from '../comparison/ComparisonCompositeScoreCard'
import RiskComparisonNodeUI from '../comparison/RiskComparisonNodeUI'
import FundamentalsComparisonNodeUI from '../comparison/FundamentalsComparisonNodeUI'
import NormalizedPerformanceChart from '../analytics/charts/NormalizedPerformanceChart'
import { RiskPanel } from '../analytics/panels'
import { VWRETooltip } from '../explainability/tooltips/TooltipLibrary'

// 🟣 FASE 2: Build comparison_state from comparison_matrix + numerical_panel when backend doesn't populate it (Dec 10, 2025)
function buildComparisonStateFromMatrix(comparisonMatrix, numericalPanel) {
  if (!comparisonMatrix || !numericalPanel || numericalPanel.length < 2) {
    return null
  }

  // Extract ranking_order (sort by composite_score)
  const ranking_order = [...numericalPanel]
    .sort((a, b) => (b.composite_score || 0) - (a.composite_score || 0))
    .map(item => item.ticker)

  // Extract winner_by_factor (max z-score per factor)
  const winner_by_factor = {}
  const factors = ['momentum_z', 'trend_z', 'sentiment_z', 'vola_z']
  factors.forEach(factor => {
    const winner = numericalPanel.reduce((max, item) => 
      (item[factor] || -999) > (max[factor] || -999) ? item : max
    )
    if (winner && winner.ticker) {
      winner_by_factor[factor] = winner.ticker
    }
  })

  // Extract factor_deltas from comparison_matrix or compute
  const factor_deltas = comparisonMatrix.deltas || {}
  
  // Extract range and range_pct
  const range = comparisonMatrix.range || (comparisonMatrix.range_pct / 100) || 0
  const range_pct = comparisonMatrix.range_pct || 0

  return {
    ranking_order,
    winner_by_factor,
    factor_deltas,
    range,
    range_pct,
    num_tickers: numericalPanel.length,
    timestamp: new Date().toISOString()
  }
}

// Helper function to render text with **bold** as <strong>
function renderTextWithBold(text) {
  if (!text) return text
  
  const parts = text.split('**')
  return parts.map((part, index) => {
    if (index % 2 === 1) {
      return <strong key={index}>{part}</strong>
    }
    return part
  })
}

export default function ComparisonNodeUI({ 
  comparisonMatrix,
  comparisonState, 
  narrative,
  veeExplanations,
  explainability,
  numericalPanel,
  className = '' 
}) {
  // � PHASE 1: Detect comparison mode (Dec 19, 2025)
  const isComparisonMode = numericalPanel && numericalPanel.length >= 2
  const tickerCount = numericalPanel?.length || 0
  
  // �🟣 FASE 2: Build comparison_state from comparison_matrix if backend didn't populate it (Dec 10, 2025)
  let effectiveComparisonState = comparisonState
  
  if (!comparisonState || !comparisonState.ranking_order) {
    // [DEV] Building comparison_state from matrix
    effectiveComparisonState = buildComparisonStateFromMatrix(comparisonMatrix, numericalPanel)
  }
  
  // Backward compatibility: Support both old comparisonState and new comparisonMatrix
  const dataSource = effectiveComparisonState || {}
  
  // ✅ FIX (Dec 21, 2025): Extract tickers from numericalPanel (NEVER from comparison_matrix keys)
  // comparison_matrix is object with keys ["winner", "loser", "range_pct", "deltas"] (NOT tickers!)
  let tickers = []
  if (numericalPanel && Array.isArray(numericalPanel)) {
    // Primary source: numericalPanel (contains real ticker data)
    tickers = numericalPanel.map(item => item.ticker)
  } else if (Array.isArray(comparisonMatrix)) {
    // Fallback: comparisonMatrix as array (legacy format)
    tickers = comparisonMatrix.map(item => item.ticker || item)
  } else {
    // Last resort: comparison_state tickers
    tickers = dataSource.tickers || []
  }
  
  // Guard: Don't render if no comparison data
  if ((!comparisonMatrix || comparisonMatrix.length < 2) && (!comparisonState || !comparisonState.tickers || comparisonState.tickers.length < 2)) {
    return (
      <UnifiedLayout
        title="Comparison Analysis"
        icon={BarChart3}
        iconColor="text-purple-600"
        narrative={narrative}
        className={className}
      >
        <div className="bg-yellow-50 border border-yellow-200 p-6 rounded-lg text-center">
          <div className="text-yellow-600 mb-2">⚠️</div>
          <p className="text-sm font-medium text-yellow-800 mb-2">No Comparison Data Available</p>
          <p className="text-xs text-yellow-700">
            Neural Engine data not available for these tickers. Try different tickers or check back later.
          </p>
        </div>
      </UnifiedLayout>
    )
  }

  // 🔵 PHASE 2: Guardrails for ticker count (Dec 19, 2025)
  // >3 tickers → block and suggest Screening
  if (tickerCount > 3) {
    return (
      <UnifiedLayout
        title="Comparison Analysis"
        icon={BarChart3}
        iconColor="text-purple-600"
        narrative={narrative}
        className={className}
      >
        <div className="bg-orange-50 border border-orange-300 p-8 rounded-lg text-center">
          <div className="text-orange-600 mb-4">
            <BarChart3 className="w-16 h-16 mx-auto" />
          </div>
          <p className="text-lg font-semibold text-orange-900 mb-3">Too Many Tickers for Direct Comparison</p>
          <p className="text-sm text-orange-800 mb-4">
            Direct comparison works best with <strong>two assets</strong>. You've selected {tickerCount} tickers.
          </p>
          <p className="text-sm text-orange-700 mb-6">
            For analyzing {tickerCount}+ tickers, we recommend using <strong>Screening</strong> instead.
          </p>
          <div 
            role="button" 
            tabIndex={0}
            className="inline-block px-6 py-3 bg-orange-600 hover:bg-orange-700 text-white font-medium rounded-lg transition-colors cursor-pointer"
            onClick={() => {/* TODO: Navigate to Screening */}}
            onKeyDown={(e) => {/* TODO: Navigate to Screening */}}
          >
            Switch to Screening →
          </div>
        </div>
      </UnifiedLayout>
    )
  }

  // 🟡 PHASE 2: Warning for 3 tickers (show UI but with warning banner)
  const showThreeTickerWarning = tickerCount === 3


  // Extract ranking from comparisonMatrix (backend format)
  let ranking_order = []
  if (Array.isArray(comparisonMatrix)) {
    ranking_order = [...comparisonMatrix].sort((a, b) => a.rank - b.rank).map(item => item.ticker)
  } else {
    ranking_order = dataSource.ranking_order || []
  }
  
  const {
    winner_by_factor = {},
    factor_deltas = {},
    range = 0,
    range_pct = 0
  } = dataSource

  // Helper: Format factor name
  const formatFactorName = (factor) => {
    const names = {
      momentum_z: 'Momentum',
      trend_z: 'Trend',
      volatility_z: 'Volatility',
      sentiment_z: 'Sentiment',
      dividend_yield_z: 'Dividend',
      composite_score: 'Overall Score'
    }
    return names[factor] || factor
  }

  // Helper: Get badge color based on delta
  const getDeltaBadgeColor = (delta) => {
    if (delta > 0.5) return 'bg-green-500 text-white'
    if (delta > 0) return 'bg-green-100 text-green-700'
    if (delta < -0.5) return 'bg-red-500 text-white'
    if (delta < 0) return 'bg-red-100 text-red-700'
    return 'bg-gray-100 text-gray-700'
  }

  // Helper: Format delta with sign
  const formatDelta = (delta) => {
    if (typeof delta !== 'number') return 'N/A'
    const sign = delta >= 0 ? '+' : ''
    return `${sign}${delta.toFixed(2)}`
  }

  // Helper: Get dispersion risk level
  const getDispersionRisk = (rangePct) => {
    if (rangePct > 40) return { label: 'High Divergence', color: 'bg-red-100 text-red-700' }
    if (rangePct > 20) return { label: 'Moderate Spread', color: 'bg-yellow-100 text-yellow-700' }
    return { label: 'Low Variance', color: 'bg-green-100 text-green-700' }
  }

  const dispersionRisk = getDispersionRisk(range_pct)

  // Extract comparison VEE (not per-ticker, but for the comparison itself)
  const comparisonVEE = veeExplanations?.comparison || veeExplanations?.[Object.keys(veeExplanations || {})[0]]

  return (
    <div className="space-y-0">
      {/* 🎯 AnalysisHeader now rendered by chat.jsx (Dec 21, 2025 - COO decision) */}
      {/* Centralized header management for all conversation types */}

      <UnifiedLayout
        title="Comparison Analysis"
        icon={BarChart3}
        iconColor="text-purple-600"
        narrative={narrative}
        className={className}
      >
      
      {/* 🟡 PHASE 2: Warning banner for 3 tickers (Dec 19, 2025) */}
      {showThreeTickerWarning && (
        <div className="mb-4 bg-yellow-50 border border-yellow-300 p-4 rounded-lg flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-sm font-medium text-yellow-900 mb-1">3-Ticker Comparison</p>
            <p className="text-xs text-yellow-800">
              Comparison works best with <strong>two assets</strong>. With 3 tickers, some insights may be harder to interpret. 
              Consider using Screening for broader analysis.
            </p>
          </div>
        </div>
      )}
      
      {/* Blockchain Registration Badge - Prominent display */}
      <div className="mb-6">
        <BlockchainLedgerBadge 
          variant="detailed"
          txHash={null}  // TODO: Pass from backend ledger system
          network="nile"
        />
      </div>

      {/* Market Intelligence - VEE Accordion (MOVED UP - after narrative, like SingleTickerUI) */}
      {comparisonVEE && (
        <div className="mb-6 border border-gray-200 rounded-lg bg-white shadow-sm">
          <div className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-gray-200">
            <div className="flex items-center gap-2">
              <BookOpen size={16} className="text-blue-600" />
              <span className="font-semibold text-sm text-gray-900">📊 Market Intelligence</span>
              <span className="text-xs text-gray-400 ml-1">Multi-level VEE® Analysis</span>
            </div>
          </div>

          <div className="p-4 space-y-3">
            {/* Summary Accordion */}
            {comparisonVEE.summary && (
              <details className="border border-gray-200 rounded-lg overflow-hidden bg-white">
                <summary className="cursor-pointer p-3 bg-blue-50 hover:bg-blue-100 font-medium text-sm text-gray-900">
                  📊 Summary
                </summary>
                <div className="p-3 text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                  {renderTextWithBold(comparisonVEE.summary)}
                </div>
              </details>
            )}

            {/* Technical Accordion */}
            {comparisonVEE.technical && (
              <details className="border border-gray-200 rounded-lg overflow-hidden bg-white">
                <summary className="cursor-pointer p-3 bg-indigo-50 hover:bg-indigo-100 font-medium text-sm text-gray-900">
                  🔧 Technical
                </summary>
                <div className="p-3 text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                  {renderTextWithBold(comparisonVEE.technical)}
                </div>
              </details>
            )}

            {/* Detailed Analysis Accordion */}
            {comparisonVEE.detailed && (
              <details className="border border-gray-200 rounded-lg overflow-hidden bg-white">
                <summary className="cursor-pointer p-3 bg-green-50 hover:bg-green-100 font-medium text-sm text-gray-900">
                  📖 Detailed Analysis
                </summary>
                <div className="p-3 text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                  {renderTextWithBold(comparisonVEE.detailed)}
                </div>
              </details>
            )}

            {/* Contextualized Accordion */}
            {comparisonVEE.contextualized && (
              <details className="border border-gray-200 rounded-lg overflow-hidden bg-white">
                <summary className="cursor-pointer p-3 bg-yellow-50 hover:bg-yellow-100 font-medium text-sm text-gray-900">
                  🎯 Contextualized
                </summary>
                <div className="p-3 text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                  {renderTextWithBold(comparisonVEE.contextualized)}
                </div>
              </details>
            )}
          </div>
        </div>
      )}

      {/* 🎯 FACTOR ANALYSIS ACCORDION - Organized comparison data */}
      <Accordion type="single" collapsible className="w-full mb-6">
        <AccordionItem value="factors">
          <AccordionTrigger className="text-left">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-blue-600" />
              <span className="font-semibold">Factor Analysis</span>
              <span className="text-xs text-gray-500 ml-2">Z-scores and sentiment comparison</span>
            </div>
          </AccordionTrigger>
          <AccordionContent className="pt-4">
            <div className="space-y-4">
              {/* Market Sentiment Comparison */}
              <ComparisonSentimentCard tickers={numericalPanel} />

              {/* Neural Engine Factor Comparison Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {/* Momentum Comparison */}
          <ZScoreCardMulti
            label="Momentum"
            icon={TrendingUp}
            tickers={numericalPanel}
            factorKey="momentum_z"
            inverted={false}
            veeSimple="Momentum: Price acceleration across comparison tickers"
            veeTechnical="Average momentum z-score shows relative strength vs market. Positive values indicate buying pressure, negative values suggest distribution."
          />
          
          {/* Trend Comparison */}
          <ZScoreCardMulti
            label="Trend"
            icon={Activity}
            tickers={numericalPanel}
            factorKey="trend_z"
            inverted={false}
            veeSimple="Trend: SMA/EMA consensus across comparison tickers"
            veeTechnical="Average trend z-score reflects structural momentum. Higher values indicate aligned uptrends, lower values suggest downward pressure."
          />
          
          {/* Volatility Comparison */}
          <ZScoreCardMulti
            label="Volatility"
            icon={AlertTriangle}
            tickers={numericalPanel}
            factorKey="vola_z"
            inverted={true}
            veeSimple="Volatility: Price stability (lower is better)"
            veeTechnical="Average volatility z-score (inverted). Lower values indicate more stable price action, higher values suggest increased risk."
          />
          
          {/* Sentiment Comparison */}
          <ZScoreCardMulti
            label="Sentiment"
            icon={MessageCircle}
            tickers={numericalPanel}
            factorKey="sentiment_z"
            inverted={false}
            veeSimple="Sentiment: Market perception across comparison tickers"
            veeTechnical="Average sentiment z-score from social media and news analysis. Positive values indicate bullish consensus, negative values bearish."
          />
        </div>
        
        {/* Composite Score Comparison (THIRD - overall ranking) */}
        <ComparisonCompositeScoreCard tickers={numericalPanel} />
        
        {/* Risk Comparison (FOURTH - risk analysis with table + bars) */}
        <RiskComparisonNodeUI 
          tickers={numericalPanel} 
          veeNarrative={comparisonVEE?.risk_narrative}
        />
        
      {/* 🎯 RISK ANALYSIS ACCORDION */}
      <Accordion type="single" collapsible className="w-full mb-6">
        <AccordionItem value="risk">
          <AccordionTrigger className="text-left">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-orange-600" />
              <span className="font-semibold">Risk Analysis</span>
              <span className="text-xs text-gray-500 ml-2">VARE multi-dimensional risk assessment</span>
            </div>
          </AccordionTrigger>
          <AccordionContent className="pt-4">
            {numericalPanel && numericalPanel.length >= 2 && (
              <div className={`grid gap-4 ${
                numericalPanel.length === 2 ? 'grid-cols-1 md:grid-cols-2' :
                numericalPanel.length === 3 ? 'grid-cols-1 md:grid-cols-3' :
                'grid-cols-1 md:grid-cols-2 lg:grid-cols-4'
              }`}>
                {numericalPanel.map((ticker, index) => {
                  const riskData = {
                    vare_risk_score: ticker.vare_risk_score || 0,
                    vare_risk_category: ticker.vare_risk_category || 'UNKNOWN',
                    vare_confidence: ticker.vare_confidence || 0,
                    market_risk: ticker.market_risk || 0,
                    volatility_risk: ticker.volatility_risk || 0,
                    liquidity_risk: ticker.liquidity_risk || 0,
                    correlation_risk: ticker.correlation_risk || 0,
                    composite_score_original: ticker.composite_score_original || ticker.composite_score || 0
                  }

                  return (
                    <div key={ticker.ticker} className={index === 0 ? 'border-2 border-purple-300' : 'border border-gray-200'}>
                      <RiskPanel
                        ticker={ticker.ticker}
                        riskData={riskData}
                        className="h-full"
                      />
                    </div>
                  )
                })}
              </div>
            )}
          </AccordionContent>
        </AccordionItem>
      </Accordion>
        
      {/* 🎯 ATTRIBUTION ANALYSIS ACCORDION */}
      <Accordion type="single" collapsible className="w-full mb-6">
        <AccordionItem value="attribution">
          <AccordionTrigger className="text-left">
            <div className="flex items-center gap-2">
              <Award className="w-5 h-5 text-purple-600" />
              <span className="font-semibold">Attribution Analysis</span>
              <span className="text-xs text-gray-500 ml-2">VWRE factor contribution breakdown</span>
            </div>
          </AccordionTrigger>
          <AccordionContent className="pt-4">
            {numericalPanel && numericalPanel.some(t => t.primary_driver) && (
              <div className="bg-gradient-to-br from-indigo-50 to-purple-50 border border-indigo-200 rounded-lg p-6">
                <div className="flex items-center gap-2 mb-4">
                  <Award className="w-5 h-5 text-indigo-600" />
                  <h3 className="text-lg font-bold text-gray-900">VWRE® Attribution Analysis</h3>
                </div>

                <div className={`grid gap-4 ${
                  numericalPanel.length === 2 ? 'grid-cols-1 md:grid-cols-2' :
                  numericalPanel.length === 3 ? 'grid-cols-1 md:grid-cols-3' :
                  'grid-cols-1 md:grid-cols-2 lg:grid-cols-4'
                }`}>
                  {numericalPanel.map((ticker, index) => (
                    <div key={ticker.ticker} className={`p-4 rounded-lg ${
                      index === 0 ? 'bg-purple-100 border-2 border-purple-400' : 'bg-white border border-gray-300'
                    }`}>
                      <div className="flex items-center justify-between mb-3">
                        <span className="font-bold text-lg text-gray-900">{ticker.ticker}</span>
                        {index === 0 && <Award className="w-5 h-5 text-purple-600" />}
                      </div>

                      {/* Primary Driver */}
                      {ticker.primary_driver && (
                        <div className="mb-2">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-semibold text-gray-600 uppercase">Primary Driver</span>
                            <VWRETooltip primaryDriver={ticker.primary_driver} ticker={ticker.ticker} />
                          </div>
                          <div className="text-2xl font-bold text-indigo-700">{ticker.primary_driver}</div>
                        </div>
                      )}

                      {/* Rank Explanation */}
                      {ticker.rank_explanation && (
                        <p className="text-sm text-gray-700 leading-relaxed mt-2">
                          {ticker.rank_explanation}
                        </p>
                      )}

                      {/* Composite Score */}
                      <div className="mt-3 pt-3 border-t border-gray-300">
                        <div className="flex justify-between items-center">
                          <span className="text-xs text-gray-600">Composite Score</span>
                          <span className="font-bold text-gray-900">{(ticker.composite_score || 0).toFixed(3)}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </AccordionContent>
        </AccordionItem>
      </Accordion>
        
      {/* 🎯 FUNDAMENTALS ANALYSIS ACCORDION */}
      <Accordion type="single" collapsible className="w-full mb-6">
        <AccordionItem value="fundamentals">
          <AccordionTrigger className="text-left">
            <div className="flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-green-600" />
              <span className="font-semibold">Fundamentals</span>
              <span className="text-xs text-gray-500 ml-2">Financial metrics comparison</span>
            </div>
          </AccordionTrigger>
          <AccordionContent className="pt-4">
            <FundamentalsComparisonNodeUI
              tickers={numericalPanel}
              veeNarrative={comparisonVEE?.fundamentals_narrative}
            />
          </AccordionContent>
        </AccordionItem>
      </Accordion>
        
      {/* 🎯 PERFORMANCE ANALYSIS ACCORDION */}
      <Accordion type="single" collapsible className="w-full mb-6">
        <AccordionItem value="performance">
          <AccordionTrigger className="text-left">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-indigo-600" />
              <span className="font-semibold">Performance</span>
              <span className="text-xs text-gray-500 ml-2">Historical price comparison</span>
            </div>
          </AccordionTrigger>
          <AccordionContent className="pt-4">
            <NormalizedPerformanceChart
              tickers={numericalPanel}
              veeNarrative={comparisonVEE?.performance_narrative}
            />
          </AccordionContent>
        </AccordionItem>
      </Accordion>
      </div>

      {/* Key Metrics Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-6">
        <MetricCard
          label="Winner"
          value={ranking_order[0]}
          color="purple"
          subtitle="Overall top performer"
          tooltip="Ticker with highest composite score across all factors"
        />
        <MetricCard
          label="Dispersion"
          value={dispersionRisk.label}
          color={range_pct > 40 ? 'red' : range_pct > 20 ? 'yellow' : 'green'}
          subtitle={`${typeof range_pct === 'number' ? range_pct.toFixed(1) : 'N/A'}% range`}
          tooltip="Measures how different the tickers perform relative to each other"
        />
        <MetricCard
          label="Max Delta"
          value={formatDelta(Math.max(...Object.values(factor_deltas)))}
          color={Math.max(...Object.values(factor_deltas)) > 0.5 ? 'green' : 'gray'}
          subtitle="Largest factor difference"
          tooltip="Biggest performance gap in any single factor"
        />
      </div>

      {/* Split Layout: Accordions Left, Radar Right */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Accordions */}
        <div>
          <Accordion type="single" collapsible defaultValue="ranking" className="w-full">
          {/* Ranking Order */}
          <AccordionItem value="ranking">
            <AccordionTrigger className="text-sm font-medium hover:no-underline">
              <div className="flex items-center gap-2">
                <Award className="w-4 h-4 text-purple-600" />
                <span>Overall Ranking</span>
              </div>
            </AccordionTrigger>
            <AccordionContent>
              <div className="space-y-2 pt-2">
                {ranking_order.map((ticker, index) => (
                  <div
                    key={ticker}
                    className="flex items-center justify-between p-2 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors"
                  >
                    <div className="flex items-center gap-2">
                      <span className={`
                        font-bold text-sm w-6 h-6 rounded-full flex items-center justify-center
                        ${index === 0 ? 'bg-purple-600 text-white' : 'bg-gray-300 text-gray-700'}
                      `}>
                        {index + 1}
                      </span>
                      <span className="font-medium text-gray-900">{ticker}</span>
                    </div>
                    {index === 0 && (
                      <Badge className="bg-purple-600 text-white text-xs">
                        Winner
                      </Badge>
                    )}
                  </div>
                ))}
              </div>
            </AccordionContent>
          </AccordionItem>

          {/* Factor Winners */}
          <AccordionItem value="winners">
            <AccordionTrigger className="text-sm font-medium hover:no-underline">
              <div className="flex items-center gap-2">
                <Target className="w-4 h-4 text-purple-600" />
                <span>Factor Winners</span>
              </div>
            </AccordionTrigger>
            <AccordionContent>
              <div className="grid grid-cols-1 gap-2 pt-2">
                {Object.entries(winner_by_factor).map(([factor, winner]) => (
                  <div
                    key={factor}
                    className="flex items-center justify-between p-2 rounded-lg border border-gray-200 bg-white"
                  >
                    <div className="flex items-center gap-2">
                      {factor === 'dividend_yield_z' && <Gift className="w-4 h-4 text-green-600" />}
                      <span className="text-sm text-gray-600">{formatFactorName(factor)}</span>
                    </div>
                    <Badge variant="outline" className="text-xs font-semibold">
                      {winner}
                    </Badge>
                  </div>
                ))}
              </div>
            </AccordionContent>
          </AccordionItem>

          {/* Factor Deltas */}
          <AccordionItem value="deltas">
            <AccordionTrigger className="text-sm font-medium hover:no-underline">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-purple-600" />
                <span>Factor Deltas</span>
                <DarkTooltip asSpan content="Performance difference between top and bottom ticker for each factor" />
              </div>
            </AccordionTrigger>
            <AccordionContent>
              <div className="space-y-2 pt-2">
                {Object.entries(factor_deltas).map(([factor, delta]) => (
                  <div
                    key={factor}
                    className="flex items-center justify-between p-2 rounded-lg bg-gray-50"
                  >
                    <div className="flex items-center gap-1">
                      <span className="text-sm text-gray-600">{formatFactorName(factor)}</span>
                      <DarkTooltip asSpan content={`${formatFactorName(factor)} z-score difference: ${formatDelta(delta)}`} />
                    </div>
                    <Badge className={`text-xs font-mono ${getDeltaBadgeColor(delta)}`}>
                      {formatDelta(delta)}
                    </Badge>
                  </div>
                ))}
              </div>
              <div className="mt-3 p-2 bg-blue-50 rounded-lg border border-blue-100">
                <p className="text-xs text-blue-800">
                  💡 <strong>Deltas</strong> show the difference between the top performer and the lowest for each factor.
                  Positive = first ticker leads, negative = second ticker leads.
                </p>
              </div>
            </AccordionContent>
          </AccordionItem>

          {/* Range / Dispersion */}
          <AccordionItem value="dispersion">
            <AccordionTrigger className="text-sm font-medium hover:no-underline">
              <div className="flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-purple-600" />
                <span>Score Dispersion</span>
                <DarkTooltip asSpan content="Statistical measure of how spread out the composite scores are" />
              </div>
            </AccordionTrigger>
            <AccordionContent>
              <div className="space-y-3 pt-2">
                <div className="flex items-center justify-between p-3 rounded-lg bg-gray-50">
                  <div className="flex items-center gap-1">
                    <span className="text-sm text-gray-600">Range</span>
                    <DarkTooltip asSpan content="Absolute difference between highest and lowest composite score" />
                  </div>
                  <span className="text-sm font-semibold text-gray-900">
                    {typeof range === 'number' ? range.toFixed(2) : 'N/A'}
                  </span>
                </div>
                <div className="flex items-center justify-between p-3 rounded-lg bg-gray-50">
                  <div className="flex items-center gap-1">
                    <span className="text-sm text-gray-600">Range %</span>
                    <DarkTooltip asSpan content="Range as percentage of average score. >40% = high divergence" />
                  </div>
                  <Badge className={`text-xs ${dispersionRisk.color}`}>
                    {typeof range_pct === 'number' ? `${range_pct.toFixed(1)}%` : 'N/A'}
                  </Badge>
                </div>
                <div className="p-2 rounded-lg border border-gray-200 bg-white">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-semibold text-gray-700">Assessment:</span>
                    <Badge className={`text-xs ${dispersionRisk.color}`}>
                      {dispersionRisk.label}
                    </Badge>
                  </div>
                  <p className="text-xs text-gray-600">
                    {range_pct > 40
                      ? 'Significant differences detected. Tickers show distinct performance profiles.'
                      : range_pct > 20
                      ? 'Moderate variance. Some differences in factor performance.'
                      : 'Low variance. Tickers show similar performance patterns.'}
                  </p>
                </div>
              </div>
            </AccordionContent>
          </AccordionItem>

        </Accordion>
        </div>

        {/* Right: Comparative Radar Chart (Dec 21, 2025) */}
        <div>
          <ComparativeRadarChart 
            tickers={ranking_order}
            numericalPanel={numericalPanel}
          />
              </div>
            </div>
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    </UnifiedLayout>
    </div>
  )
}
