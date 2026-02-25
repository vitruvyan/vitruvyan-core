/**
 * Intent Detection API Route
 * 
 * Uses GPT-4o-mini to detect user intent from natural language queries.
 * Optimized for speed (~100ms) with prompt caching.
 * 
 * Intents:
 * - portfolio_review: User wants to see their portfolio
 * - comparison: User wants to compare multiple tickers
 * - ticker_analysis: User wants analysis of specific ticker(s)
 * - general_question: General market/finance question
 */

import { NextResponse } from 'next/server'

const OPENAI_API_KEY = process.env.OPENAI_API_KEY

const SYSTEM_PROMPT = `You are an intent classifier for a financial analysis platform.

Detect user intent and return ONLY valid JSON:
{
  "intent": "portfolio_review" | "comparison" | "ticker_analysis" | "general_question",
  "confidence": 0.0-1.0,
  "tickers": ["AAPL", "MSFT"] // if mentioned explicitly
}

Intent Definitions:
- portfolio_review: User wants their portfolio analyzed ("my portfolio", "my investments", "holdings review")
- comparison: User wants to compare 2+ tickers ("compare AAPL vs MSFT", "SHOP vs PLTR")
- ticker_analysis: User wants single/multi ticker analysis ("analyze AAPL", "TSLA trend")
- general_question: Market questions, definitions, educational ("what is P/E ratio?")

Examples:
Query: "analyze my portfolio"
→ {"intent": "portfolio_review", "confidence": 0.95, "tickers": []}

Query: "come sta andando il mio investimento?"
→ {"intent": "portfolio_review", "confidence": 0.92, "tickers": []}

Query: "check my holdings"
→ {"intent": "portfolio_review", "confidence": 0.93, "tickers": []}

Query: "compare AAPL vs MSFT"
→ {"intent": "comparison", "confidence": 0.98, "tickers": ["AAPL", "MSFT"]}

Query: "SHOP vs PLTR quale scegliere?"
→ {"intent": "comparison", "confidence": 0.95, "tickers": ["SHOP", "PLTR"]}

Query: "analyze TSLA"
→ {"intent": "ticker_analysis", "confidence": 0.97, "tickers": ["TSLA"]}

Query: "what is market capitalization?"
→ {"intent": "general_question", "confidence": 0.90, "tickers": []}

Return ONLY the JSON object, no markdown, no explanation.`

export async function POST(request) {
  try {
    const { query } = await request.json()
    
    if (!query || query.trim().length === 0) {
      return NextResponse.json(
        { error: 'Query is required' },
        { status: 400 }
      )
    }
    
    console.log('[Intent API] Processing query:', query)
    
    // Call OpenAI GPT-4o-mini
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${OPENAI_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: 'gpt-4o-mini',
        messages: [
          {
            role: 'system',
            content: SYSTEM_PROMPT
          },
          {
            role: 'user',
            content: query
          }
        ],
        temperature: 0.1, // Low temperature for consistent classification
        max_tokens: 100,
        response_format: { type: "json_object" } // Force JSON response
      })
    })
    
    if (!response.ok) {
      const errorData = await response.json()
      console.error('[Intent API] OpenAI error:', errorData)
      throw new Error(`OpenAI API error: ${response.status}`)
    }
    
    const data = await response.json()
    const content = data.choices[0].message.content
    
    // Parse JSON response
    let result
    try {
      result = JSON.parse(content)
    } catch (parseError) {
      console.error('[Intent API] Failed to parse OpenAI response:', content)
      throw new Error('Invalid JSON response from LLM')
    }
    
    console.log('[Intent API] Detected intent:', result.intent, 'confidence:', result.confidence)
    
    return NextResponse.json({
      intent: result.intent,
      confidence: result.confidence || 0.0,
      tickers: result.tickers || [],
      cached: false // TODO: implement Redis caching
    })
    
  } catch (error) {
    console.error('[Intent API] Error:', error)
    
    // Fallback: Basic keyword matching
    const { query } = await request.json().catch(() => ({ query: '' }))
    const lowerQuery = query.toLowerCase()
    
    let fallbackIntent = 'general_question'
    let confidence = 0.5
    
    if (lowerQuery.includes('portfolio') || lowerQuery.includes('portafoglio') || 
        lowerQuery.includes('holdings') || lowerQuery.includes('investiment')) {
      fallbackIntent = 'portfolio_review'
      confidence = 0.7
    } else if (lowerQuery.includes('compare') || lowerQuery.includes('vs') || 
               lowerQuery.includes('versus') || lowerQuery.includes('confronta')) {
      fallbackIntent = 'comparison'
      confidence = 0.7
    }
    
    console.log('[Intent API] Fallback to keyword matching:', fallbackIntent)
    
    return NextResponse.json({
      intent: fallbackIntent,
      confidence: confidence,
      tickers: [],
      fallback: true,
      error: error.message
    })
  }
}
