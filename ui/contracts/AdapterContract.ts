// ui/contracts/AdapterContract.ts
// Adapter Contract Interface — Vitruvyan Core
// Last updated: Feb 20, 2026

import {
  UIResponsePayload,
  ValidationResult,
  EvidenceSectionPayload,
  FollowUpPayload,
  NarrativePayload,
  VEEPayload,
  ContextPayload
} from './UIContract'

/**
 * Adapter Contract
 * 
 * Pattern: Backend State → Adapter.map() → UIResponsePayload → Renderer
 * 
 * Every adapter MUST implement this interface to transform
 * backend graph state into canonical UI payload.
 * 
 * Inspired by: Mercator UI Constitution Art. II
 * "L'adapter è l'unità di UX"
 */
export interface AdapterContract<TState = any> {
  /**
   * Adapter name (unique identifier)
   * Examples: 'singleTicker', 'comparison', 'allocation', 'conversational'
   */
  name: string

  /**
   * Transform backend state to UI payload
   * 
   * @param state - Backend graph final state (LangGraph output)
   * @returns UIResponsePayload conforming to UIContract
   */
  map(state: TState): UIResponsePayload

  /**
   * Validate generated payload (optional but recommended)
   * 
   * @param payload - Generated UIResponsePayload
   * @returns Validation result with errors/warnings
   */
  validate?(payload: UIResponsePayload): ValidationResult

  /**
   * Adapter metadata (optional)
   */
  metadata?: AdapterMetadata
}

/**
 * Adapter Metadata
 */
export interface AdapterMetadata {
  /** Domain this adapter belongs to (e.g., 'finance', 'energy', 'generic') */
  domain?: string

  /** Description */
  description?: string

  /** Supported conversation types */
  conversationTypes?: string[]

  /** Version */
  version?: string

  /** Author/team */
  author?: string
}

/**
 * Adapter Registry
 * 
 * Central registry for all adapters in the system.
 * Enables dynamic adapter selection based on conversation type.
 */
export interface AdapterRegistry {
  /**
   * Register an adapter
   */
  register(adapter: AdapterContract): void

  /**
   * Get adapter by name
   */
  get(name: string): AdapterContract | undefined

  /**
   * Get adapter by conversation type
   */
  getByConversationType(conversationType: string): AdapterContract | undefined

  /**
   * List all registered adapters
   */
  list(): AdapterContract[]

  /**
   * Get adapters by domain
   */
  getByDomain(domain: string): AdapterContract[]
}

/**
 * Base Adapter (Abstract Implementation)
 * 
 * Provides common utilities for building adapters.
 * Domain-specific adapters should extend this class.
 */
export abstract class BaseAdapter<TState = any> implements AdapterContract<TState> {
  abstract name: string
  abstract map(state: TState): UIResponsePayload
  
  metadata?: AdapterMetadata

  constructor(metadata?: AdapterMetadata) {
    this.metadata = metadata
  }

  /**
   * Default validation (checks required fields)
   */
  validate(payload: UIResponsePayload): ValidationResult {
    const errors: string[] = []
    const warnings: string[] = []

    // Required fields
    if (!payload.narrative?.text) {
      errors.push('narrative.text is required')
    }

    if (!Array.isArray(payload.followUps)) {
      errors.push('followUps must be an array')
    }

    if (!payload.evidence?.sections || !Array.isArray(payload.evidence.sections)) {
      errors.push('evidence.sections must be an array')
    }

    if (!payload.vee_explanations) {
      warnings.push('vee_explanations is missing')
    }

    if (!payload.context) {
      warnings.push('context is missing')
    }

    // Evidence sections validation
    if (payload.evidence?.sections) {
      payload.evidence.sections.forEach((section, index) => {
        if (!section.id) {
          errors.push(`evidence.sections[${index}].id is required`)
        }
        if (!section.title) {
          errors.push(`evidence.sections[${index}].title is required`)
        }
        if (typeof section.priority !== 'number') {
          errors.push(`evidence.sections[${index}].priority must be a number`)
        }
      })
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings
    }
  }

  /**
   * Helper: Extract entities from state
   */
  protected extractEntities(state: any): string[] {
    return state.tickers || state.entities || state.entity_ids || []
  }

  /**
   * Helper: Build narrative payload
   */
  protected buildNarrative(
    text: string,
    tone: NarrativePayload['tone'] = 'neutral',
    intent?: string
  ): NarrativePayload {
    return {
      text,
      tone,
      intent,
      recommendation: null
    }
  }

  /**
   * Helper: Build follow-ups
   */
  protected buildFollowUps(
    followUpQueries: Array<{ label: string; query: string; icon?: string }>
  ): FollowUpPayload[] {
    return followUpQueries.map((fup, index) => ({
      id: `followup-${index}`,
      label: fup.label,
      query: fup.query,
      type: 'question' as const,
      icon: fup.icon
    }))
  }

  /**
   * Helper: Build context payload
   */
  protected buildContext(
    conversationType: string,
    entities: string[],
    additionalContext?: Record<string, any>
  ): ContextPayload {
    return {
      conversation_type: conversationType,
      entities,
      timestamp: new Date().toISOString(),
      user_id: null,
      ...additionalContext
    }
  }

  /**
   * Helper: Build VEE payload
   */
  protected buildVEE(
    technical?: string,
    detailed?: string,
    contextualized?: string,
    metrics?: Record<string, any>
  ): VEEPayload {
    return {
      technical,
      detailed,
      contextualized,
      metrics
    }
  }

  /**
   * Helper: Build evidence section
   */
  protected buildEvidenceSection(
    id: string,
    title: string,
    contentType: EvidenceSectionPayload['content']['type'],
    data: any,
    options?: {
      subtitle?: string
      priority?: number
      defaultExpanded?: boolean
      badge?: EvidenceSectionPayload['badge']
      tension_detected?: boolean
    }
  ): EvidenceSectionPayload {
    return {
      id,
      title,
      subtitle: options?.subtitle,
      priority: options?.priority ?? 999,
      defaultExpanded: options?.defaultExpanded ?? false,
      content: {
        type: contentType,
        data
      },
      badge: options?.badge,
      tension_detected: options?.tension_detected
    }
  }
}

/**
 * Adapter Registry Implementation
 */
export class AdapterRegistryImpl implements AdapterRegistry {
  private adapters: Map<string, AdapterContract> = new Map()
  private conversationTypeIndex: Map<string, AdapterContract> = new Map()

  register(adapter: AdapterContract): void {
    this.adapters.set(adapter.name, adapter)

    // Index by conversation types
    if (adapter.metadata?.conversationTypes) {
      adapter.metadata.conversationTypes.forEach(type => {
        this.conversationTypeIndex.set(type, adapter)
      })
    }

    console.log(`[AdapterRegistry] Registered adapter: ${adapter.name}`)
  }

  get(name: string): AdapterContract | undefined {
    return this.adapters.get(name)
  }

  getByConversationType(conversationType: string): AdapterContract | undefined {
    return this.conversationTypeIndex.get(conversationType)
  }

  list(): AdapterContract[] {
    return Array.from(this.adapters.values())
  }

  getByDomain(domain: string): AdapterContract[] {
    return this.list().filter(adapter => adapter.metadata?.domain === domain)
  }
}

/**
 * Global adapter registry singleton
 */
export const adapterRegistry = new AdapterRegistryImpl()

/**
 * Decorator for auto-registering adapters
 */
export function RegisterAdapter(metadata?: AdapterMetadata) {
  return function <T extends { new(...args: any[]): AdapterContract }>(constructor: T) {
    const instance = new constructor()
    instance.metadata = metadata
    adapterRegistry.register(instance)
    return constructor
  }
}
