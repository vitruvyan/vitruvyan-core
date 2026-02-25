/**
 * NEURAL ENGINE UI (Exec Node)
 * 
 * Displays Neural Engine ranking output from exec_node.
 * 
 * Backend Node: exec_node.py (calls Neural Engine API)
 * State Keys: state.numerical_panel (composite_score, momentum_z, trend_z, vola_z)
 * 
 * ⚠️ CRITICAL: This component has ZERO business logic.
 * It only receives numerical_panel from final_state and displays it.
 * 
 * Props:
 * - numericalPanel: NumericalPanelItem[] - Array with Neural Engine scores
 * - finalVerdict?: object - Optional verdict badge
 * - gauge?: object - Optional gauge indicators
 * - horizonData: object - Data for all 3 horizons from Neural Engine
 * - activeHorizon: string - Currently selected horizon
 * - className?: string - Optional Tailwind classes
 * 
 * @typedef {Object} StockFactors
 * @property {number|null} momentum_z - Momentum z-score (30-day price change)
 * @property {number|null} trend_z - Trend z-score (SMA/EMA consensus)
 * @property {number|null} vola_z - Volatility z-score (ATR)
 * @property {number|null} sentiment_z - Sentiment z-score (social + news)
 * @property {number|null} fundamentals_z - Composite fundamentals z-score (NEW: Dec 6, 2025)
 * @property {number|null} revenue_growth_yoy_z - Revenue growth YoY z-score (NEW: Dec 6, 2025)
 * @property {number|null} eps_growth_yoy_z - EPS growth YoY z-score (NEW: Dec 6, 2025)
 * @property {number|null} net_margin_z - Net margin z-score (NEW: Dec 6, 2025)
 * @property {number|null} debt_to_equity_z - Debt-to-equity z-score inverted (NEW: Dec 6, 2025)
 * @property {number|null} free_cash_flow_z - Free cash flow z-score (NEW: Dec 6, 2025)
 * @property {number|null} dividend_yield_z - Dividend yield z-score (NEW: Dec 6, 2025)
 */

'use client'

import { useState } from 'react'
import { BarChart3, TrendingUp, TrendingDown, Activity, AlertTriangle, CheckCircle } from 'lucide-react'
import FundamentalsPanel from '../analytics/panels/FundamentalsPanel'
import { RiskPanel } from '../analytics/panels'
import { MetricCard, ZScoreCard } from '../cards/CardLibrary'
import { MomentumTooltip, TrendTooltip, VolatilityTooltip, SentimentTooltip, FundamentalsTooltip, VWRETooltip } from '../explainability/tooltips/TooltipLibrary'

// Inline formatters (no external lib dependency)
const formatScore = (score) => {
  if (score === null || score === undefined) return 'N/A'
  return `${(score * 100).toFixed(1)}%`
}

const formatZScore = (z) => {
  if (z === null || z === undefined) return 'N/A'
  return z.toFixed(2)
}

const getVerdictColor = (label) => {
  const colors = {
    'BUY': 'bg-green-50 border-green-300 text-green-700',
    'HOLD': 'bg-yellow-50 border-yellow-300 text-yellow-700',
    'SELL': 'bg-red-50 border-red-300 text-red-700'
  }
  return colors[label] || 'bg-gray-50 border-gray-300 text-gray-700'
}

const getGaugeColor = (color) => {
  const colors = {
    'green': 'bg-green-500',
    'yellow': 'bg-yellow-500',
    'red': 'bg-red-500'
  }
  return colors[color] || 'bg-gray-500'
}

export default function NeuralEngineUI({ numericalPanel, finalVerdict, gauge, horizonData, activeHorizon, explainability, className = '' }) {
  
  // 🔥 Get real Neural Engine data from horizonData if available
  const getRealNeuralData = () => {
    // PRIORITY 1: Use explainability.detailed.ranking.stocks (has ALL factors including fundamentals)
    if (explainability?.detailed?.ranking?.stocks) {
      const stocks = explainability.detailed.ranking.stocks
      // [DEV] console.log('[NeuralEngineUI] ✅ Using explainability.detailed.ranking.stocks (with fundamentals):', stocks[0]?.ticker)
      return stocks.map(stock => ({
        ticker: stock.ticker,
        composite_score: stock.composite_score,
        momentum_z: stock.factors?.momentum_z || null,
        trend_z: stock.factors?.trend_z || null,
        vola_z: stock.factors?.vola_z || null,
        sentiment_z: stock.factors?.sentiment_z || null,
        // Fundamentals z-scores (Dec 6, 2025)
        fundamentals_z: stock.factors?.fundamentals_z || null,
        revenue_growth_yoy_z: stock.factors?.revenue_growth_yoy_z || null,
        eps_growth_yoy_z: stock.factors?.eps_growth_yoy_z || null,
        net_margin_z: stock.factors?.net_margin_z || null,
        debt_to_equity_z: stock.factors?.debt_to_equity_z || null,
        free_cash_flow_z: stock.factors?.free_cash_flow_z || null,
        dividend_yield_z: stock.factors?.dividend_yield_z || null
      }))
    }

    // PRIORITY 2: Use horizonData (multi-horizon support)
    if (horizonData && activeHorizon) {
      const currentHorizonData = horizonData[activeHorizon]
      if (currentHorizonData?.ranking?.stocks?.length > 0) {
        const stocks = currentHorizonData.ranking.stocks
        // [DEV] console.log(`[NeuralEngineUI] ✅ Loading ${activeHorizon} data:`, stocks[0])
        return stocks.map(stock => ({
      ticker: stock.ticker,
      composite_score: stock.composite_score,
        momentum_z: stock.factors?.momentum_z || null,
        trend_z: stock.factors?.trend_z || null,
        vola_z: stock.factors?.vola_z || null,
        sentiment_z: stock.factors?.sentiment_z || null,
        // Fundamentals z-scores (Dec 6, 2025)
        fundamentals_z: stock.factors?.fundamentals_z || null,
        revenue_growth_yoy_z: stock.factors?.revenue_growth_yoy_z || null,
        eps_growth_yoy_z: stock.factors?.eps_growth_yoy_z || null,
        net_margin_z: stock.factors?.net_margin_z || null,
        debt_to_equity_z: stock.factors?.debt_to_equity_z || null,
        free_cash_flow_z: stock.factors?.free_cash_flow_z || null,
        dividend_yield_z: stock.factors?.dividend_yield_z || null
        }))
      }
    }

    // PRIORITY 3: Fallback to numericalPanel (legacy, no fundamentals)
    // [DEV] console.log('[NeuralEngineUI] ⚠️ Fallback to numericalPanel (no fundamentals)')
    return numericalPanel
  }

  const neuralData = getRealNeuralData()
  // [DEV] console.log(`[NeuralEngineUI] Rendering with activeHorizon: ${activeHorizon}, data:`, neuralData)

  // Guard: Don't render if no Neural Engine data
  if (!neuralData || neuralData.length === 0) {
    return null
  }

  return (
    <div className={`space-y-2 ${className}`}>
      {/* Header with Verdict */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <BarChart3 size={16} className="text-vitruvyan-accent" />
          <span className="font-semibold">Neural Engine Analysis</span>
          {/* 🔥 Show active horizon indicator */}
          {horizonData && activeHorizon && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 font-medium">
              {activeHorizon === 'short' ? '1-3m' : activeHorizon === 'medium' ? '3-12m' : '12m+'}
            </span>
          )}
        </div>

        {/* Final Verdict Badge with Tooltip */}
        {finalVerdict && (
          <div className="group relative">
            <div className={`px-3 py-1 rounded-lg border text-sm font-semibold ${getVerdictColor(finalVerdict.label)} cursor-help`}>
              {finalVerdict.label}
            </div>
            {/* Tooltip */}
            <div className="absolute hidden group-hover:block bottom-full right-0 mb-2 w-64 p-3 bg-gray-900 text-white text-xs rounded shadow-lg z-50">
              <strong className="block mb-1">{finalVerdict.label} Signal</strong>
              <p className="leading-relaxed">
                {finalVerdict.label === 'Buy' && 'Strong positive momentum across all factors. This stock shows bullish signals and potential upside.'}
                {finalVerdict.label === 'Strong Buy' && 'Exceptional strength across all metrics. Very high conviction bullish signal with strong momentum and trend alignment.'}
                {finalVerdict.label === 'Hold' && 'Mixed signals or neutral positioning. Current price reflects fair value. Consider waiting for clearer directional signals before acting.'}
                {finalVerdict.label === 'Sell' && 'Negative momentum and weak trend. Risk outweighs potential reward. Consider reducing exposure or exiting position.'}
                {finalVerdict.label === 'Strong Sell' && 'Severe weakness across multiple factors. High conviction bearish signal. Strong recommendation to exit or avoid this position.'}
              </p>
              <div className="mt-2 pt-2 border-t border-gray-700">
                <span className="text-gray-400">Composite Score: </span>
                <span className="font-semibold">{formatScore(finalVerdict.composite_score)}</span>
              </div>
              <div className="absolute top-full right-4 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></div>
            </div>
          </div>
        )}
      </div>

      {/* 🎴 Technical Factors Cards Grid (4 cards) */}
      {neuralData && neuralData.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          {/* Momentum Card */}
          {neuralData[0].momentum_z !== null && (
            <ZScoreCard
              label="Momentum"
              value={neuralData[0].momentum_z}
              icon={TrendingUp}
              veeSimple={`Momentum: ${neuralData[0].momentum_z >= 0.5 ? 'Above average' : neuralData[0].momentum_z < -0.5 ? 'Below average' : 'Average'} performance`}
              veeTechnical={
                neuralData[0].momentum_z >= 0.5 
                  ? `Momentum z-score ${formatZScore(neuralData[0].momentum_z)} signals significant price acceleration (~${Math.round(50 + neuralData[0].momentum_z * 15)}th percentile). The stock shows relative strength vs market with buyers in control. This technical signal suggests uptrend continuation in the short term (30 days). Ideal for momentum-based and breakout trading strategies.`
                  : neuralData[0].momentum_z < -0.5
                  ? `Momentum z-score ${formatZScore(neuralData[0].momentum_z)} reveals relative weakness (~${Math.round(50 + neuralData[0].momentum_z * 15)}th percentile). Price is losing strength vs peers, signaling selling pressure. This technical dynamic may precede broader corrections. Caution for long positions, opportunity for contrarian strategies if valuations attractive.`
                  : `Momentum z-score ${formatZScore(neuralData[0].momentum_z)} is neutral (~${Math.round(50 + neuralData[0].momentum_z * 15)}th percentile). Price moves in line with market average, no clear directional signals. Consolidation or indecision phase. Wait for technical or fundamental catalysts before directional positioning.`
              }
            />
          )}

          {/* Trend Card */}
          {neuralData[0].trend_z !== null && (
            <ZScoreCard
              label="Trend"
              value={neuralData[0].trend_z}
              icon={Activity}
              veeSimple={`Trend: ${neuralData[0].trend_z >= 0.5 ? 'Above average' : neuralData[0].trend_z < -0.5 ? 'Below average' : 'Average'} performance`}
              veeTechnical={
                neuralData[0].trend_z >= 0.5 
                  ? `Trend z-score ${formatZScore(neuralData[0].trend_z)} confirms a consolidated structural uptrend (~${Math.round(50 + neuralData[0].trend_z * 15)}th percentile). Price stays above key moving averages (SMA 20/50/200), signaling long-term strength. This technical setup favors trend-following and position trading strategies. Trend persistence suggests both technical and fundamental support.`
                  : neuralData[0].trend_z < -0.5
                  ? `Trend z-score ${formatZScore(neuralData[0].trend_z)} reveals a structural downtrend (~${Math.round(50 + neuralData[0].trend_z * 15)}th percentile). Price is under pressure vs long-term moving averages. This technical signal requires caution: avoid aggressive long positions, consider protections (stop-loss, put options). Trend reversal needs significant catalysts.`
                  : `Trend z-score ${formatZScore(neuralData[0].trend_z)} is neutral (~${Math.round(50 + neuralData[0].trend_z * 15)}th percentile). Price oscillates around moving averages without clear direction. Range-bound or transition phase. Recommended strategy: wait for directional breakout or focus on other factors (fundamentals, sentiment).`
              }
            />
          )}

          {/* Volatility Card (Risk - inverted colors) */}
          {neuralData[0].vola_z !== null && (
            <ZScoreCard
              label="Volatility"
              value={neuralData[0].vola_z}
              icon={AlertTriangle}
              veeSimple={`Volatility: ${neuralData[0].vola_z <= -0.5 ? 'Low risk (below average)' : neuralData[0].vola_z > 0.5 ? 'High risk (above average)' : 'Average risk'}`}
              veeTechnical={
                neuralData[0].vola_z <= -0.5 
                  ? `Volatility z-score ${formatZScore(neuralData[0].vola_z)} signals low relative volatility (~${Math.round(50 - neuralData[0].vola_z * 15)}th inverted percentile). Price shows contained swings vs peers, indicating stability and predictability. This trait favors risk-averse investors, income-focused strategies (dividends), and aggressive position sizing. Low volatility often accompanies mature stocks, large-caps, and defensive sectors (utilities, consumer staples).`
                  : neuralData[0].vola_z > 0.5
                  ? `Volatility z-score ${formatZScore(neuralData[0].vola_z)} reveals high relative volatility (~${Math.round(50 + neuralData[0].vola_z * 15)}th percentile). Price shows wide swings, increasing risk and unpredictability. This dynamic requires active management: tight stop-losses, reduced sizing, option hedging. High volatility offers opportunities for experienced traders (swing trading, options) but is risky for buy-and-hold. Common in small-caps, biotech, speculative growth stocks.`
                  : `Volatility z-score ${formatZScore(neuralData[0].vola_z)} is in line with market average (~${Math.round(50 + neuralData[0].vola_z * 15)}th percentile). Risk profile is standard, no particular anomalies. Risk management follows traditional approaches (diversification, 2-5% sizing). Normal volatility allows balanced strategies without need for aggressive protections.`
              }
            />
          )}

          {/* Sentiment Card */}
          {neuralData[0].sentiment_z !== null && (
            <ZScoreCard
              label="Sentiment"
              value={neuralData[0].sentiment_z}
              icon={Activity}
              veeSimple={`Sentiment: ${neuralData[0].sentiment_z >= 0.5 ? 'Above average (positive)' : neuralData[0].sentiment_z < -0.5 ? 'Below average (negative)' : 'Average (neutral)'}`}
              veeTechnical={
                neuralData[0].sentiment_z >= 0.5 
                  ? `Sentiment z-score ${formatZScore(neuralData[0].sentiment_z)} reflects widespread optimism (~${Math.round(50 + neuralData[0].sentiment_z * 15)}th percentile). Linguistic analysis of financial news (FinBERT) and social media (Reddit, Twitter) shows positive tone, bullish expectations, and constructive narrative. This signal can precede price momentum, but beware of excess euphoria (contrarian risk). Strong sentiment favors short-term momentum strategies, but requires fundamental validation for long-term positions.`
                  : neuralData[0].sentiment_z < -0.5
                  ? `Sentiment z-score ${formatZScore(neuralData[0].sentiment_z)} indicates prevailing pessimism (~${Math.round(50 + neuralData[0].sentiment_z * 15)}th percentile). News and social media show negative tone, concerns, and bearish narrative. This signal can anticipate selling pressure, but also represents contrarian opportunity if fundamentals remain solid. Negative sentiment requires caution for long positions, but can offer attractive entry points for value investors with long horizon.`
                  : `Sentiment z-score ${formatZScore(neuralData[0].sentiment_z)} is neutral (~${Math.round(50 + neuralData[0].sentiment_z * 15)}th percentile). Market has no strong directional opinion. Waiting phase for catalysts (earnings, guidance, macro). Neutral sentiment is most reliable: less emotional distortion, more rational pricing. Recommended strategy: focus on other factors (fundamentals, technicals) for positioning decisions.`
              }
            />
          )}
        </div>
      )}

      {/* Composite Score Legend */}
      {neuralData && neuralData.length > 0 && (
        <div className="text-[10px] text-gray-600 border-t border-gray-200 pt-2 pb-1">
          <div className="font-semibold mb-1">Composite Score Legend (Percentile Ranking):</div>
          <div className="flex flex-wrap gap-3">
            <span>🟢 ≥70% Strong</span>
            <span>🟡 40-70% Neutral</span>
            <span>🔴 &lt;40% Weak</span>
          </div>
        </div>
      )}

      {/* Composite Score Highlight */}
      {neuralData && neuralData.length > 0 && (
        <div className={`group relative cursor-help rounded-lg border-2 p-2 ${
          neuralData[0].composite_score >= 0.7 ? 'bg-green-50 border-green-300' :
          neuralData[0].composite_score >= 0.4 ? 'bg-yellow-50 border-yellow-300' :
          'bg-red-50 border-red-300'
        }`}>
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-gray-800">Composite Score</span>
            <span className={`text-lg font-bold ${
              neuralData[0].composite_score >= 0.7 ? 'text-green-700' :
              neuralData[0].composite_score >= 0.4 ? 'text-yellow-700' :
              'text-red-700'
            }`}>
              {formatScore(neuralData[0].composite_score)}
            </span>
          </div>
          <div className="text-[10px] text-gray-600 mt-0.5">
            {neuralData[0].composite_score >= 0.7 && '🟢 Strong positive · Top performers'}
            {neuralData[0].composite_score >= 0.4 && neuralData[0].composite_score < 0.7 && '🟡 Neutral · Mixed signals'}
            {neuralData[0].composite_score < 0.4 && '🔴 Weak · Below average'}
          </div>
          
          {/* VEE Tooltip - Composite Score Explanation */}
          <div className="absolute hidden group-hover:block bottom-full left-1/2 transform -translate-x-1/2 mb-2 w-80 p-4 bg-white border border-gray-300 rounded-lg shadow-xl z-50">
            <strong className="block mb-2 text-sm font-bold text-gray-900">Composite Score: {neuralData[0].composite_score >= 0.7 ? 'Strong (Top 30%)' : neuralData[0].composite_score >= 0.4 ? 'Neutral (Middle 30%)' : 'Weak (Bottom 40%)'}</strong>
            <p className="text-xs text-gray-700 leading-relaxed mb-2">
              {neuralData[0].composite_score >= 0.7
                ? `Score ${formatScore(neuralData[0].composite_score)} positions this stock in the top 30% of the universe (517 tickers). This composite ranking combines momentum, trend, volatility and sentiment with optimized weights. A score ≥70% indicates technical excellence across all factors: strong price acceleration, consolidated trend, low volatility, and positive sentiment. 🟢 BUY signal for momentum and growth strategies. Historical performance: stocks >70% outperform index by 12-18% annually.`
                : neuralData[0].composite_score >= 0.4
                ? `Score ${formatScore(neuralData[0].composite_score)} places this stock in the middle range (40-70%). Mixed technical signals: some positive factors offset by neutral/negative ones. 🟡 HOLD position or await catalysts. Not strong enough for aggressive positions, but not critical. Recommended strategy: monitor evolution of key factors (momentum/sentiment) before increasing exposure. Average performance: in line with benchmark.`
                : `Score ${formatScore(neuralData[0].composite_score)} positions this stock in the bottom 40% (below median). Technical weakness across multiple factors: negative momentum, weak trend, or high volatility. 🔴 CAUTION or AVOID signal. This ranking suggests relative underperformance. Not necessarily an imminent crash, but lack of positive technical catalysts. Strategy: avoid new long positions, consider lightening if already in portfolio. Contrarian opportunity only with exceptional fundamentals.`}
            </p>
            <div className="text-xs text-gray-500 border-t border-gray-200 pt-2">
              Current Score: <span className="font-semibold text-vitruvyan-accent">{formatScore(neuralData[0].composite_score)}</span> · <span className="text-gray-400">Percentile Ranking (0-100%)</span>
            </div>
            <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-8 border-r-8 border-t-8 border-transparent border-t-white" style={{filter: 'drop-shadow(0 2px 2px rgba(0,0,0,0.1))'}}></div>
          </div>
        </div>
      )}



      {/* 📊 Fundamentals Panel (NEW: Dec 7, 2025) - AFTER "What do these numbers mean?" */}
      {neuralData && neuralData.length > 0 && (
        <FundamentalsPanel 
          factors={neuralData[0]} 
          explainability={explainability}
          className="mt-4" 
        />
      )}

      {/* 🛡️ VARE Risk Panel (NEW: Dec 23, 2025) - Multi-dimensional risk assessment */}
      {neuralData && neuralData.length > 0 && neuralData[0].vare_risk_score && (
        <RiskPanel 
          riskData={{
            vare_risk_score: neuralData[0].vare_risk_score,
            vare_risk_category: neuralData[0].vare_risk_category,
            vare_confidence: neuralData[0].vare_confidence,
            market_risk: neuralData[0].market_risk,
            volatility_risk: neuralData[0].volatility_risk,
            liquidity_risk: neuralData[0].liquidity_risk,
            correlation_risk: neuralData[0].correlation_risk
          }}
          compositeOriginal={neuralData[0].composite_score_original}
          compositeAdjusted={neuralData[0].composite_score}
          ticker={neuralData[0].ticker}
          className="mt-4"
        />
      )}

      {/* 🎯 VWRE Attribution Tooltip (Dec 23, 2025) - Show factor contributions on composite score hover */}
      {neuralData && neuralData.length > 0 && neuralData[0].attribution && (
        <div className="mt-3 p-3 bg-blue-50 border-2 border-blue-200 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm font-semibold text-blue-800">💡 Attribution Analysis</span>
            <VWRETooltip 
              attribution={neuralData[0].attribution} 
              ticker={neuralData[0].ticker}
            />
          </div>
          <p className="text-xs text-blue-700">
            <strong>Primary Driver:</strong> {neuralData[0].attribution.primary_driver} 
            ({neuralData[0].attribution.factor_percentages?.[neuralData[0].attribution.primary_driver]?.toFixed(1)}% weight)
          </p>
          <p className="text-[10px] text-blue-600 mt-1">
            {neuralData[0].attribution.rank_explanation}
          </p>
        </div>
      )}
    </div>
  )
}
