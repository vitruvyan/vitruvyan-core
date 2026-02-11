# services/api_mcp/schemas/tools.py
"""OpenAI Function Calling compatible tool schemas."""

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "screen_entities",
            "description": "Screen entities using Vitruvyan Neural Engine multi-factor ranking system. Returns composite scores, normalized factor scores, and percentile ranks. Domain-agnostic: works with any entity type (assets, documents, users, products, etc.).",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of entity identifiers (e.g., ['entity_1', 'entity_2']). Max 10 entities per call. Entity type is deployment-configured.",
                        "minItems": 1,
                        "maxItems": 10
                    },
                    "profile": {
                        "type": "string",
                        "enum": ["balanced", "aggressive", "conservative", "custom"],
                        "description": "Scoring profile (factor weighting strategy). Default: balanced. Profiles are deployment-configured.",
                        "default": "balanced"
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
            "description": "Generate Vitruvyan Explainability Engine (VEE) narrative summary for an entity. Returns conversational explanation suitable for non-technical users. Domain-agnostic: explains scoring rationale for any entity type.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "Entity identifier (e.g., 'entity_1'). Entity type is deployment-configured."
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
            "name": "query_signals",
            "description": "Query signal scores from Vitruvyan database for an entity. Returns average signal values, trends, and sample context. Domain-agnostic: signals can be sentiment, quality, relevance, performance, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "Entity identifier (e.g., 'entity_1'). Entity type is deployment-configured."
                    },
                    "time_window": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 90,
                        "description": "Time window in days to look back. Default: 7",
                        "default": 7
                    },
                    "include_context": {
                        "type": "boolean",
                        "description": "Include sample context (phrases, events, metadata). Default: true",
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
            "description": "Compare multiple entities side-by-side using Vitruvyan comparison analysis. Returns ranking, classification, and factor deltas. Domain-agnostic: works with any entity type.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of entity identifiers to compare (e.g., ['entity_1', 'entity_2']). Min 2, max 5 entities.",
                        "minItems": 2,
                        "maxItems": 5
                    },
                    "criteria": {
                        "type": "string",
                        "enum": ["composite", "factor_1", "factor_2", "factor_3", "factor_4", "factor_5"],
                        "description": "Comparison criteria (factor name). Default: composite. Factor names are deployment-configured.",
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
