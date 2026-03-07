// ui/contracts/ChatContract.ts
// Chat Contract Interface — Vitruvyan Core
// Last updated: Feb 28, 2026

import { UIResponsePayload } from './UIContract'

/**
 * Chat Contract
 * 
 * Defines the domain-agnostic interface for the Chat module.
 * The Chat is infrastructure — it doesn't know what domain it serves.
 * 
 * Pattern:
 * - User types a message → ChatEngine.send(message, context)
 * - Backend returns LangGraph finalState
 * - Adapter transforms finalState → UIResponsePayload
 * - VitruvyanResponseRenderer renders the payload
 * 
 * The Chat module NEVER:
 * - Refers to tickers, stocks, portfolios, trading (domain concepts)
 * - Hardcodes entity types (entities are opaque strings)
 * - Contains domain-specific greeting text
 * - Imports domain-specific hooks or components
 * 
 * Inspired by: Vitruvyan Costituzione Art. II, X
 */

// ═══════════════════════════════════════════════════════════════
// MESSAGE TYPES
// ═══════════════════════════════════════════════════════════════

/**
 * A single chat message (user or AI)
 */
export interface ChatMessage {
  /** Unique message ID */
  id: string

  /** Who sent it */
  sender: 'user' | 'ai'

  /** Raw text content */
  text: string

  /** Backend final state (only for AI messages) */
  finalState?: Record<string, any> | null

  /** Adapted UI payload (only for AI messages, after adapter.map()) */
  uiPayload?: UIResponsePayload | null

  /** Is the response complete? */
  isComplete: boolean

  /** Error if something went wrong */
  error?: string | null

  /** Thinking steps (for streaming UX) */
  thinkingSteps?: ThinkingStep[]

  /** Is currently streaming? */
  isStreaming?: boolean

  /** Timestamp */
  timestamp: string

  /** Domain extensions (opaque to chat, used by domain plugins) */
  extensions?: Record<string, any>
}

/**
 * Thinking step shown during processing
 */
export interface ThinkingStep {
  /** Step ID (sequential) */
  id: number

  /** Icon (Unicode character or lucide-react name) */
  icon: string

  /** Step description */
  label: string

  /** Current status */
  status: 'pending' | 'active' | 'complete' | 'error'
}

// ═══════════════════════════════════════════════════════════════
// CHAT ENGINE CONTRACT
// ═══════════════════════════════════════════════════════════════

/**
 * Chat Engine Contract
 * 
 * Defines how the chat communicates with the backend.
 * Domain plugins can provide custom engine implementations.
 */
export interface ChatEngineContract {
  /**
   * Send a message to the backend
   * 
   * @param message - User's text input
   * @param context - Conversation context (entities, user_id, etc.)
   * @returns Backend response (LangGraph finalState)
   */
  send(message: string, context: ChatContext): Promise<ChatEngineResponse>

  /**
   * Send with streaming (optional)
   * Returns an async iterator of partial responses
   */
  sendStreaming?(
    message: string,
    context: ChatContext,
    onStep?: (step: ThinkingStep[]) => void
  ): Promise<ChatEngineResponse>

  /**
   * Health check
   */
  isHealthy?(): Promise<boolean>
}

/**
 * Chat Context — passed with every message
 * Domain-agnostic: entities are opaque strings, not "tickers"
 */
export interface ChatContext {
  /** User ID (from auth provider) */
  user_id?: string | null

  /** Session/conversation ID */
  session_id?: string

  /** Entities selected by the user (domain-agnostic) */
  entities?: string[]

  /** Domain extensions (opaque to chat engine) */
  [key: string]: any
}

/**
 * Response from the chat engine
 */
export interface ChatEngineResponse {
  /** The LangGraph final state */
  finalState: Record<string, any>

  /** Narrative text (convenience shortcut) */
  narrative?: string

  /** Was the response streamed? */
  streamed?: boolean
}

// ═══════════════════════════════════════════════════════════════
// CHAT INPUT CONTRACT
// ═══════════════════════════════════════════════════════════════

/**
 * Chat Input Contract
 * 
 * The input area is domain-agnostic.
 * - No "ticker pills" — generic "entity pills"
 * - No "Type a ticker or question" — generic placeholder
 * - No domain-specific autocomplete
 */
export interface ChatInputContract {
  /** Callback when user submits a message */
  onSend: (text: string, entities: string[]) => void

  /** Whether the AI is currently processing */
  isProcessing: boolean

  /** Currently selected entities (domain-agnostic) */
  selectedEntities?: string[]

  /** Callback to add an entity */
  onEntityAdd?: (entity: string) => void

  /** Callback to remove an entity */
  onEntityRemove?: (entity: string) => void

  /** Placeholder text (domain can override) */
  placeholder?: string

  /** Domain extensions (additional UI elements injected by domain plugin) */
  extensions?: ChatInputExtensions
}

/**
 * Extensions that domain plugins can inject into the input area
 */
export interface ChatInputExtensions {
  /** Custom autocomplete component */
  autocomplete?: any

  /** Extra action buttons (e.g., "Allocate" for finance) */
  actionButtons?: ChatActionButton[]

  /** Entity pill renderer (custom styling per domain) */
  entityPillRenderer?: (entity: string) => any
}

/**
 * Action button injected by domain plugin
 */
export interface ChatActionButton {
  /** Button ID */
  id: string

  /** Label */
  label: string

  /** Icon (lucide-react name) */
  icon?: string

  /** Callback */
  onClick: () => void

  /** Visibility condition */
  visible?: boolean
}

// ═══════════════════════════════════════════════════════════════
// CHAT MESSAGE DISPLAY CONTRACT
// ═══════════════════════════════════════════════════════════════

/**
 * Chat Message Display Contract
 * 
 * How a message is rendered. Domain-agnostic core:
 * - User bubble → text + optional entity pills
 * - AI bubble → VitruvyanResponseRenderer (via adapter)
 * - Processing → ThinkingSteps animation
 * - Error → FallbackMessage
 * 
 * Domain plugins can inject:
 * - Custom header (e.g., AnalysisHeader with ticker logos)
 * - Custom sidebar panels (e.g., portfolio banner)
 * - Custom post-response actions (e.g., trading bubble)
 */
export interface ChatMessageDisplayContract {
  /** The message to display */
  message: ChatMessage

  /** Callback when follow-up chip is clicked */
  onFollowUpClick?: (question: string) => void

  /** Callback when an entity is clicked (e.g., for drill-down) */
  onEntityClick?: (entity: string) => void

  /** Domain extensions for message display */
  extensions?: ChatMessageExtensions
}

/**
 * Extensions that domain plugins can inject into message display
 */
export interface ChatMessageExtensions {
  /** Component to render above the response (e.g., AnalysisHeader) */
  headerComponent?: any

  /** Component to render after the response (e.g., AdvisorInsight) */
  footerComponent?: any

  /** Sidebar panel (e.g., PortfolioBanner) */
  sidePanel?: any

  /** AI assistant name (default: "Vitruvyan") */
  assistantName?: string

  /** AI assistant icon */
  assistantIcon?: any
}

// ═══════════════════════════════════════════════════════════════
// THINKING STEPS PRESETS
// ═══════════════════════════════════════════════════════════════

/**
 * Default thinking steps (domain-agnostic)
 * Domain plugins can override with domain-specific steps
 */
export const DEFAULT_THINKING_STEPS: ThinkingStep[] = [
  { id: 1, icon: '◈', label: 'Parsing intent & context', status: 'pending' },
  { id: 2, icon: '⊕', label: 'Resolving entities', status: 'pending' },
  { id: 3, icon: '◉', label: 'Retrieving knowledge', status: 'pending' },
  { id: 4, icon: '△', label: 'Computing analysis', status: 'pending' },
  { id: 5, icon: '◆', label: 'Running cognitive engine', status: 'pending' },
  { id: 6, icon: '⬡', label: 'Generating narrative', status: 'pending' },
  { id: 7, icon: '⊞', label: 'Finalizing response', status: 'pending' }
]

// ═══════════════════════════════════════════════════════════════
// TYPE GUARDS
// ═══════════════════════════════════════════════════════════════

export function isValidChatMessage(msg: any): msg is ChatMessage {
  return (
    msg &&
    typeof msg === 'object' &&
    typeof msg.id === 'string' &&
    (msg.sender === 'user' || msg.sender === 'ai') &&
    typeof msg.text === 'string'
  )
}

export function isCompleteAIMessage(msg: ChatMessage): boolean {
  return msg.sender === 'ai' && msg.isComplete && !msg.error && !!msg.finalState
}

// ═══════════════════════════════════════════════════════════════
// MESSAGE FEEDBACK CONTRACT (Plasticity Integration)
// ═══════════════════════════════════════════════════════════════

/**
 * Feedback signal sent by the user on an AI message.
 * 
 * This is the UI-side contract for Plasticity integration.
 * When the user taps thumbs-up or thumbs-down, a FeedbackSignal
 * is sent to the backend, which records it as an Outcome in
 * OutcomeTracker for the learning loop.
 * 
 * Domain-agnostic: no knowledge of what the message contains.
 */
export type FeedbackValue = 'positive' | 'negative'

export interface FeedbackSignal {
  /** The message ID being rated */
  message_id: string

  /** trace_id from the backend finalState (links to CognitiveEvent chain) */
  trace_id?: string

  /** User's verdict */
  feedback: FeedbackValue

  /** Optional free-text correction/comment */
  comment?: string

  /** Timestamp (ISO 8601) */
  timestamp: string
}

/**
 * Feedback submission contract.
 * Implemented by useFeedback hook, consumed by ChatMessage component.
 */
export interface FeedbackContract {
  /** Submit feedback for a message */
  submit(signal: FeedbackSignal): Promise<void>

  /** Get current feedback state for a message (if already rated) */
  getFeedback(messageId: string): FeedbackValue | null
}
