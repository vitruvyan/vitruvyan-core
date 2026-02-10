# services/api_mcp/schemas/tools.py
"""OpenAI Function Calling compatible tool schemas."""

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "screen_entities",
            "description": "Screen entity_ids using Vitruvyan Neural Engine multi-factor ranking system. Returns composite scores, z-scores for momentum/trend/volatility/sentiment/fundamentals, and percentile ranks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of entity entity_id symbols (e.g., ['EXAMPLE_ENTITY_1', 'EXAMPLE_ENTITY_2']). Max 10 entity_ids per call.",
                        "minItems": 1,
                        "maxItems": 10
                    },
                    "profile": {
                        "type": "string",
                        "enum": ["momentum_focus", "balanced_mid", "trend_follow", "short_spec", "sentiment_boost"],
                        "description": "Screening profile (weighting strategy). Default: balanced_mid",
                        "default": "balanced_mid"
                    },
                    "horizon": {
                        "type": "string",
                        "enum": ["short", "medium", "long"],
                        "description": "Investment horizon. Default: medium",
                        "default": "medium"
                    }
                },
                "required": ["entity_ids"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_vee_summary",
            "description": "Generate Vitruvyan Explainability Engine (VEE) narrative summary for a entity_id. Returns conversational explanation suitable for non-technical users.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "Entity entity_id symbol (e.g., 'EXAMPLE_ENTITY_1')"
                    },
                    "language": {
                        "type": "string",
                        "enum": ["it", "en"],
                        "description": "Output language. Default: it",
                        "default": "it"
                    }
                },
                "required": ["entity_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_sentiment",
            "description": "Query sentiment scores from Vitruvyan database for a entity_id. Returns average sentiment, trend, and recent sample phrases.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "Entity entity_id symbol (e.g., 'EXAMPLE_ENTITY_1')"
                    },
                    "days": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 30,
                        "description": "Number of days to look back. Default: 7",
                        "default": 7
                    },
                    "include_phrases": {
                        "type": "boolean",
                        "description": "Include sample sentiment phrases. Default: true",
                        "default": True
                    }
                },
                "required": ["entity_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "compare_entities",
            "description": "Compare multiple entity_ids side-by-side using Vitruvyan comparison analysis. Returns winner/loser classification and factor deltas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of entity_id symbols to compare (e.g., ['EXAMPLE_ENTITY_1', 'EXAMPLE_ENTITY_4', 'EXAMPLE_ENTITY_5']). Min 2, max 5 entity_ids.",
                        "minItems": 2,
                        "maxItems": 5
                    },
                    "criteria": {
                        "type": "string",
                        "enum": ["composite", "momentum", "trend", "volatility", "sentiment", "fundamentals"],
                        "description": "Comparison criteria. Default: composite",
                        "default": "composite"
                    }
                },
                "required": ["entity_ids"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "extract_semantic_context",
            "description": "Extract semantic context from user query using Pattern Weavers. Identifies concepts, sectors, regions, and risk profiles.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "User query text"
                    }
                },
                "required": ["query"]
            }
        }
    }
]
