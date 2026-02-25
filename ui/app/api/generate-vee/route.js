import OpenAI from 'openai';
import { NextResponse } from 'next/server';

// Lazy initialization to avoid build-time errors when OPENAI_API_KEY is not set
function getOpenAIClient() {
  return new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
  });
}

/**
 * POST /api/generate-vee
 * Generate VEE narrative using ChatGPT based on ticker data
 */
export async function POST(request) {
  try {
    const data = await request.json();
    const { ticker, momentum_z, trend_z, volatility_z, sentiment, composite_score, layer = 'beginner' } = data;

    // Build the prompt based on VEE specification
    const prompt = buildVeePrompt(ticker, momentum_z, trend_z, volatility_z, sentiment, composite_score, layer);

    console.log('[ChatGPT VEE] Generating for:', ticker, 'Layer:', layer);

    const openai = getOpenAIClient(); // Initialize only at runtime
    const response = await openai.chat.completions.create({
      model: 'gpt-4',
      messages: [
        {
          role: 'system',
          content: 'Sei un analista finanziario educativo. Fornisci analisi chiare e professionali in italiano. Non dare mai consigli di acquisto/vendita. Usa solo dati reali forniti.'
        },
        {
          role: 'user',
          content: prompt
        }
      ],
      temperature: 0.7,
      max_tokens: layer === 'beginner' ? 150 : layer === 'intermediate' ? 300 : 500,
    });

    const narrative = response.choices[0].message.content.trim();
    console.log('[ChatGPT VEE] ✅ Generated successfully');

    return NextResponse.json({ 
      narrative,
      ticker,
      layer,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('[ChatGPT VEE] ❌ Error:', error.message);
    return NextResponse.json(
      { error: 'Failed to generate VEE', details: error.message },
      { status: 500 }
    );
  }
}

/**
 * Build prompt based on VEE layer specification
 */
function buildVeePrompt(ticker, momentum_z, trend_z, volatility_z, sentiment, composite_score, layer) {
  // Helper to interpret z-scores
  const interpretZ = (z) => {
    if (z >= 1.5) return 'estremamente forte';
    if (z >= 0.5) return 'forte';
    if (z >= -0.5) return 'neutrale';
    if (z >= -1.5) return 'debole';
    return 'estremamente debole';
  };

  const momentumStr = interpretZ(momentum_z);
  const trendStr = interpretZ(trend_z);
  
  let volatilityStr;
  if (volatility_z >= 1.0) volatilityStr = 'elevata';
  else if (volatility_z >= -0.5) volatilityStr = 'normale';
  else volatilityStr = 'contenuta';

  const sentimentStr = sentiment > 0.2 ? 'positivo' : sentiment < -0.2 ? 'negativo' : 'neutrale';

  if (layer === 'beginner') {
    return `Analizza il ticker ${ticker} in modo semplice per un principiante.

Dati:
- Momentum: ${momentumStr} (z-score: ${momentum_z?.toFixed(2)})
- Trend: ${trendStr} (z-score: ${trend_z?.toFixed(2)})
- Volatilità: ${volatilityStr} (z-score: ${volatility_z?.toFixed(2)})
- Sentiment: ${sentimentStr} (valore: ${sentiment?.toFixed(2)})
- Composite Score: ${composite_score?.toFixed(2)}

Genera una spiegazione di 2-3 frasi semplici in italiano, senza tecnicismi.

Esempio: "Il titolo mostra momentum positivo, un trend forte e volatilità contenuta. Il sentiment è positivo. Il quadro complessivo è positivo."

Non inventare numeri. Usa solo i dati forniti.`;
  }

  if (layer === 'intermediate') {
    return `Analizza il ticker ${ticker} con tono educational analyst per un investitore intermedio.

Dati tecnici:
- Momentum z-score: ${momentum_z?.toFixed(2)} (${momentumStr})
- Trend z-score: ${trend_z?.toFixed(2)} (${trendStr})
- Volatilità z-score: ${volatility_z?.toFixed(2)} (${volatilityStr})
- Sentiment: ${sentiment?.toFixed(2)} (${sentimentStr})
- Composite Score: ${composite_score?.toFixed(2)}

Genera un'analisi educativa in italiano (4-5 frasi) che:
1. Spiega cosa significano gli z-scores in questo contesto
2. Identifica il fattore primario (quello con z-score più alto in valore assoluto)
3. Valuta il rischio (low/medium/high)
4. Fornisce esempi concreti

Non dare consigli di acquisto/vendita. Usa solo i dati forniti.`;
  }

  // Technical layer
  return `Analizza il ticker ${ticker} con linguaggio professionale/quantitativo per un analista tecnico.

Dati quantitativi:
- Momentum z-score: ${momentum_z?.toFixed(2)}
- Trend z-score: ${trend_z?.toFixed(2)}
- Volatilità z-score: ${volatility_z?.toFixed(2)}
- Sentiment: ${sentiment?.toFixed(2)}
- Composite Score: ${composite_score?.toFixed(2)}

Genera un'analisi tecnica in italiano (6-8 frasi) che include:
1. Breakdown dei fattori con interpretazione quantitativa
2. Primary driver (fattore con z-score più alto in valore assoluto)
3. Market regime (trend + volatilità)
4. Zone di entrata conservative/aggressive (solo educativo, non operativo)
5. Segnali di uscita safe/technical (solo educativo, non operativo)
6. Tabella interpretazione z-scores

Stile: Palantir/Victorian elegance - professionale, pulito, educativo.
Non dare consigli di acquisto/vendita. Usa solo i dati forniti.`;
}
