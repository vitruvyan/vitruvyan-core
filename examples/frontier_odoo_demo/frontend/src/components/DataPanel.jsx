import React from 'react'
import { Loader2, FileText, Users, TrendingUp, ShoppingCart, Package } from 'lucide-react'

function formatCurrency(val) {
  if (val == null) return '—'
  return new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR' }).format(val)
}

function formatDate(val) {
  if (!val) return '—'
  return new Date(val).toLocaleDateString('it-IT', { day: '2-digit', month: 'short', year: 'numeric' })
}

function PartnerTable({ records }) {
  return (
    <table className="data-table w-full">
      <thead><tr>
        <th>Nome</th><th>Città</th><th>Telefono</th><th>VAT</th>
      </tr></thead>
      <tbody>
        {records.map((r, i) => (
          <tr key={i}>
            <td className="font-medium text-white">{r.name}</td>
            <td>{r.city || '—'}</td>
            <td className="font-mono text-xs">{r.phone || '—'}</td>
            <td className="font-mono text-xs text-gray-500">{r.vat || '—'}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

function InvoiceTable({ records }) {
  return (
    <table className="data-table w-full">
      <thead><tr>
        <th>Numero</th><th>Partner</th><th>Importo</th><th>Data</th><th>Stato</th>
      </tr></thead>
      <tbody>
        {records.map((r, i) => (
          <tr key={i}>
            <td className="font-mono text-xs text-brand-400">{r.name}</td>
            <td className="text-white">{r.partner_id?.[1] || '—'}</td>
            <td className="font-mono text-right">{formatCurrency(r.amount_total)}</td>
            <td className="text-xs">{formatDate(r.invoice_date)}</td>
            <td>
              <PaymentBadge state={r.payment_state} />
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

function PaymentBadge({ state }) {
  const styles = {
    paid: 'bg-green-500/10 text-green-400 border-green-500/20',
    not_paid: 'bg-red-500/10 text-red-400 border-red-500/20',
    partial: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
    in_payment: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  }
  const labels = {
    paid: 'Pagata',
    not_paid: 'Non pagata',
    partial: 'Parziale',
    in_payment: 'In pagamento',
  }
  return (
    <span className={`inline-flex px-2 py-0.5 rounded text-[10px] font-medium border ${styles[state] || 'bg-gray-500/10 text-gray-400 border-gray-500/20'}`}>
      {labels[state] || state || '—'}
    </span>
  )
}

function OrderTable({ records }) {
  return (
    <table className="data-table w-full">
      <thead><tr>
        <th>Ordine</th><th>Cliente</th><th>Importo</th><th>Data</th><th>Stato</th>
      </tr></thead>
      <tbody>
        {records.map((r, i) => (
          <tr key={i}>
            <td className="font-mono text-xs text-brand-400">{r.name}</td>
            <td className="text-white">{r.partner_id?.[1] || '—'}</td>
            <td className="font-mono text-right">{formatCurrency(r.amount_total)}</td>
            <td className="text-xs">{formatDate(r.date_order)}</td>
            <td>
              <span className="inline-flex px-2 py-0.5 rounded text-[10px] font-medium bg-brand-500/10 text-brand-400 border border-brand-500/20">
                {r.state}
              </span>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

function CRMTable({ records }) {
  return (
    <table className="data-table w-full">
      <thead><tr>
        <th>Opportunità</th><th>Valore Atteso</th><th>Fase</th><th>Tipo</th>
      </tr></thead>
      <tbody>
        {records.map((r, i) => (
          <tr key={i}>
            <td className="font-medium text-white">{r.name}</td>
            <td className="font-mono text-right text-green-400">{formatCurrency(r.expected_revenue)}</td>
            <td className="text-xs">{r.stage_id?.[1] || '—'}</td>
            <td className="text-xs text-gray-400">{r.type || '—'}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

function EmployeeTable({ records }) {
  return (
    <table className="data-table w-full">
      <thead><tr>
        <th>Nome</th><th>Ruolo</th><th>Dipartimento</th>
      </tr></thead>
      <tbody>
        {records.map((r, i) => (
          <tr key={i}>
            <td className="font-medium text-white">{r.name}</td>
            <td>{r.job_title || '—'}</td>
            <td className="text-xs text-gray-400">{r.department_id?.[1] || '—'}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

function ProductTable({ records }) {
  return (
    <table className="data-table w-full">
      <thead><tr>
        <th>Prodotto</th><th>Tipo</th><th>Prezzo</th><th>Categoria</th>
      </tr></thead>
      <tbody>
        {records.map((r, i) => (
          <tr key={i}>
            <td className="font-medium text-white">{r.name}</td>
            <td className="text-xs">
              <span className={`px-2 py-0.5 rounded ${r.type === 'service' ? 'bg-purple-500/10 text-purple-400' : 'bg-blue-500/10 text-blue-400'}`}>
                {r.type === 'service' ? 'Servizio' : 'Prodotto'}
              </span>
            </td>
            <td className="font-mono text-right">{formatCurrency(r.list_price)}</td>
            <td className="text-xs text-gray-400">{r.categ_id?.[1] || '—'}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

const TABLE_MAP = {
  customers: PartnerTable,
  suppliers: PartnerTable,
  invoices: InvoiceTable,
  orders: OrderTable,
  crm: CRMTable,
  employees: EmployeeTable,
  products: ProductTable,
}

export default function DataPanel({ data, loading, pipelineStage }) {
  if (loading && !data) {
    return (
      <div className="glass-card p-8 flex items-center justify-center h-96">
        <div className="text-center">
          <Loader2 className="w-8 h-8 text-brand-400 animate-spin mx-auto mb-3" />
          <p className="text-sm text-gray-400">Acquisizione dati da Odoo…</p>
        </div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="glass-card p-8 flex items-center justify-center h-96">
        <div className="text-center max-w-xs">
          <div className="w-16 h-16 rounded-2xl mx-auto mb-4 flex items-center justify-center"
               style={{ background: 'var(--gradient-brand)', opacity: 0.7 }}>
            <FileText className="w-7 h-7 text-white" />
          </div>
          <h3 className="text-base font-semibold mb-2">Seleziona una sorgente</h3>
          <p className="text-sm text-gray-500">
            Clicca su una categoria nel pannello a sinistra per esplorare i dati ERP in tempo reale.
          </p>
        </div>
      </div>
    )
  }

  const TableComponent = TABLE_MAP[data.key]

  return (
    <div className="glass-card overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-white/5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-3 h-3 rounded-full" style={{ backgroundColor: data.color }} />
          <h2 className="text-sm font-semibold">{data.label}</h2>
          <span className="text-xs text-gray-500 bg-white/5 px-2 py-0.5 rounded-full">
            {data.records.length} record
          </span>
        </div>
        {pipelineStage && (
          <div className="flex items-center gap-1.5 text-[10px]">
            <span className={`w-1.5 h-1.5 rounded-full ${pipelineStage === 'complete' ? 'bg-green-400' : 'bg-brand-400 pulse-dot'}`} />
            <span className="text-gray-400">
              {pipelineStage === 'ingestion' && 'Ingestione…'}
              {pipelineStage === 'analysis' && 'Analisi…'}
              {pipelineStage === 'insight' && 'Generazione insight…'}
              {pipelineStage === 'complete' && 'Completo'}
            </span>
          </div>
        )}
      </div>

      {/* Table */}
      <div className="overflow-x-auto max-h-[600px] overflow-y-auto">
        {TableComponent && <TableComponent records={data.records} />}
      </div>
    </div>
  )
}
