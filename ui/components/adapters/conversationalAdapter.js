// adapters/conversationalAdapter.js
export const conversationalAdapter = {
  map(finalState) {
    const canResponse = finalState.can_response || {}
    const questions = finalState.questions || []

    return {
      narrative: {
        text: canResponse.narrative || questions[0] || "How can I help you?",
        tone: canResponse.mode === 'urgent' ? 'cautious' : 'neutral',
        recommendation: null
      },
      followUps: canResponse.follow_ups || [],
      context: {
        tickers: finalState.tickers || [],
        horizon: finalState.horizon || null,
        intent: finalState.intent || null,
        missingSlots: finalState.needed_slots || null
      },
      evidence: null  // Nessuna evidenza per query conversazionali
    }
  }
}