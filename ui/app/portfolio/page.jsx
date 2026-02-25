"use client"

import { useState, useEffect } from "react"
import { useKeycloak } from "@/contexts/KeycloakContext"
import { 
  TrendingUp, 
  TrendingDown,
  DollarSign, 
  Activity, 
  PieChart,
  Shield,
  AlertTriangle,
  Target,
  BarChart3,
  Calendar,
  Download,
  Mail,
  FileText,
  Settings,
  PlayCircle,
  PauseCircle,
  Clock,
  Zap,
  Eye,
  HelpCircle
} from "lucide-react"
import { GuardianAutopilotAdapter } from './adapters/GuardianAutopilotAdapter'
import { VeeChartTooltip, VeeTooltip } from '@/components/explainability/tooltips/TooltipLibrary'
import { 
  LineChart, 
  Line, 
  BarChart,
  Bar,
  PieChart as RechartsPie,
  Pie,
  Cell,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Treemap
} from "recharts"

/**
 * Portfolio Dashboard - Full Page (Task 24-25 Day 3)
 * 
 * 5 Main Sections:
 * 1. Performance Analytics (multi-timeframe, benchmarks, risk metrics)
 * 2. Composition & Diversification (sectors, geography, weight distribution)
 * 3. Risk Dashboard (VaR, volatility, liquidity, concentration)
 * 4. Guardian & Autopilot (insights timeline + control panel)
 * 5. Advanced Tools (rebalancing, dividends, holdings deep dive, export)
 */

export default function PortfolioPage() {
  const { authenticated, userInfo, token } = useKeycloak()
  const [timeframe, setTimeframe] = useState("1M") // 7D, 1M, 3M, 1Y, ALL
  const [portfolioData, setPortfolioData] = useState(null)
  const [loading, setLoading] = useState(true)
  
  // ✅ REAL USER ID from Keycloak
  const userId = userInfo?.sub || null

  // Fetch real portfolio data from Shadow Trading backend
  useEffect(() => {
    if (!userId || !authenticated) {
      console.log("[Portfolio] User not authenticated, skipping fetch")
      setLoading(false)
      return
    }

    const fetchPortfolio = async () => {
      try {
        setLoading(true)
        const response = await fetch(`http://localhost:8025/portfolio/${userId}`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        })

        if (response.ok) {
          const data = await response.json()
          setPortfolioData(data)
          console.log("[Portfolio] Fetched portfolio data:", data)
        } else {
          console.error("[Portfolio] Failed to fetch:", response.status)
        }
      } catch (error) {
        console.error("[Portfolio] Fetch error:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchPortfolio()
  }, [userId, authenticated, token])
  
  // Portfolio stats - use real data if available, fallback to mock
  const portfolioStats = portfolioData ? {
    totalValue: portfolioData.total_value || 0,
    pnlToday: portfolioData.day_pnl || 0,
    pnlPercent: portfolioData.day_pnl_percent || 0.00,
    riskScore: portfolioData.risk_score || 0,
    sharpeRatio: portfolioData.sharpe_ratio || 0,
    maxDrawdown: portfolioData.max_drawdown || 0,
    totalReturn: portfolioData.total_return || 0,
    volatility: portfolioData.volatility || 0,
    beta: portfolioData.beta || 0,
    var95: portfolioData.var_95 || 0
  } : {
    totalValue: 0,
    pnlToday: 0,
    pnlPercent: 0.00,
    riskScore: 0,
    sharpeRatio: 0,
    maxDrawdown: 0,
    totalReturn: 0,
    volatility: 0,
    beta: 0,
    var95: 0
  }

  // Show loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-vitruvyan-accent mx-auto mb-4"></div>
          <p className="text-gray-600">Loading portfolio...</p>
        </div>
      </div>
    )
  }

  // Show auth required if not logged in
  if (!authenticated) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md bg-white p-8 rounded-lg shadow-lg">
          <Shield className="w-16 h-16 text-vitruvyan-accent mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Authentication Required</h2>
          <p className="text-gray-600 mb-6">Please log in to view your portfolio dashboard.</p>
          <button 
            onClick={() => window.location.href = '/'}
            className="px-6 py-3 bg-vitruvyan-accent text-white rounded-lg hover:bg-opacity-90 transition-all"
          >
            Go to Login
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Portfolio Dashboard</h1>
              <p className="text-sm text-gray-600 mt-1">Real-time analytics and insights</p>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <p className="text-sm text-gray-600">Total Value</p>
                <p className="text-2xl font-bold text-gray-900">
                  ${portfolioStats.totalValue.toLocaleString()}
                </p>
                <p className={`text-sm font-medium ${portfolioStats.pnlPercent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {portfolioStats.pnlPercent >= 0 ? '+' : ''}{portfolioStats.pnlPercent.toFixed(2)}% today
                </p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="space-y-8">
          
          {/* SECTION 1: PERFORMANCE ANALYTICS */}
          <section>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-900">Performance Analytics</h2>
              <div className="flex gap-2">
                {["7D", "1M", "3M", "1Y", "ALL"].map(tf => (
                  <button
                    key={tf}
                    onClick={() => setTimeframe(tf)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      timeframe === tf
                        ? 'bg-gray-900 text-white'
                        : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    {tf}
                  </button>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 mb-6">
              {/* Metric Cards */}
              <MetricCard
                icon={<TrendingUp className="w-5 h-5 text-green-600" />}
                label="Total Return"
                value={`+${portfolioStats.totalReturn}%`}
                subtext="Since inception"
                colorClass="bg-green-50 border-green-200"
              />
              <MetricCard
                icon={<TrendingDown className="w-5 h-5 text-orange-600" />}
                label="Max Drawdown"
                value={`${portfolioStats.maxDrawdown}%`}
                subtext="Worst decline"
                colorClass="bg-orange-50 border-orange-200"
              />
              <MetricCard
                icon={<Activity className="w-5 h-5 text-blue-600" />}
                label="Sharpe Ratio"
                value={portfolioStats.sharpeRatio.toFixed(2)}
                subtext="Risk-adjusted return"
                colorClass="bg-blue-50 border-blue-200"
              />
              <MetricCard
                icon={<BarChart3 className="w-5 h-5 text-purple-600" />}
                label="Volatility"
                value={`${portfolioStats.volatility}%`}
                subtext="Annual std dev"
                colorClass="bg-purple-50 border-purple-200"
              />
            </div>

            {/* Performance Chart */}
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Portfolio vs Benchmarks ({timeframe})
              </h3>
              <ResponsiveContainer width="100%" height={350}>
                <LineChart data={generatePerformanceData(timeframe)}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="date" stroke="#6b7280" />
                  <YAxis stroke="#6b7280" />
                  <Tooltip 
                    content={(props) => (
                      <VeeChartTooltip 
                        {...props} 
                        simple="Portfolio performance vs benchmarks"
                        technical="Green line = your portfolio total value • Blue dashed = S&P 500 ETF (SPY) • Purple dashed = Nasdaq-100 ETF (QQQ) • Compare returns to assess relative performance"
                      />
                    )}
                  />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="portfolio" 
                    stroke="#10b981" 
                    strokeWidth={2}
                    name="Portfolio"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="spy" 
                    stroke="#3b82f6" 
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    name="SPY"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="qqq" 
                    stroke="#8b5cf6" 
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    name="QQQ"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Risk-Return Scatter + Correlation Matrix */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
              {/* Risk-Return Scatter */}
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Risk-Return Profile</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <ScatterChart>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      type="number" 
                      dataKey="risk" 
                      name="Risk" 
                      label={{ value: 'Volatility (%)', position: 'insideBottom', offset: -5 }}
                    />
                    <YAxis 
                      type="number" 
                      dataKey="return" 
                      name="Return"
                      label={{ value: 'Return (%)', angle: -90, position: 'insideLeft' }}
                    />
                    <Tooltip 
                      content={(props) => (
                        <VeeChartTooltip 
                          {...props} 
                          simple="Risk-Return tradeoff"
                          technical="X-axis = Volatility (risk) • Y-axis = Return (reward) • Ideal holdings = high return, low risk (top-left quadrant) • Each point represents one holding"
                        />
                      )}
                      cursor={{ strokeDasharray: '3 3' }} 
                    />
                    <Scatter 
                      name="Holdings" 
                      data={generateRiskReturnData()} 
                      fill="#3b82f6"
                    />
                  </ScatterChart>
                </ResponsiveContainer>
              </div>

              {/* Correlation Matrix (simplified heatmap) */}
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <div className="flex items-center gap-2 mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">Correlation Matrix</h3>
                  <VeeTooltip
                    content={
                      <div className="space-y-2">
                        <p className="text-sm font-bold text-gray-900">Come si muovono insieme i tuoi asset</p>
                        <div className="text-xs text-gray-700 space-y-1">
                          <p><span className="font-semibold text-red-600">+1.00 (rosso)</span>: Si muovono perfettamente insieme (AAPL sale → MSFT sale)</p>
                          <p><span className="font-semibold text-gray-600">0.00 (grigio)</span>: Movimenti indipendenti (vera diversificazione)</p>
                          <p><span className="font-semibold text-blue-600">-1.00 (blu)</span>: Si muovono in direzioni opposte (hedge naturale)</p>
                        </div>
                        <div className="pt-2 border-t border-gray-200">
                          <p className="text-xs font-medium text-gray-900 mb-1">Perché è importante:</p>
                          <p className="text-xs text-gray-700">Se tutti i tuoi asset hanno correlazione alta (&gt;0.7), quando un settore crolla → tutto il portfolio crolla. Obiettivo: correlazioni 0.3-0.5 per ridurre rischio sistemico.</p>
                        </div>
                      </div>
                    }
                  >
                    <HelpCircle className="w-4 h-4 text-gray-400 hover:text-gray-600 cursor-help" />
                  </VeeTooltip>
                </div>
                <div className="grid grid-cols-4 gap-2">
                  {generateCorrelationMatrix().map((row, i) => (
                    row.map((val, j) => (
                      <div 
                        key={`${i}-${j}`}
                        className="aspect-square flex items-center justify-center rounded text-xs font-medium"
                        style={{
                          backgroundColor: getCorrelationColor(val),
                          color: Math.abs(val) > 0.5 ? '#fff' : '#000'
                        }}
                      >
                        {val.toFixed(2)}
                      </div>
                    ))
                  ))}
                </div>
                <div className="mt-4 flex items-center justify-between text-xs text-gray-600">
                  <span>Low correlation</span>
                  <span>High correlation</span>
                </div>
              </div>
            </div>
          </section>

          {/* SECTION 2: COMPOSITION & DIVERSIFICATION */}
          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-6">Composition & Diversification</h2>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Sector Breakdown */}
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Sector Breakdown</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <RechartsPie>
                    <Pie
                      data={generateSectorData()}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={renderCustomLabel}
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {generateSectorData().map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={SECTOR_COLORS[index % SECTOR_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip 
                      content={(props) => (
                        <VeeChartTooltip 
                          {...props} 
                          simple="Sector diversification"
                          technical="Percentage of portfolio value in each sector • Balanced allocation reduces single-sector risk • Aim for 3+ sectors (current: {sectorsCount})"
                        />
                      )}
                    />
                  </RechartsPie>
                </ResponsiveContainer>
                
                {/* Sector Table */}
                <div className="mt-4 space-y-2">
                  {generateSectorData().map((sector, idx) => (
                    <div key={idx} className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <div 
                          className="w-3 h-3 rounded-full" 
                          style={{ backgroundColor: SECTOR_COLORS[idx] }}
                        />
                        <span className="text-gray-900">{sector.name}</span>
                      </div>
                      <span className="font-medium text-gray-900">{sector.value}%</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Geographic Exposure (Treemap placeholder - simplified as bars) */}
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Geographic Exposure</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={generateGeoData()} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" />
                    <YAxis dataKey="region" type="category" width={80} />
                    <Tooltip 
                      content={(props) => (
                        <VeeChartTooltip 
                          {...props} 
                          simple="Geographic exposure"
                          technical="Percentage invested in each geographic region • North America dominant = concentrated risk • Consider international diversification for global hedging"
                        />
                      )}
                    />
                    <Bar dataKey="value" fill="#3b82f6" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Weight Distribution */}
            <div className="bg-white border border-gray-200 rounded-lg p-6 mt-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Top 10 Holdings by Weight</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={generateWeightData()}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="ticker" />
                  <YAxis />
                  <Tooltip 
                    content={(props) => (
                      <VeeChartTooltip 
                        {...props} 
                        simple="Position sizing"
                        technical="Weight = percentage of portfolio value per ticker • Top 3 > 60% = high concentration risk • Balanced portfolios: 5-10% per position (max 20%)"
                      />
                    )}
                  />
                  <Bar dataKey="weight" fill="#8b5cf6" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </section>

          {/* SECTION 3: RISK DASHBOARD */}
          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-6">Risk Dashboard</h2>
            
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 mb-6">
              {/* Risk Metric Cards */}
              <MetricCard
                icon={<AlertTriangle className="w-5 h-5 text-red-600" />}
                label="Value at Risk (95%)"
                value={`$${portfolioStats.var95.toLocaleString()}`}
                subtext="Max 1-day loss"
                colorClass="bg-red-50 border-red-200"
              />
              <MetricCard
                icon={<Activity className="w-5 h-5 text-orange-600" />}
                label="Beta vs SPY"
                value={portfolioStats.beta.toFixed(2)}
                subtext="Market sensitivity"
                colorClass="bg-orange-50 border-orange-200"
              />
              <MetricCard
                icon={<Shield className="w-5 h-5 text-green-600" />}
                label="Liquidity Score"
                value="8/10"
                subtext="High liquidity"
                colorClass="bg-green-50 border-green-200"
              />
              <MetricCard
                icon={<Target className="w-5 h-5 text-blue-600" />}
                label="Concentration Risk"
                value="Medium"
                subtext="Top 3: 62.1%"
                colorClass="bg-blue-50 border-blue-200"
              />
            </div>

            {/* Volatility Breakdown (Radar Chart) */}
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Multi-Dimensional Risk Profile</h3>
              <ResponsiveContainer width="100%" height={350}>
                <RadarChart data={generateRiskRadarData()}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="dimension" />
                  <PolarRadiusAxis angle={90} domain={[0, 10]} />
                  <Radar 
                    name="Portfolio" 
                    dataKey="value" 
                    stroke="#3b82f6" 
                    fill="#3b82f6" 
                    fillOpacity={0.6} 
                  />
                  <Tooltip 
                    content={(props) => (
                      <VeeChartTooltip 
                        {...props} 
                        simple="Multi-dimensional risk"
                        technical="6 risk factors (0-10 scale) • Market Risk = beta vs SPY • Volatility = price fluctuation • Liquidity = ease of selling • Concentration = top holdings weight • Correlation = co-movement • Drawdown = max decline"
                      />
                    )}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </section>

          {/* SECTION 4: GUARDIAN & AUTOPILOT - ✅ MODULARIZED (Task 26.3) */}
          <GuardianAutopilotAdapter userId={userId} />

          {/* SECTION 5: ADVANCED TOOLS */}
          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-6">Advanced Tools</h2>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Rebalancing Simulator */}
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  <Target className="w-5 h-5 inline-block mr-2 text-blue-600" />
                  Rebalancing Simulator
                </h3>
                <p className="text-sm text-gray-600 mb-4">
                  Simulate portfolio rebalancing to target allocations
                </p>
                <button className="w-full bg-gray-900 hover:bg-black text-white font-medium py-3 rounded-lg transition-colors">
                  Run Simulator
                </button>
              </div>

              {/* Dividends Calendar */}
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  <Calendar className="w-5 h-5 inline-block mr-2 text-green-600" />
                  Dividends Calendar
                </h3>
                <p className="text-sm text-gray-600 mb-4">
                  Upcoming dividend payments and history
                </p>
                <button className="w-full bg-gray-900 hover:bg-black text-white font-medium py-3 rounded-lg transition-colors">
                  View Calendar
                </button>
              </div>

              {/* Holdings Deep Dive */}
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  <Eye className="w-5 h-5 inline-block mr-2 text-purple-600" />
                  Holdings Deep Dive
                </h3>
                <p className="text-sm text-gray-600 mb-4">
                  Detailed analysis of individual positions
                </p>
                <button className="w-full bg-gray-900 hover:bg-black text-white font-medium py-3 rounded-lg transition-colors">
                  Analyze Holdings
                </button>
              </div>

              {/* Export Tools */}
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  <Download className="w-5 h-5 inline-block mr-2 text-indigo-600" />
                  Export Tools
                </h3>
                <p className="text-sm text-gray-600 mb-4">
                  Export portfolio data and reports
                </p>
                <div className="flex gap-2">
                  <button className="flex-1 bg-gray-900 hover:bg-black text-white font-medium py-3 rounded-lg transition-colors flex items-center justify-center gap-2">
                    <FileText className="w-4 h-4" />
                    PDF
                  </button>
                  <button className="flex-1 bg-gray-900 hover:bg-black text-white font-medium py-3 rounded-lg transition-colors flex items-center justify-center gap-2">
                    <FileText className="w-4 h-4" />
                    CSV
                  </button>
                  <button className="flex-1 bg-gray-900 hover:bg-black text-white font-medium py-3 rounded-lg transition-colors flex items-center justify-center gap-2">
                    <Mail className="w-4 h-4" />
                    Email
                  </button>
                </div>
              </div>
            </div>
          </section>

        </div>
      </main>
    </div>
  )
}

/* MetricCard Component */
function MetricCard({ icon, label, value, subtext, colorClass }) {
  return (
    <div className={`${colorClass} border rounded-lg p-4`}>
      <div className="flex items-center gap-3 mb-2">
        {icon}
        <span className="text-sm font-medium text-gray-700">{label}</span>
      </div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-600 mt-1">{subtext}</p>
    </div>
  )
}

/* Data Generators (Mock data - replace with real API) */

function generatePerformanceData(timeframe) {
  const points = timeframe === "7D" ? 7 : timeframe === "1M" ? 30 : timeframe === "3M" ? 90 : timeframe === "1Y" ? 365 : 365
  const data = []
  let portfolioValue = 38000
  let spyValue = 38000
  let qqqValue = 38000
  
  for (let i = 0; i < points; i++) {
    portfolioValue += (Math.random() - 0.48) * 500
    spyValue += (Math.random() - 0.49) * 300
    qqqValue += (Math.random() - 0.48) * 400
    
    data.push({
      date: timeframe === "7D" ? `Day ${i+1}` : `${i+1}`,
      portfolio: Math.round(portfolioValue),
      spy: Math.round(spyValue),
      qqq: Math.round(qqqValue)
    })
  }
  
  return data
}

function generateRiskReturnData() {
  return [
    { ticker: "AAPL", risk: 18, return: 12 },
    { ticker: "MSFT", risk: 15, return: 10 },
    { ticker: "TSLA", risk: 35, return: 25 },
    { ticker: "NVDA", risk: 28, return: 22 },
    { ticker: "GOOGL", risk: 16, return: 11 }
  ]
}

function generateCorrelationMatrix() {
  return [
    [1.00, 0.65, 0.42, 0.71],
    [0.65, 1.00, 0.38, 0.59],
    [0.42, 0.38, 1.00, 0.55],
    [0.71, 0.59, 0.55, 1.00]
  ]
}

function getCorrelationColor(val) {
  const intensity = Math.abs(val)
  if (intensity > 0.8) return val > 0 ? '#dc2626' : '#2563eb'
  if (intensity > 0.6) return val > 0 ? '#f97316' : '#3b82f6'
  if (intensity > 0.4) return val > 0 ? '#fbbf24' : '#60a5fa'
  return '#e5e7eb'
}

const SECTOR_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316']

function generateSectorData() {
  return [
    { name: "Technology", value: 43.4 },
    { name: "Consumer", value: 38.6 },
    { name: "Industrials", value: 18.1 }
  ]
}

function renderCustomLabel({ cx, cy, midAngle, innerRadius, outerRadius, percent }) {
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5
  const x = cx + radius * Math.cos(-midAngle * Math.PI / 180)
  const y = cy + radius * Math.sin(-midAngle * Math.PI / 180)

  return (
    <text x={x} y={y} fill="white" textAnchor={x > cx ? 'start' : 'end'} dominantBaseline="central" fontSize={12} fontWeight="bold">
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  )
}

function generateGeoData() {
  return [
    { region: "North America", value: 85 },
    { region: "Europe", value: 10 },
    { region: "Asia", value: 5 }
  ]
}

function generateWeightData() {
  return [
    { ticker: "AAPL", weight: 43.4 },
    { ticker: "MSFT", weight: 38.6 },
    { ticker: "TSLA", weight: 18.1 }
  ]
}

function generateRiskRadarData() {
  return [
    { dimension: "Market Risk", value: 6 },
    { dimension: "Volatility", value: 5 },
    { dimension: "Liquidity", value: 8 },
    { dimension: "Concentration", value: 7 },
    { dimension: "Correlation", value: 6 },
    { dimension: "Drawdown", value: 4 }
  ]
}

// ❌ REMOVED: generateGuardianInsights() and generateAutopilotActions() 
// ✅ Replaced by GuardianAutopilotAdapter with real WebSocket data (Task 26.3)
