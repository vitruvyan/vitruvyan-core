// adapters/index.js
import { conversationalAdapter } from './conversationalAdapter'
import { singleTickerAdapter } from './singleTickerAdapter'
import { comparisonAdapter } from './comparisonAdapter'
import { allocationAdapter } from './allocationAdapter'
import { screeningAdapter } from './screeningAdapter'
import { portfolioAdapter } from './portfolioAdapter'
import { portfolioGuardianAdapter } from './portfolioGuardianAdapter'
import { approvalAdapter } from './approvalAdapter'

const adapterMap = {
  'conversational': conversationalAdapter,
  'single': singleTickerAdapter,
  'comparison': comparisonAdapter,
  'allocation': allocationAdapter,
  'screening': screeningAdapter,
  'portfolio': portfolioAdapter,
  'portfolio_guardian': portfolioGuardianAdapter,
  'approval': approvalAdapter,
  // Fallback
  'default': conversationalAdapter
}

export function selectAdapter(conversationType) {
  return adapterMap[conversationType] || adapterMap.default
}

export function adaptFinalState(finalState) {
  const type = finalState.conversation_type || 'conversational'
  const adapter = selectAdapter(type)
  return adapter.map(finalState)
}