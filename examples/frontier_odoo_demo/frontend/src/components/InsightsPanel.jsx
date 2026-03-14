import React from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { TrendingUp, FileText, Users, AlertTriangle, CircleDollarSign, BarChart3 } from 'lucide-react'

const CHART_COLORS = ['#4c6ef5', '#7950f2', '#40c057', '#f59f00', '#e64980', '#15aabf', '#ff6b6b', '#20c997']

function formatCurrency(val) {
  if (val == null) return '—'
  return new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(val)
}

function MetricCard({ icon: Icon, label, value, sub, color = '#4c6ef5' }) {
  return (
    <div className="glass-card p-4">
      <div className="flex items-center gap-2 mb-2">
        <div className="w-7 h-7 rounded-lg flex items-center justify-center"
             style={{ backgroundColor: `${color}20` }}>
          <Icon className="w-3.5 h-3.5" style={{ color }} />
        </div>
        <span className="text-[11px] text-gray-500">{label}</span>
      </div>
      <div className="text-xl font-bold text-white">{value}</div>
      {sub && <div className="text-[11px] text-gray-500 mt-1">{sub}</div>}
    </div>
  )
}

function InvoiceInsights({ data }) {
  const { receivable, payable, net_position } = data
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <MetricCard
          icon={TrendingUp}
          label="Ricavi (fatture emesse)"
          value={formatCurrency(receivable.total)}
          sub={`${receivable.count} fatture • media ${formatCurrency(receivable.avg)}`}
          color="#40c057"
        />
        <MetricCard
          icon={FileText}
          label="Costi (fatture ricevute)"
          value={formatCurrency(payable.total)}
          sub={`${payable.count} fatture • media ${formatCurrency(payable.avg)}`}
          color="#e64980"
        />
      </div>

      <div className="glass-card p-4">
        <div className="flex items-center gap-2 mb-3">
          <CircleDollarSign className="w-4 h-4 text-brand-400" />
          <span className="text-sm font-semibold">Posizione Netta</span>
        </div>
        <div className={`text-3xl font-bold ${net_position >= 0 ? 'text-green-400' : 'text-red-400'}`}>
          {formatCurrency(net_position)}
        </div>
      </div>

      {(receivable.unpaid > 0 || payable.unpaid > 0) && (
        <div className="glass-card p-4 border-l-2 border-yellow-500/50">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-4 h-4 text-yellow-400" />
            <span className="text-sm font-medium text-yellow-400">Crediti in sospeso</span>
          </div>
          <div className="grid grid-cols-2 gap-4 text-xs">
            <div>
              <span className="text-gray-500">Da incassare:</span>
              <div className="text-base font-bold text-yellow-400">{formatCurrency(receivable.unpaid_amount)}</div>
              <span className="text-gray-600">{receivable.unpaid} fatture</span>
            </div>
            <div>
              <span className="text-gray-500">Da pagare:</span>
              <div className="text-base font-bold text-orange-400">{formatCurrency(payable.unpaid_amount)}</div>
              <span className="text-gray-600">{payable.unpaid} fatture</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function CRMInsights({ data }) {
  const { total_opportunities, total_pipeline_value, avg_deal_size, by_stage } = data
  const chartData = Object.entries(by_stage).map(([name, vals]) => ({
    name: name.length > 12 ? name.slice(0, 12) + '…' : name,
    value: vals.revenue,
    count: vals.count,
  }))

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <MetricCard
          icon={TrendingUp}
          label="Pipeline totale"
          value={formatCurrency(total_pipeline_value)}
          sub={`${total_opportunities} opportunità`}
          color="#7950f2"
        />
        <MetricCard
          icon={BarChart3}
          label="Dimensione media deal"
          value={formatCurrency(avg_deal_size)}
          color="#15aabf"
        />
      </div>

      {chartData.length > 0 && (
        <div className="glass-card p-4">
          <h3 className="text-xs font-semibold text-gray-400 mb-3">Pipeline per fase</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={chartData} layout="vertical" margin={{ left: 0, right: 16 }}>
              <XAxis type="number" hide />
              <YAxis type="category" dataKey="name" tick={{ fill: '#9ca3af', fontSize: 11 }} width={100} />
              <Tooltip
                contentStyle={{ background: '#1a1d2e', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 12 }}
                formatter={(v) => [formatCurrency(v), 'Valore']}
              />
              <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                {chartData.map((_, i) => (
                  <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}

function CustomerInsights({ data }) {
  const { total_customers, by_city, cities_count } = data
  const chartData = Object.entries(by_city).slice(0, 8).map(([city, count]) => ({
    name: city,
    value: count,
  }))

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <MetricCard
          icon={Users}
          label="Clienti totali"
          value={total_customers}
          color="#4c6ef5"
        />
        <MetricCard
          icon={BarChart3}
          label="Città servite"
          value={cities_count}
          color="#15aabf"
        />
      </div>

      {chartData.length > 0 && (
        <div className="glass-card p-4">
          <h3 className="text-xs font-semibold text-gray-400 mb-3">Distribuzione per città</h3>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={chartData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={80}
                innerRadius={40}
                paddingAngle={3}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                labelLine={false}
              >
                {chartData.map((_, i) => (
                  <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: '#1a1d2e', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 12 }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Top cities list */}
      <div className="glass-card p-4">
        <h3 className="text-xs font-semibold text-gray-400 mb-3">Top città</h3>
        <div className="space-y-2">
          {Object.entries(by_city).slice(0, 6).map(([city, count], i) => (
            <div key={city} className="flex items-center gap-3">
              <div className="w-2 h-2 rounded-full" style={{ backgroundColor: CHART_COLORS[i % CHART_COLORS.length] }} />
              <span className="text-sm flex-1">{city}</span>
              <span className="text-xs text-gray-500 font-mono">{count}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default function InsightsPanel({ analysis }) {
  if (!analysis) return null

  const INSIGHT_MAP = {
    invoices: InvoiceInsights,
    crm: CRMInsights,
    customers: CustomerInsights,
  }

  const Component = INSIGHT_MAP[analysis.key]
  if (!Component) {
    return (
      <div className="glass-card p-6 text-center text-sm text-gray-500">
        Analisi non disponibile per questa categoria.
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center gap-2 mb-4">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center"
             style={{ background: 'var(--gradient-success)' }}>
          <BarChart3 className="w-4 h-4 text-white" />
        </div>
        <div>
          <h2 className="text-sm font-semibold">Cognitive Insights</h2>
          <p className="text-[10px] text-gray-500">Analisi epistemica in tempo reale</p>
        </div>
      </div>
      <Component data={analysis.data} />
    </div>
  )
}
