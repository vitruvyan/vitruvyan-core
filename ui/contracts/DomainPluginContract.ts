// ui/contracts/DomainPluginContract.ts
// Domain Plugin Contract — Vitruvyan Core
// Last updated: Feb 20, 2026

import { AdapterContract } from './AdapterContract'
import { VEEPayload, MetricVEE } from './UIContract'

/**
 * Domain Plugin Contract
 * 
 * Enables verticals to extend the UI without modifying core infrastructure.
 * 
 * Pattern:
 * - Core UI provides infrastructure (Chat, Renderer, Composites)
 * - Domain plugins provide UX (adapters, VEE content, hooks, theme overrides)
 * 
 * Inspired by: Vitruvyan Core vertical pattern + Mercator Costituzione Art. X
 */
export interface DomainPluginContract {
  /**
   * Plugin metadata
   */
  metadata: DomainPluginMetadata

  /**
   * Domain-specific adapters
   * These map backend state to UIResponsePayload for this domain
   */
  adapters: AdapterContract[]

  /**
   * Domain-specific VEE content
   * Explanations for domain-specific metrics/concepts
   */
  vee_content?: VEEContentRegistry

  /**
   * Domain-specific hooks (optional)
   * Custom React hooks for domain logic
   */
  hooks?: Record<string, Function>

  /**
   * Theme overrides (optional)
   * Domain can customize colors, fonts, spacing
   */
  theme_overrides?: Partial<ThemeTokens>

  /**
   * Domain-specific components (optional)
   * Custom React components for specialized UX
   */
  components?: Record<string, any>

  /**
   * Initialization function
   * Called when plugin is loaded
   */
  init?(): void | Promise<void>

  /**
   * Cleanup function
   * Called when plugin is unloaded
   */
  cleanup?(): void | Promise<void>
}

/**
 * Domain Plugin Metadata
 */
export interface DomainPluginMetadata {
  /** Plugin unique identifier */
  id: string

  /** Display name */
  name: string

  /** Domain identifier (finance, energy, facility, etc.) */
  domain: string

  /** Version (semver) */
  version: string

  /** Description */
  description?: string

  /** Author/team */
  author?: string

  /** Dependencies (other plugins required) */
  dependencies?: string[]

  /** Homepage URL */
  homepage?: string

  /** License */
  license?: string
}

/**
 * VEE Content Registry
 * 
 * Maps domain concepts to explanations.
 */
export interface VEEContentRegistry {
  /**
   * Metrics explanations
   * Key: metric_name (e.g., 'revenue_growth', 'roic', 'debt_to_equity')
   */
  metrics?: Record<string, MetricVEE>

  /**
   * Concepts explanations
   * Key: concept_name (e.g., 'fundamentals', 'risk', 'momentum')
   */
  concepts?: Record<string, ConceptVEE>

  /**
   * Evidence section templates
   * Key: section_id (e.g., 'fundamentals', 'risk_analysis')
   */
  evidenceSections?: Record<string, EvidenceSectionVEE>
}

/**
 * Concept VEE
 */
export interface ConceptVEE {
  /** Concept name */
  name: string

  /** Simple explanation (1 sentence) */
  simple: string

  /** Detailed explanation (1 paragraph) */
  detailed: string

  /** Technical explanation (for experts) */
  technical: string

  /** Why it matters (context) */
  relevance: string

  /** Related concepts */
  related?: string[]
}

/**
 * Evidence Section VEE
 */
export interface EvidenceSectionVEE {
  /** Section title */
  title: string

  /** Section description */
  description: string

  /** Explanation of what this section proves */
  purpose: string

  /** How to interpret data in this section */
  interpretation: string
}

/**
 * Theme Tokens (Partial Override)
 */
export interface ThemeTokens {
  colors: {
    primary: string
    secondary: string
    accent: string
    background: string
    foreground: string
    muted: string
    border: string
    success: string
    warning: string
    error: string
    info: string
  }
  fonts: {
    heading: string
    body: string
    mono: string
  }
  spacing: {
    xs: string
    sm: string
    md: string
    lg: string
    xl: string
  }
  radius: {
    sm: string
    md: string
    lg: string
    full: string
  }
  [key: string]: any
}

/**
 * Domain Plugin Registry
 */
export interface DomainPluginRegistry {
  /**
   * Register a domain plugin
   */
  register(plugin: DomainPluginContract): void

  /**
   * Get plugin by ID
   */
  get(id: string): DomainPluginContract | undefined

  /**
   * Get plugin by domain
   */
  getByDomain(domain: string): DomainPluginContract | undefined

  /**
   * List all registered plugins
   */
  list(): DomainPluginContract[]

  /**
   * Initialize all plugins
   */
  initAll(): Promise<void>

  /**
   * Cleanup all plugins
   */
  cleanupAll(): Promise<void>
}

/**
 * Domain Plugin Registry Implementation
 */
export class DomainPluginRegistryImpl implements DomainPluginRegistry {
  private plugins: Map<string, DomainPluginContract> = new Map()
  private domainIndex: Map<string, DomainPluginContract> = new Map()

  async register(plugin: DomainPluginContract): Promise<void> {
    // Check dependencies
    if (plugin.metadata.dependencies) {
      for (const depId of plugin.metadata.dependencies) {
        if (!this.plugins.has(depId)) {
          throw new Error(
            `Plugin ${plugin.metadata.id} requires dependency ${depId} which is not registered`
          )
        }
      }
    }

    // Register plugin
    this.plugins.set(plugin.metadata.id, plugin)
    this.domainIndex.set(plugin.metadata.domain, plugin)

    // Initialize
    if (plugin.init) {
      await plugin.init()
    }

    console.log(
      `[DomainPluginRegistry] Registered plugin: ${plugin.metadata.name} (${plugin.metadata.id})`
    )
  }

  get(id: string): DomainPluginContract | undefined {
    return this.plugins.get(id)
  }

  getByDomain(domain: string): DomainPluginContract | undefined {
    return this.domainIndex.get(domain)
  }

  list(): DomainPluginContract[] {
    return Array.from(this.plugins.values())
  }

  async initAll(): Promise<void> {
    const initPromises = Array.from(this.plugins.values())
      .filter(plugin => plugin.init)
      .map(plugin => plugin.init!())

    await Promise.all(initPromises)
    console.log('[DomainPluginRegistry] All plugins initialized')
  }

  async cleanupAll(): Promise<void> {
    const cleanupPromises = Array.from(this.plugins.values())
      .filter(plugin => plugin.cleanup)
      .map(plugin => plugin.cleanup!())

    await Promise.all(cleanupPromises)
    console.log('[DomainPluginRegistry] All plugins cleaned up')
  }
}

/**
 * Global domain plugin registry singleton
 */
export const domainPluginRegistry = new DomainPluginRegistryImpl()

/**
 * Decorator for auto-registering domain plugins
 */
export function RegisterDomainPlugin() {
  return function (plugin: DomainPluginContract) {
    domainPluginRegistry.register(plugin)
    return plugin
  }
}

/**
 * Type guard for domain plugin
 */
export function isDomainPlugin(obj: any): obj is DomainPluginContract {
  return (
    obj &&
    typeof obj === 'object' &&
    'metadata' in obj &&
    'adapters' in obj &&
    typeof obj.metadata === 'object' &&
    typeof obj.metadata.id === 'string' &&
    typeof obj.metadata.domain === 'string' &&
    Array.isArray(obj.adapters)
  )
}
