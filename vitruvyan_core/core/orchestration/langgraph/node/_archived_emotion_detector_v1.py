"""
emotion_detector.py
===================

Emotional Intelligence Module for Vitruvyan - Phase 2.2 (P2)

Detects user emotional state from input text and provides adaptive
response strategies for empathetic AI interaction.

Emotions detected:
- anxious: User is worried, fearful, or risk-averse
- excited: User is enthusiastic, impulsive, or overconfident
- confused: User doesn't understand, needs clarification
- neutral: No strong emotion detected

The system uses:
1. Keyword pattern matching (multilingual: IT, EN, RU, SR)
2. Babel Gardens sentiment as signal boost
3. LLM fallback for complex cases

Integration points:
- compose_node: Adapt tone in clarifications
- cached_llm_node: Adapt system prompts
"""

from typing import Dict, Any, Tuple, Optional
import re


# Multilingual emotion keyword patterns
EMOTION_PATTERNS = {
    "anxious": {
        "it": [
            r"\b(paura|preoccupato|ansioso|timore|rischio|perdere|perdo|sbaglio|errore)\b",
            r"\b(sono|ho)\s+(molto\s+)?(spaventato|terrorizzato|nervoso)\b",
            r"\b(non\s+voglio|evitare)\s+(perdere|sbagliare|rischiare)\b",
            r"\b(troppo\s+)?(rischioso|pericoloso|volatile)\b"
        ],
        "en": [
            r"\b(fear|worry|worried|anxious|afraid|scared|nervous|risk|lose|losing|lose money)\b",
            r"\b(don't\s+want\s+to|avoid)\s+(lose|risk|fail)\b",
            r"\b(too\s+)?(risky|dangerous|volatile|scary)\b",
            r"\b(what\s+if\s+I|concerned\s+about)\b"
        ],
        "ru": [
            r"\b(боюсь|боюс|страх|тревога|опасаюсь|риск|потерять|потеря|ошибка)\b",
            r"\b(очень\s+)?(страшно|опасно|рискованно)\b",
            r"\b(не\s+хочу|избежать)\s+(потерять|рисковать)\b"
        ],
        "sr": [
            r"\b(strah|zabrinut|nervozan|rizik|gubiti|gubitak|greška)\b",
            r"\b(previše\s+)?(rizično|opasno)\b",
            r"\b(ne\s+želim|izbjeći)\s+(gubiti|riskirati)\b"
        ]
    },
    
    "excited": {
        "it": [
            r"\b(fantastico|incredibile|wow|ottimo|perfetto|eccellente|eccezionale)\b",
            r"\b(sono\s+)?eccitato|entusiasta|carico\b",
            r"\b(compro|investo)\s+(subito|ora|immediatamente)\b",
            r"\b(al\s+top|alle\s+stelle|boom|pump|moon)\b",
            r"[🚀🔥💎💰🎉⭐]+"  # Emojis
        ],
        "en": [
            r"\b(amazing|awesome|fantastic|wow|great|excellent|perfect|incredible)\b",
            r"\b(so\s+)?excited|pumped|hyped|bullish\b",
            r"\b(buy|invest)\s+(now|immediately|right away|asap)\b",
            r"\b(to\s+the\s+moon|all\s+in|yolo|pump|boom)\b",
            r"[🚀🔥💎💰🎉⭐]+"
        ],
        "ru": [
            r"\b(отлично|потрясающе|фантастика|вау|превосходно)\b",
            r"\b(возбужден|в восторге|взволнован)\b",
            r"\b(покупаю|инвестирую)\s+(сейчас|немедленно|прямо сейчас)\b",
            r"\b(на луну|бум|памп)\b",
            r"[🚀🔥💎💰🎉⭐]+"
        ],
        "sr": [
            r"\b(odlično|neverovatno|fantastično|vau|savršeno)\b",
            r"\b(uzbuđen|oduševljen)\b",
            r"\b(kupujem|investiram)\s+(sada|odmah)\b",
            r"[🚀🔥💎💰🎉⭐]+"
        ]
    },
    
    "confused": {
        "it": [
            r"\b(non\s+capisco|confuso|complicato|difficile|non\s+so|aiuto|help)\b",
            r"\b(come\s+funziona|cosa\s+significa|spiegami|chiarimento)\b",
            r"\b(troppo\s+)?(complesso|tecnico|difficile\s+da\s+capire)\b",
            r"\?\s*\?+|cosa\?|come\?|perché\?"
        ],
        "en": [
            r"\b(don't\s+understand|confused|complicated|difficult|don't\s+know|help|lost)\b",
            r"\b(how\s+does|what\s+does|explain|clarify|unclear)\b",
            r"\b(too\s+)?(complex|technical|hard\s+to\s+understand)\b",
            r"\?\s*\?+|what\?|how\?|why\?"
        ],
        "ru": [
            r"\b(не\s+понимаю|запутан|сложно|трудно|не\s+знаю|помощь)\b",
            r"\b(как\s+работает|что\s+значит|объясни|непонятно)\b",
            r"\b(слишком\s+)?(сложный|технический)\b"
        ],
        "sr": [
            r"\b(ne\s+razumem|zbunjen|komplikovano|teško|ne\s+znam|pomoć)\b",
            r"\b(kako\s+funkcioniše|šta\s+znači|objasni)\b",
            r"\b(previše\s+)?(složeno|tehnički)\b"
        ]
    }
}


# Emotion-specific response adaptations
EMOTION_ADAPTATIONS = {
    "anxious": {
        "it": {
            "tone": "reassuring",
            "prefix": "Capisco la tua preoccupazione. ",
            "strategy": "Fornire analisi del rischio dettagliata, evidenziare protezioni, suggerire approccio conservativo.",
            "keywords": ["sicurezza", "protezione", "graduale", "prudente", "diversificazione"],
            "avoid": ["rischio elevato", "aggressivo", "speculativo"],
            "suggestions": [
                "Considera un approccio graduale con stop-loss",
                "Diversifica per ridurre il rischio",
                "Inizia con posizioni piccole per prendere confidenza"
            ]
        },
        "en": {
            "tone": "reassuring",
            "prefix": "I understand your concern. ",
            "strategy": "Provide detailed risk analysis, highlight protections, suggest conservative approach.",
            "keywords": ["safety", "protection", "gradual", "prudent", "diversification"],
            "avoid": ["high risk", "aggressive", "speculative"],
            "suggestions": [
                "Consider a gradual approach with stop-loss",
                "Diversify to reduce risk",
                "Start with small positions to gain confidence"
            ]
        },
        "ru": {
            "tone": "reassuring",
            "prefix": "Я понимаю ваше беспокойство. ",
            "strategy": "Предоставить детальный анализ рисков, выделить защиту, предложить консервативный подход.",
            "keywords": ["безопасность", "защита", "постепенный", "осторожный", "диверсификация"],
            "avoid": ["высокий риск", "агрессивный", "спекулятивный"]
        },
        "sr": {
            "tone": "reassuring",
            "prefix": "Razumem vašu zabrinutost. ",
            "strategy": "Pružiti detaljnu analizu rizika, istaći zaštitu, predložiti konzervativan pristup.",
            "keywords": ["sigurnost", "zaštita", "postepen", "oprezan", "diverzifikacija"],
            "avoid": ["visok rizik", "agresivan", "spekulativan"]
        }
    },
    
    "excited": {
        "it": {
            "tone": "cautious_balancing",
            "prefix": "È bello vedere il tuo entusiasmo! Però, ",
            "strategy": "Bilanciare l'entusiasmo con cautela, evidenziare rischi anche negli asset promettenti, frenare impulsi.",
            "keywords": ["valuta attentamente", "analisi obiettiva", "non solo i pro", "anche i rischi"],
            "avoid": ["garantito", "sicuro al 100%", "non può perdere"],
            "suggestions": [
                "Prima di investire, rivediamo insieme i rischi",
                "L'entusiasmo è positivo, ma serve un piano razionale",
                "Considera anche scenari negativi prima di decidere"
            ]
        },
        "en": {
            "tone": "cautious_balancing",
            "prefix": "Great to see your enthusiasm! However, ",
            "strategy": "Balance enthusiasm with caution, highlight risks even in promising assets, curb impulses.",
            "keywords": ["evaluate carefully", "objective analysis", "not just the pros", "also the risks"],
            "avoid": ["guaranteed", "100% safe", "can't lose"],
            "suggestions": [
                "Before investing, let's review the risks together",
                "Enthusiasm is positive, but we need a rational plan",
                "Consider negative scenarios before deciding"
            ]
        },
        "ru": {
            "tone": "cautious_balancing",
            "prefix": "Приятно видеть ваш энтузиазм! Однако, ",
            "strategy": "Сбалансировать энтузиазм с осторожностью, выделить риски даже в перспективных активах.",
            "keywords": ["тщательно оцените", "объективный анализ", "не только плюсы", "также риски"],
            "avoid": ["гарантированный", "100% безопасно", "не может потерять"]
        },
        "sr": {
            "tone": "cautious_balancing",
            "prefix": "Divno je videti vaš entuzijazam! Međutim, ",
            "strategy": "Balansirati entuzijazam sa oprezom, istaći rizike čak i u obećavajućim aktivama.",
            "keywords": ["pažljivo procenite", "objektivna analiza", "ne samo prednosti", "takođe rizici"],
            "avoid": ["garantovano", "100% sigurno", "ne može izgubiti"]
        }
    },
    
    "confused": {
        "it": {
            "tone": "educational_patient",
            "prefix": "Nessun problema, ti spiego passo per passo. ",
            "strategy": "Fornire spiegazioni semplici, usare analogie, evitare gergo tecnico, chiedere conferma di comprensione.",
            "keywords": ["in parole semplici", "passo per passo", "per esempio", "ti è chiaro?"],
            "avoid": ["ovviamente", "come sai", "tecnicamente parlando"],
            "suggestions": [
                "Fammi sapere se qualcosa non è chiaro",
                "Posso spiegare con un esempio concreto",
                "Procediamo un passo alla volta"
            ]
        },
        "en": {
            "tone": "educational_patient",
            "prefix": "No problem, let me explain step by step. ",
            "strategy": "Provide simple explanations, use analogies, avoid technical jargon, ask for comprehension confirmation.",
            "keywords": ["in simple terms", "step by step", "for example", "does that make sense?"],
            "avoid": ["obviously", "as you know", "technically speaking"],
            "suggestions": [
                "Let me know if anything isn't clear",
                "I can explain with a concrete example",
                "Let's go one step at a time"
            ]
        },
        "ru": {
            "tone": "educational_patient",
            "prefix": "Нет проблем, объясню пошагово. ",
            "strategy": "Предоставить простые объяснения, использовать аналогии, избегать технического жаргона.",
            "keywords": ["простыми словами", "шаг за шагом", "например", "понятно?"],
            "avoid": ["очевидно", "как вы знаете", "технически говоря"]
        },
        "sr": {
            "tone": "educational_patient",
            "prefix": "Nema problema, objasniću korak po korak. ",
            "strategy": "Pružiti jednostavna objašnjenja, koristiti analogije, izbegavati tehnički žargon.",
            "keywords": ["jednostavnim rečima", "korak po korak", "na primer", "razumete?"],
            "avoid": ["očigledno", "kako znate", "tehnički govoreći"]
        }
    },
    
    "neutral": {
        "it": {
            "tone": "professional_friendly",
            "prefix": "",
            "strategy": "Tono professionale ma amichevole, equilibrato, focalizzato sui fatti.",
            "keywords": ["analisi", "dati", "considerando", "suggerisco"],
            "avoid": []
        },
        "en": {
            "tone": "professional_friendly",
            "prefix": "",
            "strategy": "Professional but friendly tone, balanced, fact-focused.",
            "keywords": ["analysis", "data", "considering", "I suggest"],
            "avoid": []
        },
        "ru": {
            "tone": "professional_friendly",
            "prefix": "",
            "strategy": "Профессиональный, но дружелюбный тон, сбалансированный, ориентированный на факты.",
            "keywords": ["анализ", "данные", "учитывая", "предлагаю"],
            "avoid": []
        },
        "sr": {
            "tone": "professional_friendly",
            "prefix": "",
            "strategy": "Profesionalan ali prijateljski ton, uravnotežen, fokusiran na činjenice.",
            "keywords": ["analiza", "podaci", "uzimajući u obzir", "predlažem"],
            "avoid": []
        }
    }
}


def detect_emotion(
    user_input: str,
    language: str = "it",
    babel_sentiment: Optional[Dict[str, Any]] = None
) -> Tuple[str, float]:
    """
    Detect user emotional state from input text
    
    Args:
        user_input: User's text input
        language: Detected language (it, en, ru, sr)
        babel_sentiment: Optional sentiment from Babel Gardens
    
    Returns:
        Tuple of (emotion_label, confidence_score)
        - emotion_label: 'anxious', 'excited', 'confused', 'neutral'
        - confidence_score: 0.0 to 1.0
    """
    
    user_input_lower = user_input.lower()
    
    # Score each emotion
    emotion_scores = {
        "anxious": 0.0,
        "excited": 0.0,
        "confused": 0.0
    }
    
    # Pattern matching for each emotion
    for emotion, patterns_by_lang in EMOTION_PATTERNS.items():
        if language in patterns_by_lang:
            patterns = patterns_by_lang[language]
            
            for pattern in patterns:
                matches = re.findall(pattern, user_input_lower, re.IGNORECASE)
                if matches:
                    # Base score from pattern match
                    emotion_scores[emotion] += 0.3 * len(matches)
    
    # Boost from Babel Gardens sentiment (if available)
    if babel_sentiment:
        sentiment_label = babel_sentiment.get("sentiment_label", "neutral")
        sentiment_score = babel_sentiment.get("sentiment_score", 0.0)
        
        # Map Babel sentiment to emotions
        if sentiment_label in ["negative", "fear"]:
            emotion_scores["anxious"] += 0.2 * abs(sentiment_score)
        elif sentiment_label in ["positive", "joy"]:
            emotion_scores["excited"] += 0.2 * sentiment_score
    
    # Normalize scores to max 1.0
    max_score = max(emotion_scores.values()) if emotion_scores else 0.0
    
    if max_score > 0:
        for emotion in emotion_scores:
            emotion_scores[emotion] = min(1.0, emotion_scores[emotion])
    
    # Determine winner (threshold: 0.25)
    winner = "neutral"
    winner_score = 0.0
    
    for emotion, score in emotion_scores.items():
        if score >= 0.25 and score > winner_score:
            winner = emotion
            winner_score = score
    
    return winner, winner_score


def get_emotion_adaptation(
    emotion: str,
    language: str = "it"
) -> Dict[str, Any]:
    """
    Get response adaptation strategy for detected emotion
    
    Args:
        emotion: Detected emotion ('anxious', 'excited', 'confused', 'neutral')
        language: Response language
    
    Returns:
        Dict with adaptation strategy:
        - tone: How to speak
        - prefix: Optional prefix for response
        - strategy: High-level adaptation strategy
        - keywords: Words to emphasize
        - avoid: Words/phrases to avoid
        - suggestions: Optional suggestions list
    """
    
    if emotion not in EMOTION_ADAPTATIONS:
        emotion = "neutral"
    
    if language not in EMOTION_ADAPTATIONS[emotion]:
        language = "it"  # Fallback to Italian
    
    return EMOTION_ADAPTATIONS[emotion][language]


def format_emotion_aware_response(
    base_response: str,
    emotion: str,
    language: str = "it",
    add_prefix: bool = True
) -> str:
    """
    Format a response with emotion-aware adaptations
    
    Args:
        base_response: Original response text
        emotion: Detected emotion
        language: Response language
        add_prefix: Whether to add emotion-specific prefix
    
    Returns:
        Adapted response text
    """
    
    adaptation = get_emotion_adaptation(emotion, language)
    
    # Add prefix if requested and available
    if add_prefix and adaptation.get("prefix"):
        response = adaptation["prefix"] + base_response
    else:
        response = base_response
    
    # Add suggestions if emotion is anxious or confused
    if emotion in ["anxious", "confused"] and "suggestions" in adaptation:
        suggestions = adaptation["suggestions"]
        if suggestions and len(response) < 500:  # Only if response isn't too long
            response += "\n\n💡 Suggerimenti:\n"
            for i, sug in enumerate(suggestions[:2], 1):  # Max 2 suggestions
                response += f"  {i}. {sug}\n"
    
    return response


def get_emotion_system_prompt_fragment(
    emotion: str,
    language: str = "it"
) -> str:
    """
    Get system prompt fragment for LLM based on detected emotion
    
    Used in cached_llm_node to adapt LLM behavior
    
    Args:
        emotion: Detected emotion
        language: Language for instructions
    
    Returns:
        System prompt fragment to inject
    """
    
    adaptation = get_emotion_adaptation(emotion, language)
    
    fragments = {
        "it": {
            "anxious": """
IMPORTANTE - UTENTE ANSIOSO RILEVATO:
L'utente mostra preoccupazione e ansia riguardo agli investimenti.
- Usa un tono rassicurante e empatico
- Fornisci analisi dettagliata dei rischi con spiegazione delle protezioni
- Suggerisci approcci conservativi e graduali
- Evidenzia diversificazione e gestione del rischio
- EVITA di enfatizzare opportunità ad alto rischio
""",
            "excited": """
IMPORTANTE - UTENTE ENTUSIASTA RILEVATO:
L'utente mostra forte entusiasmo, possibile impulsività.
- Bilancia l'entusiasmo con cautela professionale
- Evidenzia ANCHE i rischi, non solo i potenziali guadagni
- Modera l'euforia con analisi obiettiva
- Suggerisci di considerare scenari negativi
- EVITA di alimentare l'impulso di investimento immediato
""",
            "confused": """
IMPORTANTE - UTENTE CONFUSO RILEVATO:
L'utente non comprende chiaramente il contesto o i concetti.
- Spiega in modo semplice e chiaro, senza gergo tecnico
- Usa analogie ed esempi concreti
- Procedi passo per passo nelle spiegazioni
- Chiedi conferma di comprensione
- EVITA di dare per scontato conoscenze tecniche
""",
            "neutral": ""
        },
        "en": {
            "anxious": """
IMPORTANT - ANXIOUS USER DETECTED:
User shows concern and anxiety about investments.
- Use reassuring and empathetic tone
- Provide detailed risk analysis with protection explanations
- Suggest conservative and gradual approaches
- Highlight diversification and risk management
- AVOID emphasizing high-risk opportunities
""",
            "excited": """
IMPORTANT - EXCITED USER DETECTED:
User shows strong enthusiasm, possible impulsivity.
- Balance enthusiasm with professional caution
- Highlight ALSO the risks, not just potential gains
- Moderate euphoria with objective analysis
- Suggest considering negative scenarios
- AVOID fueling immediate investment impulse
""",
            "confused": """
IMPORTANT - CONFUSED USER DETECTED:
User doesn't clearly understand context or concepts.
- Explain simply and clearly, without technical jargon
- Use analogies and concrete examples
- Proceed step by step in explanations
- Ask for comprehension confirmation
- AVOID assuming technical knowledge
""",
            "neutral": ""
        }
    }
    
    if language not in fragments:
        language = "it"
    
    return fragments[language].get(emotion, "")


# Quick test function
def _test_emotion_detection():
    """Test emotion detection with sample inputs"""
    
    test_cases = [
        ("Ho molta paura di perdere soldi", "it", "anxious"),
        ("Wow, NVDA è fantastico! 🚀 Compro subito!", "it", "excited"),
        ("Non capisco come funziona il momentum", "it", "confused"),
        ("Analizza AAPL per favore", "it", "neutral"),
        ("I'm worried about the market volatility", "en", "anxious"),
        ("This is amazing! Let's go all in! 🔥", "en", "excited"),
        ("I don't understand what RSI means", "en", "confused"),
    ]
    
    print("\n🧪 Emotion Detection Tests:\n")
    for text, lang, expected in test_cases:
        emotion, confidence = detect_emotion(text, lang)
        status = "✅" if emotion == expected else "❌"
        print(f"{status} '{text[:50]}...'")
        print(f"   Detected: {emotion} (conf: {confidence:.2f}) | Expected: {expected}\n")


if __name__ == "__main__":
    _test_emotion_detection()
