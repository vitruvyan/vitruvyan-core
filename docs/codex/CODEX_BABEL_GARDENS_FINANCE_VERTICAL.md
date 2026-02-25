# Codex Prompt — Babel Gardens Finance Vertical Implementation

> **Last updated**: Feb 23, 2026 16:00 UTC
> **Target**: ChatGPT 5.3 Codex (autonomous execution)
> **Workspace**: `/home/caravaggio/mercator`
> **Branch**: `main`

---

## MISSION

Implement the **finance vertical** for the Babel Gardens Sacred Order.
This is the **template approach** — the pattern established here will be replicated for all subsequent Sacred Orders (Pattern Weavers, Codex Hunters, Vault Keepers, Orthodoxy Wardens, Memory Orders).

The work consists of 4 deliverables:
1. **Finance Babel plugin package** (`vitruvyan_core/domains/finance/babel_gardens/`)
2. **Service plugin loader** in `services/api_babel_gardens/` to load finance vertical via config
3. **Updated API routes** to expose finance-specific endpoints conditionally
4. **Unit tests + validation**

---

## ARCHITECTURAL CONSTRAINTS (NON-NEGOTIABLE)

1. **LIVELLO 1 stays agnostic** — `vitruvyan_core/core/cognitive/babel_gardens/` is FROZEN. Do NOT modify any file there.
2. **Finance enters via plugins/config only** — through `vitruvyan_core/domains/finance/babel_gardens/` and `services/api_babel_gardens/plugins/`.
3. **Vertical Contract V1** — all artifacts must conform to `docs/contracts/verticals/VERTICAL_CONTRACT_V1.md`.
4. **LLM-first (Nuclear Option)** — sentiment/emotion analysis uses LLM as primary engine. FinBERT is a **domain signal extractor** (additional finance-specific signals), NOT a replacement for LLM sentiment.
5. **No cross-service imports** — finance plugins communicate with Sacred Orders via config injection, NOT by importing service internals.
6. **Agents for all I/O** — `PostgresAgent` for DB, `QdrantAgent` for vectors, `LLMAgent` for LLM calls. No raw clients.
7. **Environment-driven activation** — finance features activate when `BABEL_DOMAIN=finance` (default: `generic`).

---

## CURRENT STATE (What Already Exists)

### LIVELLO 1 — Pure Domain (FROZEN, do NOT modify)

Location: `vitruvyan_core/core/cognitive/babel_gardens/`

Key exports (from `__init__.py`):
- `BabelConfig`, `get_config`, `set_config`, `load_config_from_yaml`
- `TopicConfig`, `TopicCategory`
- `EmbeddingResult`, `SentimentResult`, `EmotionResult`, `ProcessingStatus`
- `SynthesisConsumer`, `TopicClassifierConsumer`, `LanguageDetectorConsumer`, `ProcessResult`
- `Channels`, `EventEnvelope`
- `MetricNames`, `HealthCheckNames`

Key domain primitives:
- `domain/signal_schema.py`: `SignalSchema`, `SignalExtractionResult`, `SignalConfig`, `load_config_from_yaml()`, `merge_configs()`
- `domain/entities.py`: Frozen dataclasses — `EmbeddingVector`, `EmbeddingResult`, `SentimentResult`, `EmotionResult`, `SynthesisRequest`, `SynthesisResult`
- `domain/config.py`: `BabelConfig` (master config), `TopicConfig` (YAML-loaded taxonomy), `EmbeddingModelConfig`, `SentimentModelConfig`, etc.
- `consumers/synthesis.py`: `SynthesisConsumer` — 4 fusion methods: concatenation, weighted_average, attention_fusion, semantic_garden_fusion
- `consumers/classifiers.py`: `TopicClassifierConsumer`, `LanguageDetectorConsumer`
- `events/__init__.py`: `Channels` (11 stream channel constants), `EventEnvelope`
- `examples/signals_finance.yaml`: 3 signals (sentiment_valence, market_fear_index, volatility_perception), taxonomy with 6 categories

### LIVELLO 2 — Service Layer

Location: `services/api_babel_gardens/`

Structure:
```
services/api_babel_gardens/
├── main.py                           # 87 lines, FastAPI bootstrap
├── config.py                         # 123 lines, centralized env vars
├── adapters/
│   ├── bus_adapter.py                # 128 lines, StreamBus orchestrator
│   ├── persistence.py                # 167 lines, PostgresAgent + QdrantAgent
│   └── embedding.py                  # 162 lines, httpx embedding adapter
├── api/
│   ├── routes_embeddings.py          # Embedding CRUD endpoints
│   ├── routes_admin.py               # Profile + Cognitive Bridge endpoints
│   ├── routes_emotion.py             # /v1/emotion/detect
│   └── routes_sentiment.py           # /v1/sentiment/analyze, /v1/sentiment/batch
├── modules/
│   ├── embedding_engine.py           # 788 lines, cooperative embedding with aiohttp
│   ├── sentiment_fusion.py           # 247 lines, LLM-first Nuclear Option
│   ├── emotion_detector.py           # 214 lines, LLM-first Nuclear Option
│   ├── profile_processor.py          # 609 lines, user behavioral profiles
│   ├── cognitive_bridge.py           # 644 lines, service routing + orchestration
│   └── embedding_engine_cooperative.py # Cooperative embedding variant
├── shared/
│   ├── base_service.py               # 177 lines, GemmaServiceBase
│   ├── model_manager.py              # 366 lines, UnifiedModelManager singleton
│   ├── vector_cache.py               # 498 lines, UnifiedVectorCache
│   └── integrity_watcher.py          # 549 lines, UnifiedIntegrityWatcher
├── schemas/
│   ├── __init__.py                   # Re-exports from api_models
│   └── api_models.py                 # 263 lines, 30+ Pydantic models
├── plugins/
│   ├── __init__.py                   # Conditional plugin loading
│   └── finance_signals.py            # 320 lines, FinBERT plugin (EXISTS)
├── streams_listener.py               # 71 lines, Redis Streams consumer
└── Dockerfile
```

### Existing Finance Plugin

`services/api_babel_gardens/plugins/finance_signals.py` (320 lines) — **ALREADY EXISTS**:
- `FinanceSignalsPlugin` class with lazy FinBERT loading (`ProsusAI/finbert`)
- `extract_sentiment_valence(text, schema) → SignalExtractionResult` (maps P(positive) - P(negative) to [-1, 1])
- `extract_market_fear_index(text, schema) → SignalExtractionResult` (P(negative) + 0.5 * P(neutral))
- `extract_signals(text, config) → List[SignalExtractionResult]` (batch extraction)
- Missing: `extract_volatility_perception` (3rd signal in YAML)
- Missing: Multi-model fusion (only has FinBERT, no gemma/multilingual integration)
- Missing: Sector resolution

### Existing Finance Domain

`vitruvyan_core/domains/finance/` — files present:
- `__init__.py` (exports ResponseFormatter + SlotFiller)
- `intent_config.py` (274L, 9 intents + 7 filters)
- `graph_plugin.py` (742L, FinanceGraphPlugin)
- `slot_filler.py` (352L, 5 slots, 4 languages)
- `response_formatter.py` (520L, verdict/gauge/matrix)
- `governance_rules.py` (90L, 16 MiFID/FINRA rules)
- `prompts/` (368L, 3 languages, 6 scenarios)
- `execution_config.py` (STUB)
- `entity_resolver_config.py` (STUB)
- No `babel_gardens/` subdirectory yet

### Pydantic Schemas (in `schemas/api_models.py`)

Finance fingerprint in current schemas:
- `ModelType.FINANCIAL` — default model type for embeddings
- `UserPreferences.risk_tolerance` — finance-origin field
- `FusionMode` enum (BASIC, ENHANCED, DEEP)
- No ticker-specific models

---

## UPSTREAM CODE TO PORT (Reference from vitruvyan)

### 1. Multi-Model Sentiment Fusion (`sentiment_fusion.py`, 758 lines)

The upstream vitruvyan has a `SentimentFusionModule` with multi-model weighted fusion:
- **Fusion weights**: `{"gemma": 0.45, "finbert": 0.35, "multilingual": 0.20}`
- **3 fusion modes**: BASIC (simple weighted), ENHANCED (language + domain boosting), DEEP (consensus analysis)
- **Language-aware boosting**: multilingual model × 1.3 for non-English, FinBERT × 1.2 for financial text
- **Cache-first pattern** with Redis
- **Batch processing** with semaphore (8 concurrent)
- **Calibration** with online learning of weights from feedback
- **3 model predictions**: `_get_gemma_prediction()`, `_get_finbert_prediction()`, `_get_multilingual_prediction()`

**What to port**: The multi-model fusion logic, enhanced/deep fusion with language boosting, calibration. 
**What NOT to port**: The raw model inference (mercator uses LLM-first for general sentiment; FinBERT is additional finance signal only).

### 2. Sector Resolver (`sector_resolver.py`, 238 lines)

Multilingual GICS sector resolution from `sector_mappings` PostgreSQL table:
- `resolve_sector(query_text, language) → {"db_sector", "gics_sector", "pattern_weaver_concept", "matched_alias", "matched_language", "confidence"}`
- JSONB query against `multilingual_aliases` column
- CJK bigram tokenization for Chinese/Japanese/Korean
- Stopword filtering for 4 languages
- `get_all_sectors_multilingual(language) → List[Dict]`

### 3. Model Manager Finance Config

FinBERT model configuration in upstream `model_manager.py`:
```python
"finbert": {
    "model_name": "ProsusAI/finbert",
    "type": "financial_sentiment",
    "max_length": 512,
    "batch_size": 16,
    "device": "cpu"
}
```
Already exists in mercator's `shared/model_manager.py`.

### 4. Financial Embedding Method

Upstream `embedding_engine.py` has `create_financial_embedding()` — uses cooperative API first, falls back to local. Model selection: `ModelType.FINANCIAL → "gemma_embeddings"`.
Already exists in mercator's `modules/embedding_engine.py`.

---

## IMPLEMENTATION PLAN

### DELIVERABLE 1: Finance Babel Plugin Package

**Create** `vitruvyan_core/domains/finance/babel_gardens/` with this structure:

```
vitruvyan_core/domains/finance/babel_gardens/
├── __init__.py
├── sentiment_config.py      # Finance-specific fusion weights + config
├── sector_resolver.py        # GICS sector resolution (ported from upstream)
├── volatility_lexicon.py     # Heuristic lexicon for volatility_perception signal
├── financial_context.py      # Financial context detector (is text financial?)
├── signals_finance.yaml      # Move from examples/ (canonical location)
└── README.md
```

#### File: `__init__.py`

```python
"""
Finance Vertical — Babel Gardens Integration
=============================================

Domain-specific signal extraction, sector resolution, and fusion configuration
for the finance vertical.

Loaded when BABEL_DOMAIN=finance.
"""

from .sentiment_config import (
    FinanceSentimentConfig,
    get_finance_fusion_weights,
    get_finance_model_boost,
)
from .financial_context import FinancialContextDetector
from .sector_resolver import SectorResolver

__all__ = [
    "FinanceSentimentConfig",
    "get_finance_fusion_weights",
    "get_finance_model_boost",
    "FinancialContextDetector",
    "SectorResolver",
]
```

#### File: `sentiment_config.py`

```python
"""
Finance Sentiment Configuration
================================

Finance-specific fusion weights, model boosting, and calibration config.
These override the agnostic defaults when BABEL_DOMAIN=finance.

Port from upstream vitruvyan SentimentFusionModule fusion logic.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass(frozen=True)
class FinanceSentimentConfig:
    """
    Finance-specific sentiment fusion configuration.
    
    Upstream origin: vitruvyan/core/babel_gardens/modules/sentiment_fusion.py
    Fusion weights from multi-model financial sentiment analysis.
    """
    
    # Multi-model fusion weights (must sum to 1.0)
    fusion_weights: Dict[str, float] = field(default_factory=lambda: {
        "llm": 0.45,        # LLM (primary, Nuclear Option) — was "gemma" upstream
        "finbert": 0.35,     # FinBERT (ProsusAI/finbert) — financial specialist
        "multilingual": 0.20,  # Multilingual model — cross-language support
    })
    
    # Language-aware model boosting factors
    # Non-English text → boost multilingual model weight
    multilingual_boost: float = 1.3
    # Financial text detected → boost FinBERT weight
    finbert_boost: float = 1.2
    
    # Confidence adjustments
    # Deep fusion: disagreement penalty (high disagreement → lower confidence)
    disagreement_penalty: float = 0.8
    # Deep fusion: agreement bonus (high agreement → boost confidence)
    agreement_bonus: float = 1.1
    # Confidence power for enhanced fusion (reduce impact of low confidence)
    confidence_power: float = 0.8
    
    # Calibration settings
    max_calibration_samples: int = 10000
    calibration_learning_rate: float = 0.01
    
    # FinBERT signal extraction config
    finbert_model: str = "ProsusAI/finbert"
    finbert_device: str = "cpu"
    finbert_max_length: int = 512
    finbert_batch_size: int = 16


def get_finance_fusion_weights() -> Dict[str, float]:
    """Get default finance fusion weights."""
    return FinanceSentimentConfig().fusion_weights


def get_finance_model_boost(language: str, is_financial: bool) -> Dict[str, float]:
    """
    Compute adjusted model weights based on language and content type.
    
    Port of upstream _enhanced_fusion weight adjustment logic.
    
    Args:
        language: ISO 639-1 language code
        is_financial: Whether text is detected as financial content
    
    Returns:
        Adjusted weights (normalized to sum to 1.0)
    """
    config = FinanceSentimentConfig()
    weights = dict(config.fusion_weights)
    
    # Boost multilingual for non-English
    if language != "en" and "multilingual" in weights:
        weights["multilingual"] *= config.multilingual_boost
    
    # Boost FinBERT for financial content
    if is_financial and "finbert" in weights:
        weights["finbert"] *= config.finbert_boost
    
    # Normalize to sum to 1.0
    total = sum(weights.values())
    if total > 0:
        weights = {k: v / total for k, v in weights.items()}
    
    return weights
```

#### File: `financial_context.py`

```python
"""
Financial Context Detector
===========================

Detects whether text is financial in nature, to enable:
- FinBERT weight boosting in fusion
- Finance-specific signal extraction
- Sector resolution triggering

Uses keyword detection as a fast classifier.
For ambiguous cases, defers to LLM (via LLMAgent).

Sacred Order: PERCEPTION
"""

import re
from typing import Dict, Any, Optional, Set


class FinancialContextDetector:
    """
    Detect financial context in text for model weight boosting.
    
    This detector determines IF text is financial (binary classification),
    NOT what the sentiment is (that's the model's job).
    """
    
    # Multilingual financial keywords (fast filter)
    FINANCIAL_TERMS: Dict[str, Set[str]] = {
        "en": {
            "market", "stock", "bond", "equity", "fund", "portfolio", "dividend",
            "earnings", "revenue", "profit", "loss", "trading", "investment",
            "hedge", "volatility", "bull", "bear", "IPO", "SEC", "Fed",
            "interest rate", "inflation", "GDP", "yield", "forex", "crypto",
            "bitcoin", "nasdaq", "dow jones", "s&p", "index", "futures",
            "options", "derivative", "commodity", "sector", "analyst",
        },
        "it": {
            "mercato", "borsa", "azioni", "titolo", "obbligazione", "fondo",
            "portafoglio", "dividendo", "utili", "ricavi", "profitto", "perdita",
            "trading", "investimento", "volatilità", "rialzo", "ribasso",
            "tasso", "inflazione", "PIL", "rendimento", "settore", "analista",
        },
        "es": {
            "mercado", "bolsa", "acciones", "bono", "fondo", "cartera",
            "dividendo", "ganancias", "ingresos", "inversión", "volatilidad",
            "tasa", "inflación", "PIB", "rendimiento", "sector",
        },
        "fr": {
            "marché", "bourse", "actions", "obligation", "fonds", "portefeuille",
            "dividende", "bénéfice", "investissement", "volatilité",
            "taux", "inflation", "PIB", "rendement", "secteur",
        },
        "de": {
            "markt", "börse", "aktien", "anleihe", "fonds", "portfolio",
            "dividende", "gewinn", "investition", "volatilität",
            "zinssatz", "inflation", "BIP", "rendite", "sektor",
        },
    }
    
    def __init__(self):
        """Initialize with flattened keyword set for fast lookup."""
        self._all_terms: Set[str] = set()
        for lang_terms in self.FINANCIAL_TERMS.values():
            self._all_terms.update(t.lower() for t in lang_terms)
    
    def is_financial(self, text: str, language: str = "auto") -> Dict[str, Any]:
        """
        Detect if text is financial in nature.
        
        Args:
            text: Input text to classify
            language: ISO 639-1 code or "auto"
        
        Returns:
            {
                "is_financial": bool,
                "confidence": float (0-1),
                "matched_terms": list of matched keywords,
                "language": str (detected or provided)
            }
        """
        text_lower = text.lower()
        
        # Get language-specific terms or all terms
        if language != "auto" and language in self.FINANCIAL_TERMS:
            terms = self.FINANCIAL_TERMS[language]
        else:
            terms = self._all_terms
        
        # Match terms
        matched = []
        for term in terms:
            if term in text_lower:
                matched.append(term)
        
        # Compute confidence based on match density
        words_count = max(len(text_lower.split()), 1)
        match_ratio = len(matched) / words_count
        
        # Threshold: at least 1 match with ratio > 0.02
        is_financial = len(matched) >= 1
        confidence = min(1.0, match_ratio * 10) if matched else 0.0
        
        return {
            "is_financial": is_financial,
            "confidence": round(confidence, 3),
            "matched_terms": matched[:10],  # Limit for response size
            "language": language,
        }
```

#### File: `sector_resolver.py`

```python
"""
Finance Sector Resolver — GICS Multilingual Resolution
=======================================================

Resolves sector queries from multilingual text using the
sector_mappings PostgreSQL table (JSONB multilingual_aliases).

Port from upstream vitruvyan/core/babel_gardens/sector_resolver.py (238L).

Sacred Order: PERCEPTION (Babel Gardens)
DB Table: sector_mappings (seeded in 002_seed_reference_data.sql)

Architecture:
- This is DOMAIN code (vitruvyan_core/domains/finance/babel_gardens/)
- It defines the LOGIC but does NOT instantiate PostgresAgent
- The PostgresAgent connection is injected by the service adapter
"""

import re
from typing import Dict, List, Optional, Any, Callable


class SectorResolver:
    """
    Resolve sector queries in 84 languages using multilingual_aliases JSONB.
    
    Examples:
        "tecnologia" (it) → Technology
        "salud" (es) → Healthcare
        "金融" (zh) → Financial Services
        "biotech" (en) → Healthcare
    
    Usage:
        resolver = SectorResolver(db_fetcher=pg_agent.fetch)
        result = resolver.resolve_sector("migliori biotech italiane", "it")
    """
    
    def __init__(self, db_fetcher: Callable):
        """
        Initialize with database query function (dependency injection).
        
        Args:
            db_fetcher: Callable that executes SQL and returns rows.
                        Signature: fetch(sql, params) -> List[Dict]
                        Example: PostgresAgent().fetch
        """
        self._fetch = db_fetcher
    
    def resolve_sector(self, query_text: str, detected_language: str = "auto") -> Optional[Dict[str, Any]]:
        """
        Resolve sector from multilingual query.
        
        Args:
            query_text: User query ("migliori biotech italiane", "tecnologia")
            detected_language: ISO 639-1 language code (auto = search all)
        
        Returns:
            {
                "db_sector": "Technology",
                "gics_sector": "Information Technology",
                "pattern_weaver_concept": "Tech Innovation",
                "matched_alias": "tecnologia",
                "matched_language": "it",
                "confidence": 0.95
            }
            or None if no match
        """
        keywords = self._extract_sector_keywords(query_text)
        
        for keyword in keywords:
            sector = self._query_sector_by_alias(keyword, detected_language)
            if sector:
                return sector
        
        # Fallback: lowercase
        for keyword in keywords:
            sector = self._query_sector_by_alias(keyword.lower(), detected_language)
            if sector:
                return sector
        
        return None
    
    def _extract_sector_keywords(self, text: str) -> List[str]:
        """
        Extract potential sector keywords from text.
        
        Handles:
        - Latin-script tokenization with stopword removal
        - CJK bigram tokenization for Chinese/Japanese/Korean
        """
        stopwords = {
            "il", "la", "i", "le", "di", "da", "a", "in", "per", "con", "su",
            "the", "and", "or", "of", "to", "in", "for", "on", "at", "is", "are",
            "el", "la", "los", "las", "de", "en", "y", "o", "del",
            "le", "les", "de", "et", "ou", "dans", "pour", "sur",
        }
        
        # CJK sequences
        cjk_sequences = re.findall(
            r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]+', text
        )
        
        # Latin-script words
        non_cjk_words = re.findall(r'[a-zA-ZÀ-ÿ]+', text.lower())
        
        keywords = []
        
        # CJK: extract bigrams
        for seq in cjk_sequences:
            if len(seq) <= 2:
                keywords.append(seq)
            else:
                for i in range(len(seq) - 1):
                    keywords.append(seq[i:i+2])
        
        # Latin: filter stopwords and short words
        for w in non_cjk_words:
            if w not in stopwords and len(w) >= 4:
                keywords.append(w)
        
        return keywords
    
    def _query_sector_by_alias(self, alias: str, language: str = "auto") -> Optional[Dict[str, Any]]:
        """
        Query sector_mappings by multilingual alias.
        
        Uses JSONB @> operator for efficient matching.
        """
        try:
            if language == "auto":
                rows = self._fetch(
                    """
                    SELECT db_sector, gics_sector, pattern_weaver_concept, multilingual_aliases
                    FROM sector_mappings
                    WHERE EXISTS (
                        SELECT 1 FROM jsonb_each(multilingual_aliases) AS lang
                        WHERE lang.value @> to_jsonb(ARRAY[%s]::text[])
                    )
                    LIMIT 1
                    """,
                    (alias,),
                )
            else:
                rows = self._fetch(
                    """
                    SELECT db_sector, gics_sector, pattern_weaver_concept, multilingual_aliases
                    FROM sector_mappings
                    WHERE multilingual_aliases -> %s @> to_jsonb(ARRAY[%s]::text[])
                    LIMIT 1
                    """,
                    (language, alias),
                )
            
            if not rows:
                return None
            
            row = rows[0]
            aliases_dict = row.get("multilingual_aliases", {})
            
            # Find which language matched
            matched_lang = None
            if isinstance(aliases_dict, dict):
                for lang, alias_list in aliases_dict.items():
                    if isinstance(alias_list, list) and alias in alias_list:
                        matched_lang = lang
                        break
            
            return {
                "db_sector": row.get("db_sector"),
                "gics_sector": row.get("gics_sector"),
                "pattern_weaver_concept": row.get("pattern_weaver_concept"),
                "matched_alias": alias,
                "matched_language": matched_lang or language,
                "confidence": 0.95 if matched_lang else 0.75,
            }
        
        except Exception:
            return None
    
    def get_all_sectors_multilingual(self, language: str = "en") -> List[Dict[str, Any]]:
        """
        Get all sectors with their aliases.
        
        Returns:
            List of {db_sector, gics_sector, aliases, languages_count}
        """
        try:
            rows = self._fetch(
                """
                SELECT db_sector, gics_sector, multilingual_aliases
                FROM sector_mappings
                WHERE multilingual_aliases IS NOT NULL
                ORDER BY db_sector
                """,
                (),
            )
            
            sectors = []
            for row in rows:
                aliases_dict = row.get("multilingual_aliases", {})
                all_aliases = []
                if isinstance(aliases_dict, dict):
                    for lang_aliases in aliases_dict.values():
                        if isinstance(lang_aliases, list):
                            all_aliases.extend(lang_aliases)
                
                sectors.append({
                    "db_sector": row.get("db_sector"),
                    "gics_sector": row.get("gics_sector"),
                    "aliases": all_aliases,
                    "languages_count": len(aliases_dict) if isinstance(aliases_dict, dict) else 0,
                })
            
            return sectors
        
        except Exception:
            return []
```

#### File: `volatility_lexicon.py`

```python
"""
Volatility Perception — Heuristic Lexicon Extractor
=====================================================

Implements the 3rd finance signal: volatility_perception [0, 1].
extraction_method: "heuristic:lexicon" (as defined in signals_finance.yaml).

This is the only signal NOT extracted via FinBERT model —
it uses keyword lexicon matching (acceptable for this signal type
as per the YAML config which explicitly declares heuristic:lexicon).

Sacred Order: PERCEPTION (Babel Gardens)
"""

import re
from typing import Dict, Any
from datetime import datetime, timezone

# LIVELLO 1 import (domain primitives only)
from core.cognitive.babel_gardens.domain.signal_schema import (
    SignalSchema,
    SignalExtractionResult,
)


# Multilingual volatility lexicon
VOLATILITY_LEXICON: Dict[str, Dict[str, float]] = {
    # English
    "volatile": 0.7, "volatility": 0.8, "turbulent": 0.7, "turbulence": 0.75,
    "crash": 0.95, "plunge": 0.9, "surge": 0.6, "spike": 0.65,
    "selloff": 0.85, "sell-off": 0.85, "panic": 0.9, "freefall": 0.95,
    "whipsaw": 0.8, "rollercoaster": 0.7, "correction": 0.6,
    "flash crash": 0.95, "circuit breaker": 0.9, "margin call": 0.85,
    "black swan": 0.95, "meltdown": 0.9, "contagion": 0.8,
    "uncertainty": 0.5, "unstable": 0.6, "erratic": 0.65,
    "swing": 0.5, "fluctuation": 0.55, "gyration": 0.6,
    # Italian
    "volatilità": 0.8, "crollo": 0.9, "turbolenza": 0.75,
    "panico": 0.9, "ribasso": 0.5, "oscillazione": 0.55,
    "instabile": 0.6, "incertezza": 0.5, "vendita massiva": 0.85,
    # Spanish
    "volatilidad": 0.8, "desplome": 0.9, "turbulencia": 0.75,
    "pánico": 0.9, "caída": 0.6, "oscilación": 0.55,
    # French
    "volatilité": 0.8, "effondrement": 0.9, "krach": 0.95,
    "panique": 0.9, "chute": 0.6,
    # German
    "Volatilität": 0.8, "Absturz": 0.9, "Panik": 0.9,
    "Einbruch": 0.85, "Schwankung": 0.55,
}


def extract_volatility_perception(text: str, schema: SignalSchema) -> SignalExtractionResult:
    """
    Extract volatility_perception signal [0, 1] from text.
    
    Method: Lexicon-based keyword matching with intensity scoring.
    Each matched term contributes its weight; final score is max(matched_weights).
    
    Args:
        text: Input text
        schema: SignalSchema for volatility_perception
    
    Returns:
        SignalExtractionResult with explainability trace
    """
    if schema.name != "volatility_perception":
        raise ValueError(f"Expected 'volatility_perception', got '{schema.name}'")
    
    text_lower = text.lower()
    matched_terms = {}
    
    for term, weight in VOLATILITY_LEXICON.items():
        if term.lower() in text_lower:
            matched_terms[term] = weight
    
    if matched_terms:
        # Use max weight as primary signal (worst-case volatility perception)
        raw_value = max(matched_terms.values())
        confidence = min(1.0, 0.3 + (len(matched_terms) * 0.15))
    else:
        raw_value = 0.0
        confidence = 0.1  # Low confidence — no signal detected
    
    normalized_value = schema.normalize_value(raw_value)
    
    extraction_trace = {
        "method": "heuristic:lexicon",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "matched_terms": matched_terms,
        "computation": f"max({list(matched_terms.values()) or [0.0]}) = {raw_value:.3f}",
        "lexicon_size": len(VOLATILITY_LEXICON),
    }
    
    return SignalExtractionResult(
        signal_name="volatility_perception",
        value=normalized_value,
        confidence=confidence,
        extraction_trace=extraction_trace,
        metadata={
            "text_length": len(text),
            "terms_matched": len(matched_terms),
        },
    )
```

#### File: `signals_finance.yaml`

Copy from `vitruvyan_core/core/cognitive/babel_gardens/examples/signals_finance.yaml` — this becomes the **canonical** config location for the finance vertical:

```yaml
# Finance Vertical - Signal Schema Configuration
# Babel Gardens v2.1 - Domain-Agnostic Signal Extraction
# Canonical location: vitruvyan_core/domains/finance/babel_gardens/signals_finance.yaml

signals:
  - name: sentiment_valence
    range: [-1.0, 1.0]
    aggregation_method: weighted
    fusion_weight: 0.8
    explainability_required: true
    extraction_method: "model:finbert"
    description: "Overall market sentiment polarity (positive/negative)"
  
  - name: market_fear_index
    range: [0.0, 1.0]
    aggregation_method: max
    fusion_weight: 0.6
    explainability_required: true
    extraction_method: "model:finbert"
    description: "Market stress and uncertainty indicator"
  
  - name: volatility_perception
    range: [0.0, 1.0]
    aggregation_method: mean
    fusion_weight: 0.5
    explainability_required: false
    extraction_method: "heuristic:lexicon"
    description: "Perceived market volatility from text signals"

taxonomy:
  categories:
    - earnings
    - macroeconomic
    - fed_policy
    - geopolitical
    - sector_rotation
    - market_structure
  
  embeddings:
    model: "sentence-transformers/all-MiniLM-L6-v2"
    dimension: 384

metadata:
  vertical: finance
  version: "2.1.0"
  created: "2026-02-11"
  contact: "babel-finance@vitruvyan.ai"
```

#### File: `README.md`

```markdown
# Finance Vertical — Babel Gardens Integration

> **Last updated**: Feb 23, 2026 16:00 UTC

## Purpose

Finance-specific signal extraction, sector resolution, and sentiment fusion
configuration for the Babel Gardens Sacred Order.

## Architecture

This package follows the **Vertical Contract V1** pattern:
- Domain code lives here (`vitruvyan_core/domains/finance/babel_gardens/`)
- Service integration via `services/api_babel_gardens/plugins/`
- Activated by `BABEL_DOMAIN=finance` environment variable

## Components

| File | Purpose |
|------|---------|
| `sentiment_config.py` | Multi-model fusion weights + language boosting |
| `sector_resolver.py` | GICS sector resolution via sector_mappings |
| `volatility_lexicon.py` | Heuristic lexicon for volatility_perception signal |
| `financial_context.py` | Financial content detection for model boosting |
| `signals_finance.yaml` | Canonical signal schema (3 signals, 6 taxonomy categories) |

## Signal Extraction

| Signal | Range | Method | Description |
|--------|-------|--------|-------------|
| `sentiment_valence` | [-1, 1] | model:finbert | Market sentiment polarity |
| `market_fear_index` | [0, 1] | model:finbert | Market stress indicator |
| `volatility_perception` | [0, 1] | heuristic:lexicon | Perceived volatility |

## Fusion Weights

| Model | Weight | Role |
|-------|--------|------|
| LLM (GPT-4o-mini) | 0.45 | Primary (Nuclear Option) — general sentiment |
| FinBERT | 0.35 | Finance specialist — domain-specific signals |
| Multilingual | 0.20 | Cross-language support |

## Usage

```python
from domains.finance.babel_gardens import FinanceSentimentConfig, SectorResolver
from domains.finance.babel_gardens.volatility_lexicon import extract_volatility_perception

# Get finance fusion weights
config = FinanceSentimentConfig()
weights = config.fusion_weights  # {"llm": 0.45, "finbert": 0.35, "multilingual": 0.20}

# Sector resolution (requires PostgresAgent)
from core.agents.postgres_agent import PostgresAgent
pg = PostgresAgent()
resolver = SectorResolver(db_fetcher=pg.fetch)
result = resolver.resolve_sector("migliori biotech italiane", "it")
# → {"db_sector": "Healthcare", "gics_sector": "Healthcare", ...}
```
```

---

### DELIVERABLE 2: Enhanced Finance Signals Plugin

**Modify** `services/api_babel_gardens/plugins/finance_signals.py` to add:
1. `extract_volatility_perception()` method using the lexicon
2. Integration with `FinanceSentimentConfig` for fusion weights
3. Full `extract_signals()` that handles all 3 signals

Add to the `FinanceSignalsPlugin` class:

```python
    def extract_volatility_perception(self, text: str, schema: SignalSchema) -> SignalExtractionResult:
        """Extract volatility_perception signal using lexicon heuristic."""
        from domains.finance.babel_gardens.volatility_lexicon import extract_volatility_perception
        return extract_volatility_perception(text, schema)
```

Update `extract_signals()` to dispatch volatility_perception:

```python
    def extract_signals(self, text: str, config: SignalConfig) -> List[SignalExtractionResult]:
        results = []
        for schema in config.signals:
            if schema.name == "sentiment_valence":
                results.append(self.extract_sentiment_valence(text, schema))
            elif schema.name == "market_fear_index":
                results.append(self.extract_market_fear_index(text, schema))
            elif schema.name == "volatility_perception":
                results.append(self.extract_volatility_perception(text, schema))
            else:
                logger.warning(f"Signal '{schema.name}' not implemented, skipping")
        return results
```

---

### DELIVERABLE 3: Service Plugin Loader

**Create** `services/api_babel_gardens/adapters/finance_adapter.py`:

```python
"""
Finance Vertical Adapter
=========================

Loads finance-specific components when BABEL_DOMAIN=finance.
Wires domain code (LIVELLO 1) with service infrastructure (LIVELLO 2).
"""

import logging
import os
from typing import Dict, Any, List, Optional

from ..config import get_config

logger = logging.getLogger(__name__)

_DOMAIN = os.getenv("BABEL_DOMAIN", "generic")


class FinanceAdapter:
    """
    Finance vertical adapter for Babel Gardens.
    
    Loaded only when BABEL_DOMAIN=finance.
    Provides:
    - Finance signal extraction (FinBERT + lexicon)
    - GICS sector resolution
    - Financial context detection
    - Finance-specific fusion weights
    """
    
    def __init__(self):
        self._signals_plugin = None
        self._sector_resolver = None
        self._context_detector = None
        self._sentiment_config = None
        self._signal_config = None
    
    @property
    def signals_plugin(self):
        """Lazy-load FinanceSignalsPlugin."""
        if self._signals_plugin is None:
            from ..plugins.finance_signals import FinanceSignalsPlugin
            self._signals_plugin = FinanceSignalsPlugin()
        return self._signals_plugin
    
    @property
    def sector_resolver(self):
        """Lazy-load SectorResolver with PostgresAgent."""
        if self._sector_resolver is None:
            from domains.finance.babel_gardens.sector_resolver import SectorResolver
            from ..adapters.persistence import get_persistence
            persistence = get_persistence()
            if persistence.pg_agent:
                self._sector_resolver = SectorResolver(
                    db_fetcher=persistence.pg_agent.fetch
                )
            else:
                logger.warning("⚠️ SectorResolver unavailable: no PostgresAgent")
        return self._sector_resolver
    
    @property
    def context_detector(self):
        """Lazy-load FinancialContextDetector."""
        if self._context_detector is None:
            from domains.finance.babel_gardens.financial_context import FinancialContextDetector
            self._context_detector = FinancialContextDetector()
        return self._context_detector
    
    @property
    def sentiment_config(self):
        """Lazy-load FinanceSentimentConfig."""
        if self._sentiment_config is None:
            from domains.finance.babel_gardens.sentiment_config import FinanceSentimentConfig
            self._sentiment_config = FinanceSentimentConfig()
        return self._sentiment_config
    
    @property
    def signal_config(self):
        """Lazy-load finance signal config from YAML."""
        if self._signal_config is None:
            from core.cognitive.babel_gardens.domain.signal_schema import load_config_from_yaml
            from pathlib import Path
            yaml_path = Path(__file__).resolve().parents[3] / (
                "vitruvyan_core/domains/finance/babel_gardens/signals_finance.yaml"
            )
            if yaml_path.exists():
                self._signal_config = load_config_from_yaml(str(yaml_path))
            else:
                logger.warning(f"⚠️ Finance signals YAML not found: {yaml_path}")
        return self._signal_config
    
    def extract_finance_signals(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract all finance signals from text.
        
        Returns list of signal dicts for API response.
        """
        if not self.signal_config:
            return []
        
        results = self.signals_plugin.extract_signals(text, self.signal_config)
        return [
            {
                "signal_name": r.signal_name,
                "value": r.value,
                "confidence": r.confidence,
                "extraction_trace": r.extraction_trace,
                "metadata": r.metadata,
            }
            for r in results
        ]
    
    def detect_financial_context(self, text: str, language: str = "auto") -> Dict[str, Any]:
        """Detect if text is financial content."""
        return self.context_detector.is_financial(text, language)
    
    def resolve_sector(self, query: str, language: str = "auto") -> Optional[Dict[str, Any]]:
        """Resolve sector from multilingual query."""
        if not self.sector_resolver:
            return None
        return self.sector_resolver.resolve_sector(query, language)
    
    def get_fusion_weights(self, language: str, text: str) -> Dict[str, float]:
        """Get adjusted fusion weights for text."""
        from domains.finance.babel_gardens.sentiment_config import get_finance_model_boost
        ctx = self.detect_financial_context(text, language)
        return get_finance_model_boost(language, ctx["is_financial"])


# ── Conditional singleton ──

_finance_adapter: Optional["FinanceAdapter"] = None


def get_finance_adapter() -> Optional["FinanceAdapter"]:
    """
    Get finance adapter if BABEL_DOMAIN=finance.
    Returns None for non-finance domains.
    """
    global _finance_adapter
    if _DOMAIN != "finance":
        return None
    if _finance_adapter is None:
        _finance_adapter = FinanceAdapter()
        logger.info("🏦 Finance vertical adapter loaded (BABEL_DOMAIN=finance)")
    return _finance_adapter


def is_finance_enabled() -> bool:
    """Check if finance vertical is active."""
    return _DOMAIN == "finance"
```

**Add** `services/api_babel_gardens/api/routes_finance.py`:

```python
"""
Finance Routes — Conditional endpoints for BABEL_DOMAIN=finance.

These routes are only registered when the finance vertical is active.
They provide finance-specific functionality on top of the agnostic Babel Gardens API.
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

from ..adapters.finance_adapter import get_finance_adapter, is_finance_enabled

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/finance", tags=["finance"])


# ── Request/Response models ──

class FinanceSignalsRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=8192, description="Text to analyze")
    language: str = Field(default="auto", description="ISO 639-1 code or 'auto'")


class FinanceSignalsResponse(BaseModel):
    status: str
    signals: List[Dict[str, Any]]
    context: Dict[str, Any]
    metadata: Dict[str, Any]


class SectorResolveRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2048, description="Sector query text")
    language: str = Field(default="auto", description="ISO 639-1 code or 'auto'")


class SectorResolveResponse(BaseModel):
    status: str
    sector: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class FinanceSentimentRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=8192)
    language: str = Field(default="auto")


# ── Endpoints ──

@router.post("/signals", response_model=FinanceSignalsResponse)
async def extract_finance_signals(request: FinanceSignalsRequest):
    """
    Extract finance-specific signals from text (FinBERT + lexicon).
    
    Returns sentiment_valence, market_fear_index, volatility_perception.
    Only available when BABEL_DOMAIN=finance.
    """
    adapter = get_finance_adapter()
    if adapter is None:
        raise HTTPException(status_code=404, detail="Finance vertical not enabled. Set BABEL_DOMAIN=finance")
    
    signals = adapter.extract_finance_signals(request.text)
    context = adapter.detect_financial_context(request.text, request.language)
    
    return FinanceSignalsResponse(
        status="success",
        signals=signals,
        context=context,
        metadata={
            "signals_count": len(signals),
            "language": request.language,
            "vertical": "finance",
        },
    )


@router.post("/sector/resolve", response_model=SectorResolveResponse)
async def resolve_sector(request: SectorResolveRequest):
    """
    Resolve GICS sector from multilingual text query.
    
    Uses sector_mappings PostgreSQL table with JSONB multilingual aliases.
    Only available when BABEL_DOMAIN=finance.
    """
    adapter = get_finance_adapter()
    if adapter is None:
        raise HTTPException(status_code=404, detail="Finance vertical not enabled")
    
    result = adapter.resolve_sector(request.query, request.language)
    
    if result:
        return SectorResolveResponse(status="success", sector=result)
    else:
        return SectorResolveResponse(
            status="not_found",
            error=f"No sector matched for query: {request.query}",
        )


@router.post("/sentiment/enhanced")
async def enhanced_finance_sentiment(request: FinanceSentimentRequest):
    """
    Finance-enhanced sentiment analysis.
    
    Combines:
    1. LLM-first sentiment (Nuclear Option) — from agnostic module
    2. FinBERT finance signals — from finance plugin
    3. Adjusted fusion weights (based on language + financial context)
    
    Only available when BABEL_DOMAIN=finance.
    """
    adapter = get_finance_adapter()
    if adapter is None:
        raise HTTPException(status_code=404, detail="Finance vertical not enabled")
    
    # 1. Get agnostic LLM sentiment
    from ..main import service
    if service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    llm_sentiment = await service.sentiment_fusion.analyze(
        text=request.text,
        language=request.language,
    )
    
    # 2. Get finance signals
    finance_signals = adapter.extract_finance_signals(request.text)
    
    # 3. Get context-adjusted fusion weights
    weights = adapter.get_fusion_weights(request.language, request.text)
    context = adapter.detect_financial_context(request.text, request.language)
    
    # 4. Build enhanced response
    return {
        "status": "success",
        "llm_sentiment": llm_sentiment,
        "finance_signals": finance_signals,
        "fusion_weights": weights,
        "financial_context": context,
        "enhanced": True,
        "vertical": "finance",
    }


@router.get("/config")
async def get_finance_config():
    """Get current finance vertical configuration."""
    adapter = get_finance_adapter()
    if adapter is None:
        raise HTTPException(status_code=404, detail="Finance vertical not enabled")
    
    config = adapter.sentiment_config
    return {
        "status": "success",
        "fusion_weights": dict(config.fusion_weights),
        "finbert_model": config.finbert_model,
        "finbert_device": config.finbert_device,
        "multilingual_boost": config.multilingual_boost,
        "finbert_boost": config.finbert_boost,
    }
```

**Modify** `services/api_babel_gardens/main.py` to conditionally register finance routes:

After the existing router includes, add:

```python
# ── Finance vertical (conditional on BABEL_DOMAIN=finance) ──
from .adapters.finance_adapter import is_finance_enabled
if is_finance_enabled():
    from .api.routes_finance import router as finance_router
    app.include_router(finance_router)
```

---

### DELIVERABLE 4: Unit Tests

**Create** `vitruvyan_core/domains/finance/babel_gardens/tests/` directory with:

#### `test_sentiment_config.py`

```python
"""Tests for finance sentiment configuration."""
import pytest
from domains.finance.babel_gardens.sentiment_config import (
    FinanceSentimentConfig,
    get_finance_fusion_weights,
    get_finance_model_boost,
)


def test_default_weights_sum_to_one():
    config = FinanceSentimentConfig()
    total = sum(config.fusion_weights.values())
    assert abs(total - 1.0) < 0.001


def test_get_finance_fusion_weights():
    weights = get_finance_fusion_weights()
    assert "llm" in weights
    assert "finbert" in weights
    assert "multilingual" in weights
    assert abs(sum(weights.values()) - 1.0) < 0.001


def test_model_boost_non_english():
    weights = get_finance_model_boost(language="it", is_financial=False)
    default = get_finance_fusion_weights()
    # Multilingual should be boosted for non-English
    assert weights["multilingual"] > default["multilingual"]


def test_model_boost_financial_content():
    weights = get_finance_model_boost(language="en", is_financial=True)
    default = get_finance_fusion_weights()
    # FinBERT should be boosted for financial content
    assert weights["finbert"] > default["finbert"]


def test_model_boost_both():
    weights = get_finance_model_boost(language="it", is_financial=True)
    # Both multilingual and finbert should be boosted
    assert sum(weights.values()) == pytest.approx(1.0, abs=0.001)


def test_model_boost_english_non_financial():
    weights = get_finance_model_boost(language="en", is_financial=False)
    default = get_finance_fusion_weights()
    # No boosts applied
    assert weights == default
```

#### `test_financial_context.py`

```python
"""Tests for financial context detection."""
import pytest
from domains.finance.babel_gardens.financial_context import FinancialContextDetector


@pytest.fixture
def detector():
    return FinancialContextDetector()


def test_financial_text_english(detector):
    result = detector.is_financial("The stock market rallied on earnings reports", "en")
    assert result["is_financial"] is True
    assert result["confidence"] > 0.0


def test_financial_text_italian(detector):
    result = detector.is_financial("Il mercato azionario è in rialzo", "it")
    assert result["is_financial"] is True


def test_non_financial_text(detector):
    result = detector.is_financial("The weather is nice today", "en")
    assert result["is_financial"] is False


def test_auto_language_detection(detector):
    result = detector.is_financial("La borsa di Milano ha chiuso in positivo", "auto")
    assert result["is_financial"] is True


def test_empty_text(detector):
    result = detector.is_financial("", "en")
    assert result["is_financial"] is False
```

#### `test_volatility_lexicon.py`

```python
"""Tests for volatility perception signal extraction."""
import pytest
from core.cognitive.babel_gardens.domain.signal_schema import SignalSchema
from domains.finance.babel_gardens.volatility_lexicon import (
    extract_volatility_perception,
    VOLATILITY_LEXICON,
)

SCHEMA = SignalSchema(
    name="volatility_perception",
    value_range=(0.0, 1.0),
    aggregation_method="mean",
    fusion_weight=0.5,
    extraction_method="heuristic:lexicon",
)


def test_high_volatility_text():
    result = extract_volatility_perception("Market crash and panic selling", SCHEMA)
    assert result.signal_name == "volatility_perception"
    assert result.value > 0.8
    assert result.confidence > 0.3


def test_no_volatility_text():
    result = extract_volatility_perception("The weather is sunny today", SCHEMA)
    assert result.value == 0.0
    assert result.confidence < 0.2


def test_moderate_volatility():
    result = extract_volatility_perception("Some market volatility expected", SCHEMA)
    assert 0.3 < result.value < 1.0


def test_italian_volatility():
    result = extract_volatility_perception("Crollo in borsa e panico tra gli investitori", SCHEMA)
    assert result.value > 0.8


def test_value_in_range():
    result = extract_volatility_perception("flash crash meltdown", SCHEMA)
    assert 0.0 <= result.value <= 1.0


def test_extraction_trace():
    result = extract_volatility_perception("Market volatility rising", SCHEMA)
    assert "method" in result.extraction_trace
    assert result.extraction_trace["method"] == "heuristic:lexicon"
    assert "timestamp" in result.extraction_trace


def test_wrong_schema_name():
    wrong_schema = SignalSchema(
        name="wrong_name",
        value_range=(0.0, 1.0),
        aggregation_method="mean",
    )
    with pytest.raises(ValueError):
        extract_volatility_perception("test", wrong_schema)
```

#### `test_sector_resolver.py`

```python
"""Tests for sector resolution (mocked DB)."""
import pytest
from domains.finance.babel_gardens.sector_resolver import SectorResolver


def _mock_fetcher_tech(sql, params):
    """Mock DB returning Technology sector."""
    return [{
        "db_sector": "Technology",
        "gics_sector": "Information Technology",
        "pattern_weaver_concept": "Tech Innovation",
        "multilingual_aliases": {
            "en": ["technology", "tech", "software"],
            "it": ["tecnologia", "informatica"],
            "es": ["tecnología", "informática"],
        },
    }]


def _mock_fetcher_empty(sql, params):
    """Mock DB returning no results."""
    return []


def test_resolve_english():
    resolver = SectorResolver(db_fetcher=_mock_fetcher_tech)
    result = resolver.resolve_sector("technology stocks", "en")
    assert result is not None
    assert result["db_sector"] == "Technology"


def test_resolve_italian():
    resolver = SectorResolver(db_fetcher=_mock_fetcher_tech)
    result = resolver.resolve_sector("settore tecnologia", "it")
    assert result is not None


def test_resolve_no_match():
    resolver = SectorResolver(db_fetcher=_mock_fetcher_empty)
    result = resolver.resolve_sector("xyz123", "en")
    assert result is None


def test_keyword_extraction():
    resolver = SectorResolver(db_fetcher=_mock_fetcher_empty)
    keywords = resolver._extract_sector_keywords("migliori biotech italiane")
    assert "biotech" in keywords
    assert "migliori" in keywords
    assert "italiane" in keywords
```

---

### DELIVERABLE 5: Integration with `services/api_babel_gardens/adapters/__init__.py`

**Modify** or **create** `services/api_babel_gardens/adapters/__init__.py` to export the finance adapter:

```python
"""Babel Gardens Adapters."""

from .bus_adapter import get_bus_adapter, BusAdapter
from .persistence import get_persistence, PersistenceAdapter
from .embedding import get_embedding_adapter, EmbeddingAdapter

# Finance vertical (conditional)
from .finance_adapter import get_finance_adapter, is_finance_enabled

__all__ = [
    "get_bus_adapter", "BusAdapter",
    "get_persistence", "PersistenceAdapter",
    "get_embedding_adapter", "EmbeddingAdapter",
    "get_finance_adapter", "is_finance_enabled",
]
```

---

## DOCKER CONFIGURATION

Add `BABEL_DOMAIN` env var to docker-compose for the babel service:

```yaml
mercator_babel_gardens:
  environment:
    - BABEL_DOMAIN=finance  # Activate finance vertical
```

---

## VALIDATION CHECKLIST

After implementation, verify:

- [ ] `python -c "from domains.finance.babel_gardens import FinanceSentimentConfig; print('✅')"` — imports work
- [ ] `python -c "from domains.finance.babel_gardens.sector_resolver import SectorResolver; print('✅')"` — sector resolver importable
- [ ] `python -c "from domains.finance.babel_gardens.volatility_lexicon import extract_volatility_perception; print('✅')"` — volatility lexicon importable
- [ ] `python -c "from domains.finance.babel_gardens.financial_context import FinancialContextDetector; print('✅')"` — context detector importable
- [ ] `pytest vitruvyan_core/domains/finance/babel_gardens/tests/ -v` — all unit tests pass
- [ ] LIVELLO 1 not modified: `git diff vitruvyan_core/core/cognitive/babel_gardens/` shows no changes
- [ ] Finance routes: `curl localhost:2009/v1/finance/signals -X POST -H "Content-Type: application/json" -d '{"text": "Fed signals rate hike"}'` → 200 with 3 signals
- [ ] Sector resolution: `curl localhost:2009/v1/finance/sector/resolve -X POST -H "Content-Type: application/json" -d '{"query": "tecnologia", "language": "it"}'` → Technology
- [ ] Enhanced sentiment: `curl localhost:2009/v1/finance/sentiment/enhanced -X POST -H "Content-Type: application/json" -d '{"text": "Markets crash on inflation fears"}'` → fused response
- [ ] Health check: `curl localhost:2009/health` → 200 with finance components
- [ ] Non-finance mode: Without `BABEL_DOMAIN=finance`, `/v1/finance/*` → 404

---

## FILE MANIFEST (Complete list of files to create/modify)

### CREATE (new files):
1. `vitruvyan_core/domains/finance/babel_gardens/__init__.py`
2. `vitruvyan_core/domains/finance/babel_gardens/sentiment_config.py`
3. `vitruvyan_core/domains/finance/babel_gardens/sector_resolver.py`
4. `vitruvyan_core/domains/finance/babel_gardens/volatility_lexicon.py`
5. `vitruvyan_core/domains/finance/babel_gardens/financial_context.py`
6. `vitruvyan_core/domains/finance/babel_gardens/signals_finance.yaml`
7. `vitruvyan_core/domains/finance/babel_gardens/README.md`
8. `vitruvyan_core/domains/finance/babel_gardens/tests/__init__.py`
9. `vitruvyan_core/domains/finance/babel_gardens/tests/test_sentiment_config.py`
10. `vitruvyan_core/domains/finance/babel_gardens/tests/test_financial_context.py`
11. `vitruvyan_core/domains/finance/babel_gardens/tests/test_volatility_lexicon.py`
12. `vitruvyan_core/domains/finance/babel_gardens/tests/test_sector_resolver.py`
13. `services/api_babel_gardens/adapters/finance_adapter.py`
14. `services/api_babel_gardens/api/routes_finance.py`

### MODIFY (existing files):
15. `services/api_babel_gardens/plugins/finance_signals.py` — add `extract_volatility_perception()` method
16. `services/api_babel_gardens/main.py` — conditionally register finance routes
17. `services/api_babel_gardens/adapters/__init__.py` — export finance adapter

### DO NOT MODIFY:
- `vitruvyan_core/core/cognitive/babel_gardens/*` — LIVELLO 1, FROZEN

---

## GIT COMMIT MESSAGE

```
feat(finance/babel): Finance vertical for Babel Gardens — template approach

DOMAIN LAYER (vitruvyan_core/domains/finance/babel_gardens/):
- sentiment_config.py: Multi-model fusion weights (LLM 0.45, FinBERT 0.35, Multilingual 0.20)
- sector_resolver.py: GICS sector resolution from sector_mappings (multilingual JSONB)
- volatility_lexicon.py: Heuristic lexicon for volatility_perception signal
- financial_context.py: Financial content detection for model weight boosting
- signals_finance.yaml: Canonical 3-signal + 6-category taxonomy config
- 4 unit test files (sentiment_config, financial_context, volatility_lexicon, sector_resolver)

SERVICE LAYER (services/api_babel_gardens/):
- adapters/finance_adapter.py: Conditional finance adapter (BABEL_DOMAIN=finance)
- api/routes_finance.py: /v1/finance/signals, /v1/finance/sector/resolve, /v1/finance/sentiment/enhanced
- plugins/finance_signals.py: Added extract_volatility_perception (3/3 signals)
- main.py: Conditional finance route registration

Architecture:
- LIVELLO 1 (core) UNCHANGED — finance enters via domain plugins only
- Vertical Contract V1 compliant
- LLM-first (Nuclear Option) for general sentiment; FinBERT for domain signals
- Environment-driven: BABEL_DOMAIN=finance activates all finance features

Template: This approach will be replicated for Pattern Weavers, Codex Hunters,
Vault Keepers, Orthodoxy Wardens, Memory Orders.
```
