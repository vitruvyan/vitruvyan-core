// ui/contracts/index.ts
// UI Contracts — Central Export
// Last updated: Feb 20, 2026

/**
 * Core UI Contracts
 * 
 * This module exports all UI contracts for vitruvyan-core.
 * Import from here to ensure type consistency across the UI.
 */

// UIContract exports
export type {
  UIContract,
  UIResponsePayload,
  NarrativePayload,
  FollowUpPayload,
  EvidencePayload,
  EvidenceSectionPayload,
  VEEPayload,
  MetricVEE,
  ContextPayload,
  DomainExtensions,
  ValidationResult
} from './UIContract'

export {
  isValidUIResponsePayload,
  isValidNarrativePayload,
  isValidEvidencePayload
} from './UIContract'

// AdapterContract exports
export type {
  AdapterContract,
  AdapterMetadata,
  AdapterRegistry
} from './AdapterContract'

export {
  BaseAdapter,
  AdapterRegistryImpl,
  adapterRegistry,
  RegisterAdapter
} from './AdapterContract'

// DomainPluginContract exports
export type {
  DomainPluginContract,
  DomainPluginMetadata,
  VEEContentRegistry,
  ConceptVEE,
  EvidenceSectionVEE,
  MetricVEE as DomainMetricVEE,
  ThemeTokens,
  DomainPluginRegistry
} from './DomainPluginContract'

export {
  DomainPluginRegistryImpl,
  domainPluginRegistry,
  RegisterDomainPlugin,
  isDomainPlugin
} from './DomainPluginContract'

/**
 * Usage Examples:
 * 
 * ```typescript
 * import {
 *   AdapterContract,
 *   BaseAdapter,
 *   UIResponsePayload,
 *   adapterRegistry
 * } from '@/ui/contracts'
 * 
 * // Create adapter
 * class MyAdapter extends BaseAdapter {
 *   name = 'myAdapter'
 *   
 *   map(state: any): UIResponsePayload {
 *     return {
 *       narrative: this.buildNarrative(state.text),
 *       followUps: this.buildFollowUps([...]),
 *       evidence: { sections: [...] },
 *       vee_explanations: this.buildVEE(...),
 *       context: this.buildContext('my_type', [...])
 *     }
 *   }
 * }
 * 
 * // Register adapter
 * adapterRegistry.register(new MyAdapter())
 * 
 * // Create domain plugin
 * const myDomainPlugin: DomainPluginContract = {
 *   metadata: {
 *     id: 'my-domain',
 *     name: 'My Domain',
 *     domain: 'my_domain',
 *     version: '1.0.0'
 *   },
 *   adapters: [new MyAdapter()],
 *   vee_content: { ... }
 * }
 * 
 * // Register domain plugin
 * domainPluginRegistry.register(myDomainPlugin)
 * ```
 */
