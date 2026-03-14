import React from 'react'
import { Eye, Brain, Shield, Zap, Database, ArrowDown, CheckCircle2 } from 'lucide-react'

const STAGES = [
  {
    key: 'ingestion',
    icon: Eye,
    label: 'Perception',
    detail: 'Oculus Prime acquisisce i dati dall\'ERP e crea Evidence Pack normalizzati.',
    color: '#4c6ef5',
  },
  {
    key: 'analysis',
    icon: Brain,
    label: 'Reason',
    detail: 'Pattern Weavers analizzano segmentazione, trend e anomalie nei dati strutturati.',
    color: '#7950f2',
  },
  {
    key: 'insight',
    icon: Shield,
    label: 'Truth',
    detail: 'Orthodoxy Wardens validano le conclusioni e ne garantiscono la coerenza.',
    color: '#40c057',
  },
]

export default function PipelinePanel({ stage, activeCategory }) {
  if (!activeCategory) {
    return (
      <div className="glass-card p-8 h-96 flex items-center justify-center">
        <div className="text-center max-w-xs">
          <div className="w-16 h-16 rounded-2xl mx-auto mb-4 flex items-center justify-center"
               style={{ background: 'linear-gradient(135deg, #7950f2, #4c6ef5)', opacity: 0.7 }}>
            <Zap className="w-7 h-7 text-white" />
          </div>
          <h3 className="text-base font-semibold mb-2">Pipeline Cognitiva</h3>
          <p className="text-sm text-gray-500">
            Il flusso cognitivo di Vitruvyan si attiverà quando selezioni una sorgente dati.
          </p>
          <div className="mt-6 space-y-3">
            {STAGES.map((s, i) => (
              <div key={s.key} className="flex items-center gap-3 text-left px-4 py-2 rounded-lg bg-white/[0.02]">
                <s.icon className="w-4 h-4 flex-shrink-0" style={{ color: s.color }} />
                <div>
                  <span className="text-xs font-medium text-gray-300">{s.label}</span>
                  <span className="text-[10px] text-gray-600 ml-1.5">{s.detail.split(' ').slice(0, 5).join(' ')}…</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  const activeIdx = STAGES.findIndex(s => s.key === stage)
  const isComplete = stage === 'complete'

  return (
    <div className="glass-card p-6">
      <div className="flex items-center gap-2 mb-6">
        <Zap className="w-4 h-4 text-purple-400" />
        <h2 className="text-sm font-semibold">Pipeline Elaborazione</h2>
      </div>

      <div className="space-y-1">
        {STAGES.map((s, i) => {
          const isActive = i === activeIdx && !isComplete
          const isDone = i < activeIdx || isComplete
          const Icon = s.icon

          return (
            <React.Fragment key={s.key}>
              <div
                className={`rounded-xl p-4 border transition-all duration-500 ${
                  isActive
                    ? 'border-white/15 bg-white/[0.06] shadow-lg'
                    : isDone
                    ? 'border-green-500/10 bg-green-500/[0.03]'
                    : 'border-transparent bg-white/[0.02]'
                }`}
              >
                <div className="flex items-center gap-3 mb-2">
                  <div
                    className={`w-8 h-8 rounded-lg flex items-center justify-center transition-all ${
                      isDone ? 'bg-green-500/20' : ''
                    }`}
                    style={!isDone ? { backgroundColor: `${s.color}20` } : {}}
                  >
                    {isDone ? (
                      <CheckCircle2 className="w-4 h-4 text-green-400" />
                    ) : (
                      <Icon
                        className={`w-4 h-4 ${isActive ? 'animate-pulse' : ''}`}
                        style={{ color: s.color }}
                      />
                    )}
                  </div>
                  <div className="flex-1">
                    <div className="text-sm font-medium flex items-center gap-2">
                      {s.label}
                      {isActive && (
                        <span className="text-[10px] text-brand-400 font-normal animate-pulse">
                          in esecuzione…
                        </span>
                      )}
                      {isDone && (
                        <span className="text-[10px] text-green-400 font-normal">
                          completato
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <p className="text-xs text-gray-500 pl-11">{s.detail}</p>
              </div>
              {i < STAGES.length - 1 && (
                <div className="flex justify-center py-1">
                  <ArrowDown className={`w-3.5 h-3.5 transition-colors duration-300 ${
                    isDone ? 'text-green-500/40' : 'text-white/10'
                  }`} />
                </div>
              )}
            </React.Fragment>
          )
        })}
      </div>

      {isComplete && (
        <div className="mt-6 p-4 rounded-xl border border-green-500/20 bg-green-500/[0.04]">
          <div className="flex items-center gap-2 text-green-400 text-sm font-medium mb-1">
            <CheckCircle2 className="w-4 h-4" /> Pipeline completata
          </div>
          <p className="text-[11px] text-gray-500">
            I dati sono stati acquisiti, analizzati e validati dal framework epistemico.
          </p>
        </div>
      )}
    </div>
  )
}
