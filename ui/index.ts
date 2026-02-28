// ui/index.ts
// Vitruvyan UI — Central Export
// Last updated: Feb 28, 2026

/**
 * Vitruvyan UI Framework
 * 
 * Domain-agnostic cognitive interface for Vitruvyan Core.
 * 
 * @example
 * ```typescript
 * import { adapterRegistry, BaseAdapter, UIResponsePayload } from '@vitruvyan/ui'
 * 
 * // Create and register adapter
 * class MyAdapter extends BaseAdapter {
 *   name = 'my_adapter'
 *   map(state): UIResponsePayload {
 *     return {
 *       narrative: this.buildNarrative(state.text),
 *       followUps: [],
 *       evidence: { sections: [] },
 *       vee_explanations: {},
 *       context: this.buildContext('my_type', [])
 *     }
 *   }
 * }
 * 
 * adapterRegistry.register(new MyAdapter())
 * ```
 */

// Contracts (TypeScript interfaces)
export * from './contracts'

// Adapters (example implementations)
export { ConversationalAdapter } from './components/adapters/_base/BaseAdapterExample'
export { FinanceSingleTickerAdapter } from './components/adapters/_examples/FinanceSingleTickerAdapter'

// Components (re-export commonly used)
export { default as Chat } from './components/chat/Chat'
export { ChatMessage } from './components/chat/ChatMessage'
export { ChatInput } from './components/chat/ChatInput'
export { ChatMessages } from './components/chat/ChatMessages'
export { ThinkingSteps } from './components/chat/ThinkingSteps'
export { VitruvyanResponseRenderer } from './components/response'
export { NarrativeBlock } from './components/composites/NarrativeBlock'
export { EvidenceAccordion } from './components/composites/EvidenceAccordion'
export { FollowUpChips } from './components/composites/FollowUpChips'

// Theme
export { tokens } from './components/theme/tokens'

// Hooks
export { useChat } from './components/chat/hooks/useChat'
export { useMessages } from './components/chat/hooks/useMessages'

/**
 * Version
 */
export const VERSION = '0.1.0'

/**
 * Package info
 */
export const UI_INFO = {
  name: '@vitruvyan/ui',
  version: VERSION,
  description: 'Domain-agnostic UI framework for Vitruvyan Core',
  repository: 'https://github.com/vitruvyan/vitruvyan-core/tree/main/ui',
  license: 'SEE LICENSE IN ../LICENSE.md'
}
