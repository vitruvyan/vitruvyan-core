"""
    Chronicle The Sacred Lexicon of the Synaptic Conclave
Schema definitions for semantic communication

The Lexicon defines the sacred language that all Orders use
to communicate through the Conclave Heart.
"""
    
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import json
import os


class SemanticEvent(BaseModel):
    """
    Base model for all semantic events in the sacred language.
    Format: domain.intent.payload
    """
    domain: str = Field(..., description="Sacred Order domain")
    intent: str = Field(..., description="Specific intent within domain")
    payload: Dict[str, Any] = Field(..., description="Event data")
    timestamp: str = Field(..., description="ISO timestamp")
    source: str = Field(..., description="Source of the event")
    event_id: str = Field(..., description="Unique event identifier")


class DomainSchema(BaseModel):
    """
    Schema definition for a Sacred Order domain.
    """
    domain: str
    description: str
    intents: Dict[str, Dict[str, Any]]
    payload_schemas: Dict[str, Dict[str, Any]]


class SacredLexicon:
    """
    The Sacred Lexicon manages semantic schemas for all Orders.
    """
    
    def __init__(self, schema_path: str = "core/synaptic_conclave/scroll_of_bonds.json"):
        self.schema_path = schema_path
        self.domains: Dict[str, DomainSchema] = {}
        self._load_schemas()
    
    def _load_schemas(self):
        """
        Load schemas from the Scroll of Sacred Bonds.
        """
        if os.path.exists(self.schema_path):
            try:
                with open(self.schema_path, 'r') as f:
                    schema_data = json.load(f)
                
                for domain_name, domain_data in schema_data.get("domains", {}).items():
                    self.domains[domain_name] = DomainSchema(
                        domain=domain_name,
                        **domain_data
                    )
                    
            except Exception as e:
                print(f"WARNING Failed to load schemas: {e}")
                self._create_default_schemas()
        else:
            self._create_default_schemas()
    
    def _create_default_schemas(self):
        """
        Create default schemas for all Sacred Orders.
        """
        default_schemas = {
            "domains": {
                "babel": {
                    "description": "Sacred Order of Babel Gardens - Multilingual Embedding and Fusion (EPOCH II Enhanced)",
                    "intents": {
                        # EPOCH II - Synaptic Conclave Integration
                        "sentiment.requested": "Sentiment analysis requested via Cognitive Bus",
                        "sentiment.fused": "Sentiment fusion completed (Gemma + FinBERT)",
                        "linguistic.analysis.requested": "Linguistic analysis requested",
                        "language.interpreted": "Language interpretation completed",
                        # Legacy intents (maintained for backward compatibility)
                        "fusion.started": "Embedding fusion process initiated",
                        "fusion.completed": "Embedding fusion successfully completed",
                        "fusion.failed": "Embedding fusion encountered error",
                        "sentiment.shifted": "Sentiment analysis detected significant change",
                        "language.detected": "Automatic language detection completed",
                        "grove.awakened": "Sacred Grove component initialized"
                    },
                    "payload_schemas": {
                        "sentiment.requested": {
                            "entity_id": "string",
                            "mode": "string",
                            "cultural_weighting": "boolean",
                            "correlation_id": "string"
                        },
                        "sentiment.fused": {
                            "entity_id": "string",
                            "sentiment_score": "float",
                            "sentiment_label": "string",
                            "confidence": "float",
                            "fusion_method": "string",
                            "primary_score": "float",
                            "secondary_score": "float",
                            "correlation_id": "string"
                        },
                        "linguistic.analysis.requested": {
                            "text": "string",
                            "source_language": "string",
                            "correlation_id": "string"
                        },
                        "language.interpreted": {
                            "text": "string",
                            "detected_language": "string",
                            "confidence": "float",
                            "correlation_id": "string"
                        },
                        # Legacy schemas
                        "fusion.completed": {
                            "phrase_id": "integer",
                            "language": "string",
                            "dimensions": "integer", 
                            "processing_time_ms": "float",
                            "confidence_score": "float"
                        },
                        "sentiment.shifted": {
                            "phrase_id": "integer",
                            "old_sentiment": "float",
                            "new_sentiment": "float",
                            "shift_magnitude": "float"
                        }
                    }
                },
                "memory": {
                    "description": "Sacred Order of Memory Orders - Dual-Memory System (Archivarium + Mnemosyne) EPOCH II",
                    "intents": {
                        # Memory Write Operations
                        "write.requested": "Memory write to dual-system requested",
                        "write.completed": "Memory write to Archivarium + Mnemosyne completed",
                        "write.failed": "Memory write operation failed",
                        # Memory Read Operations (Archivarium - PostgreSQL)
                        "read.requested": "Relational memory read requested",
                        "read.fulfilled": "Relational memory read completed",
                        "read.failed": "Relational memory read failed",
                        # Memory Vector Operations (Mnemosyne - Qdrant)
                        "vector.match.requested": "Semantic vector search requested",
                        "vector.match.fulfilled": "Semantic vector search completed",
                        "vector.match.failed": "Semantic vector search failed",
                        # Memory Lifecycle
                        "memory.indexed": "Memory indexed in both systems",
                        "memory.archived": "Memory archived successfully",
                        "coherence.validated": "Dual-memory coherence validated",
                        "coherence.failed": "Dual-memory coherence validation failed"
                    },
                    "payload_schemas": {
                        "write.requested": {
                            "text": "string",
                            "source": "string",
                            "language": "string",
                            "metadata": "object",
                            "correlation_id": "string"
                        },
                        "write.completed": {
                            "phrase_id": "integer",
                            "text_preview": "string",
                            "archivarium_status": "string",
                            "mnemosyne_status": "string",
                            "duration_ms": "float",
                            "correlation_id": "string"
                        },
                        "read.requested": {
                            "query_type": "string",
                            "limit": "integer",
                            "filters": "object",
                            "correlation_id": "string"
                        },
                        "read.fulfilled": {
                            "memories": "array",
                            "count": "integer",
                            "query_type": "string",
                            "duration_ms": "float",
                            "correlation_id": "string"
                        },
                        "vector.match.requested": {
                            "query_text": "string",
                            "top_k": "integer",
                            "filters": "object",
                            "correlation_id": "string"
                        },
                        "vector.match.fulfilled": {
                            "query_text": "string",
                            "matches": "array",
                            "count": "integer",
                            "top_k": "integer",
                            "duration_ms": "float",
                            "correlation_id": "string"
                        },
                        "coherence.validated": {
                            "phrase_id_matches": "integer",
                            "text_mismatches": "integer",
                            "coherence_status": "string",
                            "validation_time_ms": "float"
                        }
                    }
                },
                "orthodoxy": {
                    "description": "Sacred Order of Orthodoxy Wardens - System Audit and Healing",
                    "intents": {
                        "heresy.detected": "System inconsistency or error detected",
                        "heresy.classified": "Heresy type and severity determined",
                        "healing.initiated": "Auto-healing process started",
                        "healing.completed": "System healing successfully applied",
                        "validation.requested": "Validation check requested",
                        "validation.completed": "Validation check completed",
                        "doctrine.updated": "System doctrine/configuration updated"
                    },
                    "payload_schemas": {
                        "heresy.detected": {
                            "heresy_type": "string",
                            "severity": "string",
                            "affected_component": "string",
                            "description": "string",
                            "auto_healable": "boolean"
                        },
                        "healing.completed": {
                            "heresy_id": "string",
                            "healing_action": "string",
                            "success": "boolean",
                            "restoration_time_ms": "float"
                        }
                    }
                },
                "conclave": {
                    "description": "Synaptic Conclave Core - Central Communication Hub",
                    "intents": {
                        "awakened": "Conclave Heart started successfully",
                        "heartbeat": "Regular system heartbeat pulse",
                        "event.routed": "Event successfully routed to Order",
                        "event.failed": "Event routing failed",
                        "subscribers.updated": "Subscription list changed",
                        "diagnostics.requested": "System diagnostics requested"
                    },
                    "payload_schemas": {
                        "heartbeat": {
                            "active_orders": "integer",
                            "total_events_today": "integer",
                            "redis_status": "string",
                            "system_load": "float"
                        },
                        "event.routed": {
                            "original_domain": "string",
                            "original_intent": "string",
                            "target_orders": "array",
                            "routing_time_ms": "float"
                        }
                    }
                },
                "codex": {
                    "description": "Sacred Order of Codex Hunters - Knowledge Discovery and Mapping",
                    "intents": {
                        "discovery.initiated": "Knowledge discovery process started",
                        "discovery.mapped": "New knowledge successfully mapped",
                        "discovery.failed": "Knowledge discovery failed",
                        "pattern.detected": "Significant pattern detected in data",
                        "correlation.found": "Cross-domain correlation discovered",
                        "index.updated": "Knowledge index updated"
                    },
                    "payload_schemas": {
                        "discovery.mapped": {
                            "knowledge_type": "string",
                            "source": "string",
                            "confidence": "float",
                            "related_entities": "array",
                            "discovery_depth": "integer"
                        }
                    }
                },
                "vault": {
                    "description": "Sacred Order of Vault Keepers - Data Protection and Recovery",
                    "intents": {
                        "backup.initiated": "Backup process started",
                        "backup.completed": "Backup successfully completed",
                        "backup.failed": "Backup process failed",
                        "recovery.requested": "Data recovery requested",
                        "recovery.executed": "Data recovery executed",
                        "integrity.verified": "Data integrity check passed"
                    },
                    "payload_schemas": {
                        "backup.completed": {
                            "backup_type": "string",
                            "data_size_mb": "float",
                            "backup_duration_ms": "integer",
                            "backup_location": "string"
                        },
                        "recovery.executed": {
                            "recovery_type": "string",
                            "recovered_records": "integer",
                            "recovery_success_rate": "float"
                        }
                    }
                },
                "crew": {
                    "description": "Mercantile Guild (CrewAI) - Multi-Agent Analysis and Strategy",
                    "intents": {
                        "analysis.initiated": "Multi-agent analysis started",
                        "analysis.completed": "Analysis successfully completed",
                        "strategy.generated": "New strategy generated by crew",
                        "consensus.reached": "Agent consensus achieved",
                        "prototype.created": "New prototype/solution created",
                        "crew.assembled": "Agent crew successfully assembled"
                    },
                    "payload_schemas": {
                        "analysis.completed": {
                            "analysis_type": "string",
                            "participating_agents": "array",
                            "consensus_score": "float",
                            "recommendations": "array",
                            "analysis_duration_ms": "integer"
                        }
                    }
                },
                "system": {
                    "description": "System-wide events and monitoring",
                    "intents": {
                        "startup.completed": "System startup completed",
                        "shutdown.initiated": "System shutdown initiated",
                        "health.critical": "Critical system health issue",
                        "performance.degraded": "System performance degradation detected",
                        "resource.exhausted": "System resource exhaustion",
                        "integration.test": "Integration test event"
                    },
                    "payload_schemas": {
                        "health.critical": {
                            "component": "string",
                            "issue": "string",
                            "severity": "integer",
                            "suggested_action": "string"
                        }
                    }
                }
            }
        }
        
        # Save default schemas
        os.makedirs(os.path.dirname(self.schema_path), exist_ok=True)
        with open(self.schema_path, 'w') as f:
            json.dump(default_schemas, f, indent=2)
        
        # Load into memory
        for domain_name, domain_data in default_schemas["domains"].items():
            self.domains[domain_name] = DomainSchema(
                domain=domain_name,
                **domain_data
            )
    
    def validate_event(self, domain: str, intent: str, payload: Dict[str, Any]) -> bool:
        """
        Validate a semantic event against the schema.
        """
        if domain not in self.domains:
            return False
        
        domain_schema = self.domains[domain]
        
        # Check if intent exists
        if intent not in domain_schema.intents:
            return False
        
        # For now, just validate domain and intent exist
        # TODO: Add payload schema validation
        return True
    
    def get_domain_intents(self, domain: str) -> List[str]:
        """
        Get all available intents for a domain.
        """
        if domain not in self.domains:
            return []
        
        return list(self.domains[domain].intents.keys())
    
    def get_all_domains(self) -> List[str]:
        """
        Get all available domains.
        """
        return list(self.domains.keys())
    
    def get_domain_description(self, domain: str) -> Optional[str]:
        """
        Get description for a domain.
        """
        if domain not in self.domains:
            return None
        
        return self.domains[domain].description
    
    def get_intent_description(self, domain: str, intent: str) -> Optional[str]:
        """
        Get description for a specific intent.
        """
        if domain not in self.domains:
            return None
        
        domain_schema = self.domains[domain]
        return domain_schema.intents.get(intent)
    
    def export_schema(self) -> Dict[str, Any]:
        """
        Export the complete schema for documentation.
        """
        export_data = {
            "lexicon_version": "1.0.0",
            "last_updated": datetime.utcnow().isoformat(),
            "domains": {}
        }
        
        for domain_name, domain_schema in self.domains.items():
            export_data["domains"][domain_name] = {
                "description": domain_schema.description,
                "intents": domain_schema.intents,
                "payload_schemas": domain_schema.payload_schemas
            }
        
        return export_data


# Global lexicon instance
_lexicon: Optional[SacredLexicon] = None

async def get_lexicon() -> SacredLexicon:
    """
    Get the global Sacred Lexicon instance.
    """
    global _lexicon
    if _lexicon is None:
        _lexicon = SacredLexicon()
    return _lexicon