// response/VitruvyanResponseRenderer.jsx
// UX Constitution compliant - Jan 2, 2026
// Flow: VEE Summary → Follow-ups → Accordions → AdvisorInsight (AFTER accordions)
'use client'

import { useState } from 'react'
import { tokens } from '../theme/tokens'
import VEEAccordions from '../explainability/vee/VEEAccordions'
import { NarrativeBlock } from '../composites/NarrativeBlock'
import { FollowUpChips } from '../composites/FollowUpChips'
import { EvidenceAccordion } from '../composites/EvidenceAccordion'
import { AdvisorInsight } from '../composites/AdvisorInsight'
import { AdvisorAdapter } from '../adapters/AdvisorAdapter'
import { IntentBadge } from '../composites/IntentBadge'
import { FallbackMessage } from '../composites/FallbackMessage'
import { AllocationPieChart } from './AllocationPieChart'
import { AllocationWeightsTable } from './AllocationWeightsTable'
import { ChevronDown, ChevronUp, HelpCircle, BarChart3 } from 'lucide-react'

export function VitruvyanResponseRenderer({ 
  response, 
  onFollowUpClick, 
  onRetry,
  ticker = null,
  currentPrice = 0,
  userHolding = null,
  onOrderExecuted = null,
  onViewPortfolio = null // Feb 4, 2026: Portfolio navigation callback (optional)
}) {
  const [whyExpanded, setWhyExpanded] = useState(false)
  const [dataExpanded, setDataExpanded] = useState(false)

  // FALLBACK: Handle error or missing response
  if (!response || response.error) {
    return <FallbackMessage error={response?.error} onRetry={onRetry} />
  }

  const { narrative, followUps, evidence, vee_explanations, pieChart, rationale, advisorInsight, context } = response
  const hasEvidence = evidence?.sections?.length > 0
  const isAllocation = context?.conversation_type === 'allocation'
  
  // 🎯 Extract ticker from response (Feb 1, 2026)
  const responseTicker = response.tickers?.[0] || context?.tickers?.[0] || null
  
  // VEE stratification: Technical + Detailed for "Perché?" accordion
  const veeData = vee_explanations || evidence?.vee || {}
  const hasVeeDeepDive = veeData.technical || veeData.detailed

  return (
    <div className={`${tokens.colors.vitruvyan.bg} ${tokens.colors.vitruvyan.border} border ${tokens.radius.card} ${tokens.spacing.card}`}>

      {/* ═══════════════════════════════════════════════════════════════
          LAYER 1: NARRATIVE (VEE Summary)
          Per Costituzione Art. I: "L'utente parla prima con il consulente"
          ═══════════════════════════════════════════════════════════════ */}
      <NarrativeBlock
        text={narrative?.text}
        tone={narrative?.tone}
        recommendation={narrative?.recommendation}
      />

      {/* ═══════════════════════════════════════════════════════════════
          ALLOCATION SPECIFIC: PIE CHART (Always visible, outside accordions)
          ═══════════════════════════════════════════════════════════════ */}
      {isAllocation && pieChart && (
        <div className="mt-6">
          <AllocationPieChart data={pieChart.data} />
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════════
          LAYER 2: FOLLOW-UP QUESTIONS
          Per Costituzione Art. VII: Stratificazione dell'informazione
          ═══════════════════════════════════════════════════════════════ */}
      {followUps?.length > 0 && (
        <div className="mt-4 pt-4 border-t border-emerald-100">
          <FollowUpChips
            questions={followUps}
            onChipClick={onFollowUpClick}
          />
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════════
          LAYER 3: ACCORDION "PERCHÉ?" (VEE Technical + Detailed OR Allocation Rationale)
          Per Costituzione: VEE stratification OR Allocation rationale
          ═══════════════════════════════════════════════════════════════ */}
      {((hasVeeDeepDive && !isAllocation) || (isAllocation && rationale)) && (
        <div className="mt-4 pt-4 border-t border-emerald-100">
          <button
            onClick={() => setWhyExpanded(!whyExpanded)}
            className="flex items-center gap-2 text-sm font-medium text-gray-700 hover:text-gray-900 transition-colors w-full"
          >
            <HelpCircle size={16} className="text-emerald-600" />
            <span>Why?</span>
            <span className="text-xs text-gray-400 ml-1">
              {isAllocation ? 'Allocation rationale' : 'Technical and detailed analysis'}
            </span>
            <span className="ml-auto">
              {whyExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </span>
          </button>

          {whyExpanded && (
            <div className="mt-3 space-y-4 pl-6 border-l-2 border-emerald-200">
              {isAllocation ? (
                /* Allocation Rationale */
                <div>
                  <div className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                    Allocation Method: {rationale.method || 'Optimized'}
                  </div>
                  <p className="text-sm text-gray-700 leading-relaxed">
                    {rationale.text}
                  </p>
                  {rationale.veeDetailed && (
                    <div className="mt-3">
                      <div className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                        Detailed Analysis
                      </div>
                      <p className="text-sm text-gray-700 leading-relaxed">
                        {rationale.veeDetailed}
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                /* VEE Technical + Detailed */
                <>
                  {/* VEE Technical */}
                  {veeData.technical && (
                    <div>
                      <div className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                        Technical Analysis
                      </div>
                      <p className="text-sm text-gray-700 leading-relaxed">
                        {veeData.technical}
                      </p>
                    </div>
                  )}
                  
                  {/* VEE Detailed */}
                  {veeData.detailed && (
                    <div>
                      <div className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                        Detailed Analysis
                      </div>
                      <p className="text-sm text-gray-700 leading-relaxed">
                        {veeData.detailed}
                      </p>
                    </div>
                  )}

                  {/* VEE Contextualized (if available) */}
                  {veeData.contextualized && (
                    <div>
                      <div className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                        Historical Context
                      </div>
                      <p className="text-sm text-gray-700 leading-relaxed">
                        {veeData.contextualized}
                      </p>
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════════
          LAYER 4: ACCORDION "DATI DI SUPPORTO"
          Contains: Signal Drivers → Fundamentals → Risk → Charts
          Per Costituzione Art. XII: Ordine epistemico
          ═══════════════════════════════════════════════════════════════ */}
      {hasEvidence && (
        <div className="mt-4 pt-4 border-t border-emerald-100">
          <button
            onClick={() => setDataExpanded(!dataExpanded)}
            className="flex items-center gap-2 text-sm font-medium text-gray-700 hover:text-gray-900 transition-colors w-full"
          >
            <BarChart3 size={16} className="text-blue-600" />
            <span>Supporting Data</span>
            <span className="text-xs text-gray-400 ml-1">Signal drivers, fundamentals, risk</span>
            <span className="ml-auto">
              {dataExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </span>
          </button>

          {dataExpanded && (
            <div className="mt-4">
              <EvidenceAccordion sections={evidence.sections} />
            </div>
          )}
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════════
          LAYER 5: ADVISOR INSIGHT + TRADING ADAPTER (Feb 1, 2026)
          POSITIONING RULE (BINDING):
          - ALWAYS after accordions (conclusione cognitiva, non introduzione)
          - ALWAYS visible (mai dentro accordion)
          - Renders only if rationale exists
          
          TRADING UX RULE (BINDING - Feb 1, 2026):
          - AdvisorAdapter for single ticker analysis (con trading bubble)
          - AdvisorInsight for allocation/portfolio (NO trading)
          - 5-signal clear system: STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL
          - Bubble expansion pattern (consistent con PortfolioBanner)
          ═══════════════════════════════════════════════════════════════ */}
      {isAllocation ? (
        <AdvisorInsight insight={advisorInsight} />
      ) : (ticker || responseTicker) && response.advisor_recommendation ? (
        <AdvisorAdapter
          advisorRecommendation={response.advisor_recommendation}
          ticker={ticker || responseTicker}
          currentPrice={currentPrice}
          userHolding={userHolding}
          onOrderExecuted={onOrderExecuted}
          onViewPortfolio={onViewPortfolio}
        />
      ) : response.advisor_recommendation ? (
        <AdvisorInsight insight={response.advisor_recommendation} />
      ) : null}
    </div>
  )
}