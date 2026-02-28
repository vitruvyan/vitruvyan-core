// ui/contracts/UIContract.ts
// Domain-Agnostic UI Contract — Vitruvyan Core
// Last updated: Feb 20, 2026

/**
 * Base UI Contract
 * 
 * Defines the canonical interface between backend (LangGraph state)
 * and frontend (UI renderer). All adapters MUST produce this payload.
 * 
 * Inspired by: Mercator UI Constitution (Art. II, III, IV)
 * Pattern: Backend → Adapter → UIPayload → Renderer → User
 */

export interface UIContract {
  /**
   * Response payload consumato dal renderer
   * Questo è l'output OBBLIGATORIO di ogni adapter
   */
  response: UIResponsePayload

  /**
   * Renderer fisso (infrastruttura)
   * Per ora solo VitruvyanResponseRenderer
   */
  renderer: 'VitruvyanResponseRenderer'

  /**
   * Estensioni di dominio (optional)
   * Permettono ai verticali di aggiungere payload custom
   * senza rompere il contract base
   */
  extensions?: DomainExtensions
}

/**
 * UI Response Payload (Canonical Structure)
 * 
 * Flow visivo fisso:
 * 1. Narrative (VEE Summary)
 * 2. Follow-ups (chip interattivi)
 * 3. Evidence (accordions con dati)
 * 4. VEE Deep Dive (spiegazione stratificata)
 * 5. Domain Extensions (advisor, charts, etc.)
 */
export interface UIResponsePayload {
  /**
   * LAYER 1: Narrativa primaria
   * La risposta in linguaggio naturale (da CAN node)
   */
  narrative: NarrativePayload

  /**
   * LAYER 2: Follow-up suggeriti
   * Domande contestuali che l'utente può cliccare
   */
  followUps: FollowUpPayload[]

  /**
   * LAYER 3: Evidenze strutturate
   * Dati/metriche che supportano la narrativa
   */
  evidence: EvidencePayload

  /**
   * LAYER 4: Spiegazione stratificata (VEE)
   * Technical → Detailed → Contextualized
   */
  vee_explanations: VEEPayload

  /**
   * Metadata di contesto
   */
  context: ContextPayload

  /**
   * Estensioni di dominio (optional)
   */
  [key: string]: any
}

/**
 * Narrative Payload
 */
export interface NarrativePayload {
  /** Testo narrativo principale (markdown-safe) */
  text: string

  /** Tono della narrativa */
  tone?: 'confident' | 'neutral' | 'cautious' | 'uncertain'

  /** Raccomandazione esplicita (optional, deprecato in favore di advisor) */
  recommendation?: string | null

  /** Intent riconosciuto (per badge) */
  intent?: string
}

/**
 * Follow-Up Payload
 */
export interface FollowUpPayload {
  /** ID univoco */
  id: string

  /** Testo del chip */
  label: string

  /** Query da inviare al backend quando cliccato */
  query: string

  /** Tipo di follow-up (per styling) */
  type?: 'question' | 'action' | 'exploration'

  /** Icona (lucide-react name) */
  icon?: string
}

/**
 * Evidence Payload
 * 
 * Sezioni accordionabili che provano la narrativa.
 * Order matters: riflette l'epistemologia del dominio.
 */
export interface EvidencePayload {
  /**
   * Sezioni di evidenza (ordine epistemico)
   * Esempio (finance): Solidità → Redditività → Crescita → Risk
   * Esempio (energy): Disponibilità → Efficienza → Sostenibilità → Costo
   */
  sections: EvidenceSectionPayload[]
}

/**
 * Evidence Section Payload
 */
export interface EvidenceSectionPayload {
  /** ID univoco */
  id: string

  /** Titolo sezione */
  title: string

  /** Sottotitolo dinamico (basato su dati) */
  subtitle?: string

  /** Priorità (1 = più importante) */
  priority: number

  /** Espansa di default? */
  defaultExpanded: boolean

  /** Tipo di contenuto */
  content: {
    /** Tipo renderer da usare */
    type: 'signal-drivers' | 'metrics' | 'chart' | 'table' | 'text' | 'custom'

    /** Dati per il renderer */
    data: any
  }

  /** Badge micro-indicatore (visibile da collapsed) */
  badge?: {
    label: string
    color: 'green' | 'gray' | 'orange' | 'red'
  }

  /** Flag tensione epistemica */
  tension_detected?: boolean
}

/**
 * VEE Payload (Explainability Stratificata)
 */
export interface VEEPayload {
  /** Spiegazione tecnica (per esperti) */
  technical?: string | null

  /** Spiegazione dettagliata (per utenti informati) */
  detailed?: string | null

  /** Spiegazione contestualizzata (per tutti) */
  contextualized?: string | null

  /** VEE per singole metriche (key = metric_name) */
  metrics?: Record<string, MetricVEE>
}

/**
 * Metric VEE
 */
export interface MetricVEE {
  /** Spiegazione semplice (tooltip) */
  simple: string

  /** Spiegazione tecnica (accordion) */
  technical: string

  /** Perché conta nel contesto attuale */
  relevance: string
}

/**
 * Context Payload
 */
export interface ContextPayload {
  /** Tipo di conversazione */
  conversation_type?: string

  /** Entity principale (ticker, asset_id, entity_id) */
  entities?: string[]

  /** Timestamp */
  timestamp?: string

  /** User ID (se autenticato) */
  user_id?: string | null

  /** Metadata addizionale */
  [key: string]: any
}

/**
 * Domain Extensions
 * 
 * Ogni verticale può estendere con payload custom
 * (es. advisor_recommendation, allocation_weights, portfolio_metrics)
 */
export interface DomainExtensions {
  [key: string]: any
}

/**
 * Validation Result
 */
export interface ValidationResult {
  valid: boolean
  errors: string[]
  warnings: string[]
}

/**
 * Type Guards
 */
export function isValidUIResponsePayload(payload: any): payload is UIResponsePayload {
  return (
    payload &&
    typeof payload === 'object' &&
    'narrative' in payload &&
    'followUps' in payload &&
    'evidence' in payload &&
    'vee_explanations' in payload &&
    'context' in payload
  )
}

export function isValidNarrativePayload(narrative: any): narrative is NarrativePayload {
  return narrative && typeof narrative === 'object' && typeof narrative.text === 'string'
}

export function isValidEvidencePayload(evidence: any): evidence is EvidencePayload {
  return evidence && typeof evidence === 'object' && Array.isArray(evidence.sections)
}
