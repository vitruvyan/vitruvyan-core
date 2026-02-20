// ui/components/adapters/index.js
// Adapter Registry — Central Export
// Last updated: Feb 20, 2026

/**
 * Adapter Registry
 * 
 * Import this to access the global adapter registry
 * and register new adapters.
 */

export { adapterRegistry } from '../../contracts'

// Example adapters (for reference)
export { ConversationalAdapter } from './_base/BaseAdapterExample'
export { FinanceSingleTickerAdapter } from './_examples/FinanceSingleTickerAdapter'

/**
 * Usage:
 * 
 * ```javascript
 * import { adapterRegistry, ConversationalAdapter } from '@/ui/components/adapters'
 * 
 * // Register adapter
 * adapterRegistry.register(new ConversationalAdapter())
 * 
 * // Get adapter by name
 * const adapter = adapterRegistry.get('conversational')
 * 
 * // Get adapter by conversation type
 * const adapter = adapterRegistry.getByConversationType('single_ticker')
 * 
 * // Use adapter
 * const uiPayload = adapter.map(backendFinalState)
 * ```
 */
