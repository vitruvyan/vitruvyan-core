// ui/components/adapters/_base/BaseAdapterExample.js
// Base Adapter Example — Domain-Agnostic Pattern
// Last updated: Feb 20, 2026

/**
 * Base Adapter Example
 * 
 * This is a reference implementation showing how to create
 * a domain-agnostic adapter using the BaseAdapter class.
 * 
 * Pattern: Backend State → map() → UIResponsePayload
 */

import { BaseAdapter } from '../../../contracts'

export class ConversationalAdapter extends BaseAdapter {
  name = 'conversational'

  constructor() {
    super({
      domain: 'generic',
      description: 'Generic conversational adapter for simple Q&A',
      conversationTypes: ['conversational', 'unknown', 'generic'],
      version: '1.0.0',
      author: 'vitruvyan-core'
    })
  }

  /**
   * Map backend state to UI payload
   * 
   * @param {Object} state - LangGraph final state
   * @returns {UIResponsePayload}
   */
  map(state) {
    // Extract data from backend state
    const canResponse = state.can_response || {}
    const entities = this.extractEntities(state)
    const veeAll = state.vee_explanations || {}
    const vee = veeAll[entities[0]] || {}

    // Build narrative
    const narrativeText = canResponse.narrative || state.answer || vee.summary || "I don't have a specific answer for that."

    // Build follow-ups (if available)
    const followUpQueries = (canResponse.follow_ups || []).map((query, idx) => ({
      label: query,
      query: query,
      icon: 'HelpCircle'
    }))

    // Build VEE explanations
    const veePayload = this.buildVEE(
      vee.technical,
      vee.detailed,
      vee.contextualized
    )

    // Build context
    const contextPayload = this.buildContext(
      'conversational',
      entities,
      {
        intent: state.intent || 'unknown',
        confidence: state.confidence || 0
      }
    )

    return {
      narrative: this.buildNarrative(narrativeText, 'neutral', state.intent),
      followUps: this.buildFollowUps(followUpQueries),
      evidence: { sections: [] }, // No structured evidence for conversational
      vee_explanations: veePayload,
      context: contextPayload
    }
  }
}

/**
 * Usage:
 * 
 * ```javascript
 * import { adapterRegistry } from '@/ui/contracts'
 * import { ConversationalAdapter } from './BaseAdapterExample'
 * 
 * // Register adapter
 * adapterRegistry.register(new ConversationalAdapter())
 * 
 * // Use adapter
 * const adapter = adapterRegistry.get('conversational')
 * const uiPayload = adapter.map(backendState)
 * ```
 */
