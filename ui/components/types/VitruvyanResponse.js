/**
 * Modello canonico per tutte le risposte Vitruvyan
 * Ogni adapter deve produrre output conforme a questo schema
 */

export const VitruvyanResponseSchema = {
  // LAYER 1: Conversazione (sempre visibile)
  narrative: {
    text: "",              // String - La risposta testuale principale (REQUIRED)
    tone: "neutral",       // "neutral" | "cautious" | "confident" | "exploratory"
    recommendation: null   // { action: string, confidence: number } | null
  },

  followUps: [],           // String[] - Domande suggerite per continuare

  // LAYER 2: Contesto (metadata, non mostrato di default)
  context: {
    tickers: [],           // String[] - Ticker coinvolti
    horizon: null,         // "short" | "medium" | "long" | null
    intent: null,          // String - Per debug/logging, non UI
    missingSlots: null     // String[] | null - Se servono chiarimenti
  },

  // LAYER 3: Evidenza (collapsed by default)
  evidence: null           // { sections: EvidenceSection[] } | null
}

export const EvidenceSectionSchema = {
  id: "",                  // String - "metrics" | "chart" | "comparison" | "risk" | "vee"
  title: "",               // String - "Momentum Metrics", "Price Action", etc.
  priority: 1,             // Number - Ordine di visualizzazione
  defaultExpanded: false,  // Boolean - Primo elemento può essere true
  content: {
    type: "",              // "metrics" | "table" | "chart" | "text" | "radar"
    data: null             // Any - Dati specifici per il tipo
  }
}