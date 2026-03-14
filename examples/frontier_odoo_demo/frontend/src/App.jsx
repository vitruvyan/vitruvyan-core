import React, { useState, useEffect, useCallback } from 'react'
import {
  Database, Users, FileText, ShoppingCart, TrendingUp,
  UserCheck, Package, Activity, Zap, BarChart3, Eye, RefreshCw,
  ArrowRight, CircleDot, Layers, Brain, Shield
} from 'lucide-react'
import DataPanel from './components/DataPanel'
import PipelinePanel from './components/PipelinePanel'
import InsightsPanel from './components/InsightsPanel'

const API = '/api'

const CATEGORIES = [
  { key: 'customers',  label: 'Clienti',         icon: Users,        color: '#4c6ef5', endpoint: '/partners?type=customer' },
  { key: 'suppliers',  label: 'Fornitori',        icon: Package,      color: '#f59f00', endpoint: '/partners?type=supplier' },
  { key: 'invoices',   label: 'Fatture',          icon: FileText,     color: '#40c057', endpoint: '/invoices' },
  { key: 'orders',     label: 'Ordini Vendita',   icon: ShoppingCart,  color: '#e64980', endpoint: '/orders/sale' },
  { key: 'crm',        label: 'CRM Pipeline',     icon: TrendingUp,   color: '#7950f2', endpoint: '/crm' },
  { key: 'employees',  label: 'Dipendenti',       icon: UserCheck,    color: '#15aabf', endpoint: '/employees' },
  { key: 'products',   label: 'Prodotti',         icon: BarChart3,    color: '#ff6b6b', endpoint: '/products' },
]

export default function App() {
  const [overview, setOverview] = useState(null)
  const [health, setHealth] = useState(null)
  const [activeCategory, setActiveCategory] = useState(null)
  const [categoryData, setCategoryData] = useState(null)
  const [analysis, setAnalysis] = useState(null)
  const [loading, setLoading] = useState(false)
  const [pipelineStage, setPipelineStage] = useState(null)
  const [error, setError] = useState(null)

  // Boot: fetch overview + health
  useEffect(() => {
    Promise.all([
      fetch(`${API}/overview`).then(r => r.json()),
      fetch(`${API}/health`).then(r => r.json()),
    ]).then(([ov, hl]) => {
      setOverview(ov)
      setHealth(hl)
    }).catch(e => setError(`Backend non raggiungibile: ${e.message}`))
  }, [])

  // Fetch category data
  const selectCategory = useCallback(async (cat) => {
    setActiveCategory(cat.key)
    setCategoryData(null)
    setAnalysis(null)
    setLoading(true)
    setError(null)

    // Pipeline animation: ingestion -> analysis -> insight
    setPipelineStage('ingestion')
    try {
      const res = await fetch(`${API}${cat.endpoint}`)
      const data = await res.json()
      setCategoryData({ key: cat.key, label: cat.label, records: data, color: cat.color })

      setPipelineStage('analysis')
      // Fetch analysis if available
      const analysisMap = {
        invoices: '/analysis/invoices',
        crm: '/analysis/crm',
        customers: '/analysis/customers',
      }
      if (analysisMap[cat.key]) {
        const aRes = await fetch(`${API}${analysisMap[cat.key]}`)
        const aData = await aRes.json()
        setAnalysis({ key: cat.key, data: aData })
      } else {
        setAnalysis(null)
      }

      setPipelineStage('insight')
      setTimeout(() => setPipelineStage('complete'), 800)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  const refresh = useCallback(() => {
    fetch(`${API}/overview`).then(r => r.json()).then(setOverview)
    if (activeCategory) {
      const cat = CATEGORIES.find(c => c.key === activeCategory)
      if (cat) selectCategory(cat)
    }
  }, [activeCategory, selectCategory])

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b border-white/5 bg-gray-950/80 backdrop-blur-lg sticky top-0 z-50">
        <div className="max-w-[1600px] mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center"
                 style={{ background: 'var(--gradient-brand)' }}>
              <Eye className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight">
                Vitruvyan <span className="text-brand-400">Frontier</span>
              </h1>
              <p className="text-xs text-gray-500">Enterprise Connector — Odoo ERP Demo</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            {health && (
              <div className="flex items-center gap-2 text-xs text-gray-400">
                <span className="w-2 h-2 rounded-full bg-green-400 pulse-dot" />
                Odoo {health.odoo?.server_version} • {health.odoo?.database}
              </div>
            )}
            <button
              onClick={refresh}
              className="p-2 rounded-lg hover:bg-white/5 transition-colors text-gray-400 hover:text-white"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      {/* Error banner */}
      {error && (
        <div className="bg-red-500/10 border-b border-red-500/20 px-6 py-3 text-sm text-red-400 text-center">
          {error}
        </div>
      )}

      {/* Overview stats */}
      {overview && (
        <div className="max-w-[1600px] mx-auto px-6 py-6">
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
            {[
              { label: 'Partners', value: overview.partners, icon: Users },
              { label: 'Prodotti', value: overview.products, icon: Package },
              { label: 'Vendite', value: overview.sale_orders, icon: ShoppingCart },
              { label: 'Acquisti', value: overview.purchase_orders, icon: ShoppingCart },
              { label: 'Fatture', value: overview.invoices, icon: FileText },
              { label: 'CRM', value: overview.crm_leads, icon: TrendingUp },
              { label: 'Dipendenti', value: overview.employees, icon: UserCheck },
              { label: 'Task', value: overview.tasks, icon: Activity },
            ].map(s => (
              <div key={s.label} className="glass-card stat-glow p-4 text-center">
                <s.icon className="w-4 h-4 mx-auto mb-2 text-gray-500" />
                <div className="text-2xl font-bold text-white">{s.value}</div>
                <div className="text-[11px] text-gray-500 mt-1">{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 3-column layout */}
      <main className="flex-1 max-w-[1600px] mx-auto px-6 pb-8 w-full">
        <div className="grid grid-cols-12 gap-6 h-full">

          {/* Left: Data source categories */}
          <div className="col-span-12 lg:col-span-3">
            <div className="glass-card p-4">
              <div className="flex items-center gap-2 mb-4">
                <Database className="w-4 h-4 text-brand-400" />
                <h2 className="text-sm font-semibold">Sorgenti Dati ERP</h2>
              </div>
              <div className="space-y-2">
                {CATEGORIES.map(cat => {
                  const Icon = cat.icon
                  const isActive = activeCategory === cat.key
                  const count = overview ? {
                    customers: overview.partners,
                    suppliers: overview.partners,
                    invoices: overview.invoices,
                    orders: overview.sale_orders,
                    crm: overview.crm_leads,
                    employees: overview.employees,
                    products: overview.products,
                  }[cat.key] : null
                  return (
                    <button
                      key={cat.key}
                      onClick={() => selectCategory(cat)}
                      className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left transition-all duration-200 ${
                        isActive
                          ? 'bg-white/10 border border-white/15 shadow-lg'
                          : 'hover:bg-white/5 border border-transparent'
                      }`}
                    >
                      <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
                           style={{ backgroundColor: `${cat.color}20` }}>
                        <Icon className="w-4 h-4" style={{ color: cat.color }} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium">{cat.label}</div>
                        {count != null && (
                          <div className="text-[11px] text-gray-500">{count} record</div>
                        )}
                      </div>
                      {isActive && (
                        <ArrowRight className="w-4 h-4 text-gray-400 flex-shrink-0" />
                      )}
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Sacred Orders info */}
            <div className="glass-card p-4 mt-4">
              <div className="flex items-center gap-2 mb-3">
                <Layers className="w-4 h-4 text-purple-400" />
                <h2 className="text-sm font-semibold">Pipeline Cognitiva</h2>
              </div>
              <div className="space-y-2 text-[11px] text-gray-500">
                {[
                  { icon: Eye, label: 'Perception', desc: 'Oculus Prime Intake', color: '#4c6ef5' },
                  { icon: Brain, label: 'Reason', desc: 'Pattern Weavers', color: '#7950f2' },
                  { icon: Shield, label: 'Truth', desc: 'Orthodoxy Wardens', color: '#40c057' },
                ].map(s => (
                  <div key={s.label} className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/[0.02]">
                    <s.icon className="w-3.5 h-3.5" style={{ color: s.color }} />
                    <div>
                      <span className="text-gray-300 font-medium">{s.label}</span>
                      <span className="ml-1 text-gray-600">— {s.desc}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Center: Data viewer */}
          <div className="col-span-12 lg:col-span-5">
            <DataPanel
              data={categoryData}
              loading={loading}
              pipelineStage={pipelineStage}
            />
          </div>

          {/* Right: Analysis / Insights */}
          <div className="col-span-12 lg:col-span-4">
            {analysis ? (
              <InsightsPanel analysis={analysis} />
            ) : (
              <PipelinePanel
                stage={pipelineStage}
                activeCategory={activeCategory}
              />
            )}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-white/5 py-4 text-center text-xs text-gray-600">
        Vitruvyan Frontier v1.0 — Enterprise Cognitive Layer • Powered by Oculus Prime + Sacred Orders
      </footer>
    </div>
  )
}
