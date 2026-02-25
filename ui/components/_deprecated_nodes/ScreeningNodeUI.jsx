/**
 * SCREENING NODE UI - 2-4 Tickers Ranking
 * 
 * Purpose: Display ranked list of 2-4 tickers with composite scores.
 * Backend provides screening_data with ranking and signals.
 * 
 * Props:
 * - screeningData: {tickers, ranking, signals} - Backend ranking data
 * - narrative: string - VEE conversational explanation
 * - veeExplanations: object - Multi-level VEE (optional)
 * - numericalPanel: array - Composite scores
 * - className: string
 */

'use client'

import { TrendingUp, TrendingDown, Minus, ArrowUp, ArrowDown, Gift } from 'lucide-react'
import CompositeBarChart from '../analytics/charts/CompositeBarChart'
import MetricsHeatmap from '../analytics/charts/MetricsHeatmap'
import RiskRewardScatter from '../analytics/charts/RiskRewardScatter'
import MiniRadarGrid from '../analytics/charts/MiniRadarGrid'
import VEEAccordions from '../explainability/vee/VEEAccordions'
import { VeeTooltip } from '../explainability/tooltips/TooltipLibrary'
import { BaseCard } from '../cards/CardLibrary'
import { VAREBadge, VARETooltip } from '../explainability/tooltips/TooltipLibrary'

export default function ScreeningNodeUI({ 
  screeningData, 
  narrative, 
  veeExplanations,
  explainability,
  numericalPanel,
  className = '' 
}) {
  // Guard: Require screening_data
  if (!screeningData || !screeningData.ranking || screeningData.ranking.length === 0) {
    return (
      <div className={`bg-yellow-50 border border-yellow-200 p-4 rounded-lg ${className}`}>
        <p className="text-sm text-yellow-800">⚠️ No screening data available</p>
      </div>
    )
  }

  const { ranking, signals } = screeningData

  // Helper: Get signal color
  const getSignalColor = (value) => {
    if (value > 0.5) return 'text-green-600 bg-green-50'
    if (value < -0.5) return 'text-red-600 bg-red-50'
    return 'text-gray-600 bg-gray-50'
  }

  // Helper: Get signal icon
  const getSignalIcon = (value) => {
    if (value > 0.5) return <ArrowUp size={14} className="text-green-600" />
    if (value < -0.5) return <ArrowDown size={14} className="text-red-600" />
    return <Minus size={14} className="text-gray-600" />
  }

  return (
    <div className={`space-y-4 ${className}`}>

      {/* VEE Narrative */}
      {narrative && (
        <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-4 rounded-lg border border-blue-100">
          <div className="text-sm text-gray-700 leading-relaxed">
            {narrative.split('\n').map((line, i) => (
              line.trim() ? <p key={i} className="mb-2">{line}</p> : <br key={i} />
            ))}
          </div>
        </div>
      )}

      {/* Ranking Table */}
      <BaseCard variant="elevated" padding="none" className="overflow-hidden">
        <div className="bg-gradient-to-r from-purple-50 to-pink-50 px-4 py-3 border-b border-gray-200">
          <h3 className="font-semibold text-gray-900 flex items-center gap-2">
            <TrendingUp size={18} className="text-purple-600" />
            Screening Results ({ranking.length} tickers)
          </h3>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3 text-left font-semibold text-gray-700">Rank</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-700">Ticker</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">Composite</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">Momentum</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">Trend</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">Sentiment</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">Dividend</th>
                <th className="px-4 py-3 text-center font-semibold text-gray-700">Signal</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {ranking.map((item, index) => {
                const tickerSignals = signals?.[item.ticker] || {}
                const composite = tickerSignals.composite_score || item.composite || 0
                const momentum = tickerSignals.momentum_z || 0
                const trend = tickerSignals.trend_z || 0
                const sentiment = tickerSignals.sentiment_z || 0
                const dividend = tickerSignals.dividend_yield_z || 0

                return (
                  <tr key={item.ticker} className="hover:bg-gray-50 transition-colors">
                    {/* Rank */}
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full font-bold ${
                        index === 0 ? 'bg-yellow-100 text-yellow-800' :
                        index === 1 ? 'bg-gray-100 text-gray-800' :
                        'bg-gray-50 text-gray-600'
                      }`}>
                        {index + 1}
                      </span>
                    </td>

                    {/* Ticker with Logo */}
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <img 
                          src={`https://logo.clearbit.com/${item.ticker.toLowerCase()}.com`}
                          alt={`${item.ticker} logo`}
                          className="w-6 h-6 rounded"
                          onError={(e) => {
                            e.target.onerror = null
                            e.target.src = `https://storage.googleapis.com/iex/api/logos/${item.ticker}.png`
                          }}
                        />
                        <span className="font-bold text-gray-900">{item.ticker}</span>
                      </div>
                    </td>

                    {/* Composite Score */}
                    <td className="px-4 py-3 text-right">
                      <span className={`font-bold ${
                        composite > 0.5 ? 'text-green-600' :
                        composite < -0.5 ? 'text-red-600' :
                        'text-gray-600'
                      }`}>
                        {composite.toFixed(2)}
                      </span>
                    </td>

                    {/* Momentum */}
                    <td className="px-4 py-3 text-right">
                      <span className={`text-xs px-2 py-1 rounded ${getSignalColor(momentum)}`}>
                        {momentum.toFixed(2)}
                      </span>
                    </td>

                    {/* Trend */}
                    <td className="px-4 py-3 text-right">
                      <span className={`text-xs px-2 py-1 rounded ${getSignalColor(trend)}`}>
                        {trend.toFixed(2)}
                      </span>
                    </td>

                    {/* Sentiment */}
                    <td className="px-4 py-3 text-right">
                      <span className={`text-xs px-2 py-1 rounded ${getSignalColor(sentiment)}`}>
                        {sentiment.toFixed(2)}
                      </span>
                    </td>

                    {/* 🎯 VARE Risk Badge (Dec 24, 2025) */}
                    <td className="px-4 py-3 text-center">
                      {item.vare_risk_category && (
                        <div className="flex items-center justify-center gap-1">
                          <VAREBadge category={item.vare_risk_category} score={item.vare_risk_score} />
                          <VARETooltip 
                            riskScore={item.vare_risk_score || 0}
                            riskCategory={item.vare_risk_category}
                            marketRisk={item.market_risk || 0}
                            volatilityRisk={item.volatility_risk || 0}
                            liquidityRisk={item.liquidity_risk || 0}
                            correlationRisk={item.correlation_risk || 0}
                          />
                        </div>
                      )}
                    </td>

                    {/* Dividend */}
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        {dividend > 0.5 && <Gift className="w-4 h-4 text-green-600" />}
                        <span className={`text-xs px-2 py-1 rounded ${getSignalColor(dividend)}`}>
                          {dividend ? dividend.toFixed(2) : 'N/A'}
                        </span>
                        {explainability?.[item.ticker]?.dividend_yield_z && (
                          <VeeTooltip content={`Dividend Yield Z-Score: ${explainability[item.ticker].dividend_yield_z}`}>
                            <span className="text-xs text-gray-400 ml-1">ℹ️</span>
                          </VeeTooltip>
                        )}
                      </div>
                    </td>

                    {/* Signal Icon */}
                    <td className="px-4 py-3 text-center">
                      {getSignalIcon(composite)}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>

        {/* Quick Insights */}
        <div className="bg-gray-50 px-4 py-3 border-t border-gray-200 text-xs text-gray-600">
          <p>
            <strong>Top Pick:</strong> {ranking[0]?.ticker} (Composite: {(signals?.[ranking[0]?.ticker]?.composite_score || ranking[0]?.composite || 0).toFixed(2)})
          </p>
        </div>
      </BaseCard>

      {/* NEW CHARTS SECTION */}
      <div className="space-y-4">
        {/* 1. Composite Bar Chart */}
        <CompositeBarChart 
          data={ranking.map(item => ({
            ticker: item.ticker,
            composite: signals?.[item.ticker]?.composite_score || item.composite || 0
          }))}
        />

        {/* 2. Metrics Heatmap */}
        <MetricsHeatmap 
          data={ranking.map(item => ({
            ticker: item.ticker,
            momentum_z: signals?.[item.ticker]?.momentum_z || 0,
            trend_z: signals?.[item.ticker]?.trend_z || 0,
            vola_z: signals?.[item.ticker]?.vola_z || 0,
            sentiment_z: signals?.[item.ticker]?.sentiment_z || 0,
            dividend_yield_z: signals?.[item.ticker]?.dividend_yield_z || 0
          }))}
        />

        {/* 3. Risk-Reward Scatter */}
        <RiskRewardScatter 
          data={ranking.map(item => ({
            ticker: item.ticker,
            composite: signals?.[item.ticker]?.composite_score || item.composite || 0,
            momentum_z: signals?.[item.ticker]?.momentum_z || 0,
            vola_z: signals?.[item.ticker]?.vola_z || 0,
            sentiment_z: signals?.[item.ticker]?.sentiment_z || 0
          }))}
        />

        {/* 4. Mini Radar Grid */}
        <MiniRadarGrid 
          data={ranking.map(item => ({
            ticker: item.ticker,
            composite: signals?.[item.ticker]?.composite_score || item.composite || 0,
            momentum_z: signals?.[item.ticker]?.momentum_z || 0,
            trend_z: signals?.[item.ticker]?.trend_z || 0,
            vola_z: signals?.[item.ticker]?.vola_z || 0,
            sentiment_z: signals?.[item.ticker]?.sentiment_z || 0,
            dividend_yield_z: signals?.[item.ticker]?.dividend_yield_z || 0
          }))}
        />
      </div>

      {/* VEE Multi-Level Accordions (like single ticker) */}
      <VEEAccordions
        veeExplanations={veeExplanations}
        explainability={explainability}
        numericalPanel={numericalPanel}
      />

    </div>
  )
}
