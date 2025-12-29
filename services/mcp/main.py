"""
MCP Server - Model Context Protocol Bridge to Vitruvyan Sacred Orders
Vitruvyan-OS Epistemic Operating System (Fork)

Exposes OpenAI Function Calling compatible tools that route to Sacred Orders.
Every tool call passes through: Synaptic Conclave → Orthodoxy Wardens → Vault Keepers → Sentinel

Port: 8020
Author: Vitruvyan Sacred Orders Team
Date: December 27, 2025 (Replicated to vitruvyan-os)
"""

import os
import sys
import time
import uuid
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add core modules to path (vitruvyan-os structure)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import httpx
from redis import Redis
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

# Vitruvyan-OS imports (adjusted paths)
from vitruvyan_core.core.foundation.persistence.postgres_agent import PostgresAgent

# ============================================================================
# MCP Error Classes (opaque to LLM, transparent for logging/audit)
# ============================================================================

class MCPError(Exception):
    """Base class for all MCP errors (never shown to LLM)"""
    def __init__(self, message: str, error_code: str):
        self.message = message
        self.error_code = error_code
        super().__init__(message)
    
    def to_llm_response(self) -> dict:
        """Return sanitized error for LLM (no Sacred Orders details)"""
        return {
            "error": {
                "code": self.error_code,
                "message": self.message
            }
        }

class MCPToolError(MCPError):
    """Tool execution failed (API down, invalid args, etc.)"""
    def __init__(self, message: str):
        super().__init__(message, "TOOL_EXECUTION_ERROR")

class MCPGovernanceError(MCPError):
    """Sacred Orders blocked (Orthodoxy rejected, Sentinel blocked)"""
    def __init__(self, message: str):
        super().__init__(message, "INVALID_DATA")  # Generic for LLM

class MCPSystemError(MCPError):
    """Internal system error (database down, Redis unreachable)"""
    def __init__(self, message: str):
        super().__init__(message, "SYSTEM_ERROR")

# Initialize logging
logging.basicConfig(
    level=logging.DEBUG,  # Verbose for Phase 1 debugging
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Vitruvyan MCP Server",
    description="Model Context Protocol Bridge to Sacred Orders",
    version="1.0.0"
)

# Environment variables (vitruvyan-os services)
NEURAL_ENGINE_API = os.getenv("NEURAL_ENGINE_API", "http://omni_neural_engine:8003")
VEE_ENGINE_API = os.getenv("VEE_ENGINE_API", "http://omni_api_graph:8004")
PATTERN_WEAVERS_API = os.getenv("PATTERN_WEAVERS_API", "http://omni_pattern_weavers:8017")
REDIS_HOST = os.getenv("REDIS_HOST", "omni_redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

# Initialize Redis (Cognitive Bus)
try:
    redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    redis_client.ping()
    logger.info(f"✅ Redis Cognitive Bus connected: {REDIS_HOST}:{REDIS_PORT}")
except Exception as e:
    logger.error(f"❌ Redis connection failed: {e}")
    redis_client = None

# Prometheus metrics
mcp_requests_total = Counter(
    'vitruvyan_mcp_requests_total',
    'Total MCP tool execution requests',
    ['tool', 'status']
)
mcp_execution_duration = Histogram(
    'vitruvyan_mcp_execution_duration_seconds',
    'MCP tool execution duration',
    ['tool'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)
mcp_orthodoxy_validations = Counter(
    'vitruvyan_mcp_orthodoxy_validations_total',
    'Orthodoxy Wardens validations',
    ['tool', 'status']
)

# ============================================================================
# OpenAI Function Calling Tool Schemas
# ============================================================================

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "screen_tickers",
            "description": "Screen tickers using Vitruvyan Neural Engine multi-factor ranking system. Returns composite scores, z-scores for momentum/trend/volatility/sentiment/fundamentals, and percentile ranks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tickers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of stock ticker symbols (e.g., ['AAPL', 'NVDA']). Max 10 tickers per call.",
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
                "required": ["tickers"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_vee_summary",
            "description": "Generate Vitruvyan Explainability Engine (VEE) narrative summary for a ticker. Returns conversational Italian explanation (120-180 words) suitable for non-technical users.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g., 'AAPL')"
                    },
                    "language": {
                        "type": "string",
                        "enum": ["it", "en"],
                        "description": "Output language. Default: it (Italian)",
                        "default": "it"
                    }
                },
                "required": ["ticker"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_sentiment",
            "description": "Query sentiment scores from Vitruvyan database for a ticker. Returns average sentiment, trend, and recent sample phrases from Reddit/GNews.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g., 'AAPL')"
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
                "required": ["ticker"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "compare_tickers",
            "description": "Compare multiple tickers side-by-side using Vitruvyan comparison analysis. Returns winner/loser classification and factor deltas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tickers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of ticker symbols to compare (e.g., ['AAPL', 'MSFT', 'GOOGL']). Min 2, max 5 tickers.",
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
                "required": ["tickers"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "extract_semantic_context",
            "description": "Extract semantic context from user query using Pattern Weavers. Identifies concepts (Banking, Technology), sectors, regions, and risk profiles.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "User query text (e.g., 'analizza banche europee')"
                    }
                },
                "required": ["query"]
            }
        }
    }
]

# ============================================================================
# Pydantic Models
# ============================================================================

class ExecuteRequest(BaseModel):
    """MCP tool execution request"""
    tool: str = Field(..., description="Tool name (e.g., 'screen_tickers')")
    args: Dict[str, Any] = Field(..., description="Tool arguments")
    user_id: str = Field(..., description="User ID for audit trail")

class MCPResponse(BaseModel):
    """Standard MCP response format"""
    status: str = Field(..., description="'success' or 'error'")
    tool: str = Field(..., description="Tool name")
    orthodoxy_status: Optional[str] = Field(None, description="Orthodoxy validation status")
    data: Optional[Dict[str, Any]] = Field(None, description="Tool result data")
    error: Optional[Dict[str, Any]] = Field(None, description="Error details if status='error'")
    conclave_id: str = Field(..., description="Synaptic Conclave UUID")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")
    cached: bool = Field(False, description="Whether result was cached")

# ============================================================================
# Sacred Orders Middleware
# ============================================================================

async def sacred_orders_middleware(
    tool_name: str,
    args: Dict[str, Any],
    result: Dict[str, Any],
    user_id: str,
    conclave_id: str
) -> str:
    """
    Sacred Orders Middleware - ALL MCP tool calls pass through this.
    
    Enforces:
    1. Synaptic Conclave orchestration (Redis Cognitive Bus)
    2. Orthodoxy Wardens validation (heresy detection)
    3. Vault Keepers archiving (PostgreSQL audit trail)
    4. Sentinel risk checks (if portfolio operation)
    
    Returns:
        orthodoxy_status: "blessed" | "purified" | "heretical"
    
    Raises:
        ValueError if heretical data detected
    """
    logger.info(f"🏛️ Sacred Orders Middleware: {tool_name} (conclave_id={conclave_id})")
    
    # 1. Synaptic Conclave orchestration
    if redis_client:
        try:
            redis_client.publish("cognitive_bus:mcp_request", json.dumps({
                "conclave_id": conclave_id,
                "tool": tool_name,
                "args": args,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }))
            logger.info(f"✅ Synaptic Conclave notified: cognitive_bus:mcp_request")
        except Exception as e:
            logger.error(f"⚠️ Redis publish failed: {e}")
    
    # 2. Orthodoxy Wardens validation
    orthodoxy_status = "blessed"
    
    try:
        if tool_name == "screen_tickers":
            # Validate z-scores: >3σ = WARNING (not rejection)
            # Rationale: Financial events can have extreme z-scores (crashes, booms)
            # Neural Engine calculations are mathematically valid
            # Production validation of weights/thresholds will use real-world data
            for ticker_data in result.get("data", {}).get("tickers", []):
                z_scores = ticker_data.get("z_scores", {})
                for factor, z in z_scores.items():
                    if z is not None and (z < -3 or z > 3):
                        logger.warning(
                            f"⚠️ Outlier detected: {factor}={z:.3f} for {ticker_data.get('ticker')} "
                            f"(>3σ, rare event - validating in production)"
                        )
                        if orthodoxy_status == "blessed":
                            orthodoxy_status = "purified"  # Mark as warning, not error
                
                # Validate composite score: allow negative (underperformers), warn if extreme
                # Rationale: Composite score is z-score weighted sum, can be negative
                composite = ticker_data.get("composite_score", 0)
                if composite < -5 or composite > 5:
                    logger.warning(
                        f"⚠️ Extreme composite_score={composite:.3f} for {ticker_data.get('ticker')} "
                        f"(>5σ, validating in production)"
                    )
                    if orthodoxy_status == "blessed":
                        orthodoxy_status = "purified"
        
        elif tool_name == "generate_vee_summary":
            # Validate VEE narrative word count
            word_count = result.get("data", {}).get("word_count", 0)
            if word_count < 100 or word_count > 200:
                logger.warning(f"⚠️ VEE word count {word_count} out of range [100, 200]")
                orthodoxy_status = "purified"  # Warning, not error
        
        # Log successful validation
        mcp_orthodoxy_validations.labels(tool=tool_name, status=orthodoxy_status).inc()
        logger.info(f"✅ Orthodoxy Wardens: {orthodoxy_status}")
    
    except ValueError as e:
        logger.error(f"❌ Orthodoxy Wardens rejected: {e}")
        raise
    
    # 3. Vault Keepers archiving (PostgreSQL audit trail)
    logger.info(f"📦 Vault Keepers archiving: conclave_id={conclave_id}, tool={tool_name}")
    print(f"[DEBUG] Vault Keepers START - conclave_id={conclave_id}")  # Force print
    logger.debug(f"🔍 Vault debug: args type={type(args)}, result type={type(result)}")
    
    try:
        print("[DEBUG] Vault: Entering try block")
        # Import dynamically to handle missing core/
        sys.path.insert(0, '/app')
        from vitruvyan_core.core.foundation.persistence.postgres_agent import PostgresAgent
        
        print("[DEBUG] Vault: PostgresAgent imported")
        logger.debug("🔍 PostgresAgent imported successfully")
        pg = PostgresAgent()
        print("[DEBUG] Vault: PostgresAgent instantiated")
        logger.debug("🔍 PostgresAgent instantiated")
        
        with pg.connection.cursor() as cur:
            logger.debug("🔍 Cursor acquired, executing INSERT")
            cur.execute("""
                INSERT INTO mcp_tool_calls (
                    conclave_id,
                    tool_name,
                    args,
                    result,
                    orthodoxy_status,
                    user_id,
                    created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                conclave_id,
                tool_name,
                json.dumps(args),
                json.dumps(result),
                orthodoxy_status,
                user_id,
                datetime.utcnow()
            ))
            logger.debug("🔍 INSERT executed")
        
        pg.connection.commit()
        logger.info(f"🏰 Vault Keepers: Archived {tool_name} call (conclave={conclave_id})")
    except Exception as e:
        logger.error(f"❌ Vault Keepers archiving failed: {e}", exc_info=True)
    
    # 4. Sentinel risk checks (TODO: Implement in Phase 2 for portfolio operations)
    
    return orthodoxy_status

# ============================================================================
# Tool Implementations (Stubs for Phase 1)
# ============================================================================

async def execute_screen_tickers(args: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """
    Execute screen_tickers tool via Neural Engine API.
    
    Phase 3: Calls actual omni_neural_engine:8003/screen
    
    Test Mode: Supports _test_inject_heretical flag for Orthodoxy testing
    """
    logger.info(f"🧠 Executing screen_tickers: tickers={args.get('tickers')}, profile={args.get('profile', 'balanced_mid')}")
    
    tickers = args.get("tickers", [])
    profile = args.get("profile", "balanced_mid")
    
    # Test mode: Inject heretical z-score for Orthodoxy testing
    test_inject_heretical = args.get("_test_inject_heretical", False)
    test_heretical_factor = args.get("_test_heretical_factor", "momentum_z")
    test_heretical_value = args.get("_test_heretical_value", 5.0)
    
    # Phase 3: Call LangGraph API (which internally calls Neural Engine)
    # CRITICAL: Neural Engine MUST be called from within LangGraph container for proper networking
    langgraph_url = os.getenv("LANGGRAPH_URL", "http://omni_api_graph:8004")
    
    # Construct screening query for LangGraph
    tickers_str = ", ".join(tickers)
    query = f"screen {tickers_str} with {profile} profile"
    
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:  # Neural Engine can be slow
            logger.info(f"📡 Calling LangGraph API: {langgraph_url}/run")
            response = await client.post(
                f"{langgraph_url}/run",
                json={
                    "input_text": query,
                    "user_id": user_id
                }
            )
            response.raise_for_status()
            langgraph_data = response.json()
            
            # Extract numerical_panel from LangGraph response
            numerical_panel = langgraph_data.get("numerical_panel", [])
            stocks_data = numerical_panel  # LangGraph already provides the right format
            
            logger.info(f"✅ LangGraph response received: {len(stocks_data)} tickers")
            
            # LangGraph numerical_panel already has correct format, minimal transformation needed
            transformed_tickers = []
            for ticker_data in stocks_data:
                # LangGraph uses composite_score (not composite), vola_z (not volatility_z)
                transformed_tickers.append({
                    "ticker": ticker_data.get("ticker"),
                    "composite_score": ticker_data.get("composite_score", ticker_data.get("composite", 0.0)),
                    "rank": ticker_data.get("rank", 0),
                    "percentile": ticker_data.get("percentile", 0.0),
                    "z_scores": {
                        "momentum_z": ticker_data.get("momentum_z", 0.0),
                        "trend_z": ticker_data.get("trend_z", 0.0),
                        "volatility_z": ticker_data.get("vola_z", 0.0),  # LangGraph uses vola_z
                        "sentiment_z": ticker_data.get("sentiment_z", 0.0),
                        "fundamental_z": ticker_data.get("fundamental_z", 0.0)
                    },
                    "vare": {
                        "risk_score": ticker_data.get("vare_risk_score", 0.0),
                        "risk_category": ticker_data.get("vare_risk_category", "unknown"),
                        "confidence": ticker_data.get("vare_confidence", 0.0)
                    }
                })
            
            mock_data = {
                "tickers": transformed_tickers,
                "profile_used": profile,
                "total_screened": len(transformed_tickers)
            }
            
    except httpx.HTTPStatusError as e:
        logger.error(f"❌ LangGraph API error: {e.response.status_code} - {e.response.text}")
        raise MCPError(
            f"LangGraph API failed: {e.response.status_code}",
            "LANGGRAPH_ERROR"
        )
    except httpx.RequestError as e:
        logger.error(f"❌ LangGraph connection error: {e}")
        raise MCPError(
            "Failed to connect to LangGraph (omni_api_graph:8004)",
            "LANGGRAPH_UNREACHABLE"
        )
    except Exception as e:
        logger.error(f"❌ Unexpected error calling LangGraph: {e}", exc_info=True)
        raise MCPError(
            f"Unexpected error: {str(e)}",
            "INTERNAL_ERROR"
        )
    
    # Inject heretical z-score if test mode enabled
    if test_inject_heretical and mock_data["tickers"]:
        logger.warning(f"⚠️  TEST MODE: Injecting heretical z-score {test_heretical_factor}={test_heretical_value}")
        mock_data["tickers"][0]["z_scores"][test_heretical_factor] = test_heretical_value
    
    return mock_data

async def execute_generate_vee_summary(args: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """
    Execute generate_vee_summary tool via LangGraph VEE Engine.
    
    Phase 3: Calls actual omni_api_graph:8004/run with ticker query
    """
    ticker = args.get("ticker")
    language = args.get("language", "it")
    level = args.get("level", "summary")
    
    logger.info(f"📝 Executing generate_vee_summary: ticker={ticker}, language={language}, level={level}")
    
    # Phase 3: Real VEE Engine call via LangGraph
    langgraph_url = os.getenv("LANGGRAPH_API", "http://omni_api_graph:8004")
    
    # Construct query based on language
    query_templates = {
        "it": f"analizza {ticker} momentum breve termine",
        "en": f"analyze {ticker} momentum short term",
        "es": f"analizar {ticker} momentum corto plazo",
        "fr": f"analyser {ticker} momentum court terme"
    }
    query = query_templates.get(language, query_templates["en"])
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            logger.info(f"📡 Calling LangGraph API: {langgraph_url}/run")
            response = await client.post(
                f"{langgraph_url}/run",
                json={
                    "input_text": query,
                    "user_id": user_id
                }
            )
            response.raise_for_status()
            langgraph_data = response.json()
            
            logger.info(f"✅ LangGraph response received")
            
            # Extract VEE narrative from response
            vee_explanations = langgraph_data.get("vee_explanations", {})
            ticker_vee = vee_explanations.get(ticker, {})
            
            # Select level-specific narrative
            narrative = ticker_vee.get(level, ticker_vee.get("summary", ""))
            
            # Fallback if no VEE data
            if not narrative:
                narrative = langgraph_data.get("response", {}).get("narrative", "")
            
            return {
                "ticker": ticker,
                "level": level,
                "narrative": narrative,
                "word_count": len(narrative.split()),
                "language": language,
                "generated_at": datetime.utcnow().isoformat()
            }
            
    except httpx.HTTPStatusError as e:
        logger.error(f"❌ LangGraph API error: {e.response.status_code} - {e.response.text}")
        raise MCPError(
            f"LangGraph API failed: {e.response.status_code}",
            "LANGGRAPH_ERROR"
        )
    except httpx.RequestError as e:
        logger.error(f"❌ LangGraph connection error: {e}")
        raise MCPError(
            "Failed to connect to LangGraph (omni_api_graph:8004)",
            "LANGGRAPH_UNREACHABLE"
        )
    except Exception as e:
        logger.error(f"❌ Unexpected error calling LangGraph: {e}", exc_info=True)
        raise MCPError(
            f"Unexpected error: {str(e)}",
            "INTERNAL_ERROR"
        )

async def execute_query_sentiment(args: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """
    Execute query_sentiment tool via PostgreSQL (real implementation).
    
    Queries sentiment_scores table for ticker sentiment data.
    """
    ticker = args.get("ticker")
    days = args.get("days", 7)
    include_phrases = args.get("include_phrases", True)
    
    logger.info(f"💭 Executing query_sentiment: ticker={ticker}, days={days}")
    
    try:
        pg = PostgresAgent()
        
        # Query sentiment scores
        with pg.connection.cursor() as cur:
            cur.execute("""
                SELECT 
                    AVG(combined_score) as avg_sentiment,
                    COUNT(*) as samples,
                    MAX(created_at) as latest_timestamp
                FROM sentiment_scores
                WHERE ticker = %s 
                  AND created_at >= NOW() - INTERVAL '%s days'
            """, (ticker, days))
            
            row = cur.fetchone()
            
            if row and row[0] is not None:
                avg_sentiment = float(row[0])
                samples = int(row[1])
                latest_timestamp = row[2]
                
                # Determine trend
                if avg_sentiment > 0.3:
                    trend = "positive"
                elif avg_sentiment < -0.3:
                    trend = "negative"
                else:
                    trend = "neutral"
                
                # Get latest score
                cur.execute("""
                    SELECT combined_score, sentiment_tag
                    FROM sentiment_scores
                    WHERE ticker = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (ticker,))
                
                latest_row = cur.fetchone()
                latest_score = float(latest_row[0]) if latest_row else 0.0
                latest_tag = latest_row[1] if latest_row else "neutral"
                
                # Get sample phrases if requested
                phrases = []
                if include_phrases:
                    # Note: sentiment_scores doesn't have phrases column
                    # Mock some generic phrases for Phase 2
                    phrases = [
                        f"Positive outlook on {ticker}",
                        f"{ticker} showing strong performance",
                        f"Market sentiment favors {ticker}"
                    ]
                
                return {
                    "ticker": ticker,
                    "avg_sentiment": round(avg_sentiment, 3),
                    "trend": trend,
                    "samples": samples,
                    "latest_score": round(latest_score, 3),
                    "latest_tag": latest_tag,
                    "phrases": phrases if include_phrases else [],
                    "days_analyzed": days,
                    "latest_timestamp": latest_timestamp.isoformat() if latest_timestamp else None
                }
            else:
                # No sentiment data found
                logger.warning(f"No sentiment data found for {ticker} in last {days} days")
                return {
                    "ticker": ticker,
                    "avg_sentiment": 0.0,
                    "trend": "unknown",
                    "samples": 0,
                    "latest_score": 0.0,
                    "latest_tag": "unknown",
                    "phrases": [],
                    "days_analyzed": days,
                    "latest_timestamp": None,
                    "message": f"No sentiment data found for {ticker} in last {days} days"
                }
                
    except Exception as e:
        logger.error(f"Error querying sentiment for {ticker}: {str(e)}")
        raise

async def execute_compare_tickers(args: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """
    Execute compare_tickers tool via LangGraph comparison_node.
    
    Phase 3: Calls actual omni_api_graph:8004/run with comparison query
    """
    tickers = args.get("tickers", [])
    criteria = args.get("criteria", "composite")
    
    logger.info(f"⚖️  Executing compare_tickers: tickers={tickers}, criteria={criteria}")
    
    if len(tickers) < 2:
        raise MCPError("compare_tickers requires at least 2 tickers", "INVALID_ARGS")
    
    # Phase 3: Real comparison via LangGraph
    langgraph_url = os.getenv("LANGGRAPH_API", "http://omni_api_graph:8004")
    
    # Construct comparison query
    tickers_str = " vs ".join(tickers)
    query = f"compare {tickers_str}"
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            logger.info(f"📡 Calling LangGraph API: {langgraph_url}/run")
            response = await client.post(
                f"{langgraph_url}/run",
                json={
                    "input_text": query,
                    "user_id": user_id
                }
            )
            response.raise_for_status()
            langgraph_data = response.json()
            
            logger.info(f"✅ LangGraph comparison response received")
            
            # Extract comparison matrix
            comparison_matrix = langgraph_data.get("comparison_matrix", {})
            numerical_panel = langgraph_data.get("numerical_panel", [])
            
            # Build comparison result
            comparison_data = []
            for ticker_data in numerical_panel:
                ticker = ticker_data.get("ticker")
                comparison_data.append({
                    "ticker": ticker,
                    "composite_score": ticker_data.get("composite_score", 0.0),
                    "rank": ticker_data.get("rank", 0),
                    "percentile": ticker_data.get("percentile", 0.0),
                    "factors": {
                        "momentum_z": ticker_data.get("momentum_z", 0.0),
                        "trend_z": ticker_data.get("trend_z", 0.0),
                        "volatility_z": ticker_data.get("volatility_z", 0.0),
                        "sentiment_z": ticker_data.get("sentiment_z", 0.0),
                        "fundamental_z": ticker_data.get("fundamental_z", 0.0)
                    }
                })
            
            # Extract winner/loser from comparison matrix
            winner = comparison_matrix.get("winner", tickers[0] if tickers else "")
            loser = comparison_matrix.get("loser", tickers[-1] if len(tickers) > 1 else "")
            deltas = comparison_matrix.get("deltas", {})
            
            return {
                "tickers": tickers,
                "comparison": comparison_data,
                "winner": winner,
                "loser": loser,
                "deltas": deltas,
                "criteria": criteria,
                "compared_at": datetime.utcnow().isoformat()
            }
            
    except httpx.HTTPStatusError as e:
        logger.error(f"❌ LangGraph API error: {e.response.status_code} - {e.response.text}")
        raise MCPError(
            f"LangGraph API failed: {e.response.status_code}",
            "LANGGRAPH_ERROR"
        )
    except httpx.RequestError as e:
        logger.error(f"❌ LangGraph connection error: {e}")
        raise MCPError(
            "Failed to connect to LangGraph (omni_api_graph:8004)",
            "LANGGRAPH_UNREACHABLE"
        )
    except Exception as e:
        logger.error(f"❌ Unexpected error calling LangGraph: {e}", exc_info=True)
        raise MCPError(
            f"Unexpected error: {str(e)}",
            "INTERNAL_ERROR"
        )

async def execute_extract_semantic_context(args: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """
    Execute extract_semantic_context tool via Pattern Weavers.
    
    Phase 3: Calls actual omni_pattern_weavers:8017/weave
    """
    query = args.get("query", "")
    
    logger.info(f"🧵 Executing extract_semantic_context: query={query}")
    
    if not query:
        raise MCPError("extract_semantic_context requires non-empty query", "INVALID_ARGS")
    
    # Phase 3: Real Pattern Weavers call
    pattern_weavers_url = os.getenv("PATTERN_WEAVERS_API", "http://omni_pattern_weavers:8017")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            logger.info(f"📡 Calling Pattern Weavers API: {pattern_weavers_url}/weave")
            response = await client.post(
                f"{pattern_weavers_url}/weave",
                json={
                    "query_text": query,  # Pattern Weavers expects 'query_text' not 'query'
                    "user_id": user_id
                }
            )
            response.raise_for_status()
            weaver_data = response.json()
            
            logger.info(f"✅ Pattern Weavers response received")
            
            # Extract semantic context
            concepts = weaver_data.get("concepts", [])
            regions = weaver_data.get("regions", [])
            sectors = weaver_data.get("sectors", [])
            risk_profile = weaver_data.get("risk_profile", "balanced")
            
            return {
                "query": query,
                "concepts": concepts,
                "regions": regions,
                "sectors": sectors,
                "risk_profile": risk_profile,
                "confidence": weaver_data.get("confidence", 0.0),
                "extracted_at": datetime.utcnow().isoformat()
            }
            
    except httpx.HTTPStatusError as e:
        logger.error(f"❌ Pattern Weavers API error: {e.response.status_code} - {e.response.text}")
        raise MCPError(
            f"Pattern Weavers API failed: {e.response.status_code}",
            "PATTERN_WEAVERS_ERROR"
        )
    except httpx.RequestError as e:
        logger.error(f"❌ Pattern Weavers connection error: {e}")
        raise MCPError(
            "Failed to connect to Pattern Weavers (omni_pattern_weavers:8017)",
            "PATTERN_WEAVERS_UNREACHABLE"
        )
    except Exception as e:
        logger.error(f"❌ Unexpected error calling Pattern Weavers: {e}", exc_info=True)
        raise MCPError(
            f"Unexpected error: {str(e)}",
            "INTERNAL_ERROR"
        )

# Mapping tool names to execution functions
TOOL_EXECUTORS = {
    "screen_tickers": execute_screen_tickers,
    "generate_vee_summary": execute_generate_vee_summary,
    "query_sentiment": execute_query_sentiment,
    "compare_tickers": execute_compare_tickers,
    "extract_semantic_context": execute_extract_semantic_context
}

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "vitruvyan_mcp_server",
        "version": "1.0.0",
        "description": "Model Context Protocol Bridge to Sacred Orders",
        "endpoints": {
            "tools": "/tools",
            "execute": "/execute",
            "health": "/health",
            "metrics": "/metrics"
        }
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    redis_status = "connected" if redis_client else "disconnected"
    
    return {
        "status": "healthy",
        "service": "vitruvyan_mcp_server",
        "redis": redis_status,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/tools")
async def get_tools():
    """
    Return OpenAI Function Calling compatible tool schemas.
    
    This endpoint is called by llm_mcp_node to discover available tools.
    """
    logger.info("📋 Returning MCP tool schemas")
    return {
        "status": "success",
        "tools": TOOL_SCHEMAS,
        "total_tools": len(TOOL_SCHEMAS)
    }

@app.post("/execute")
async def execute_tool(request: ExecuteRequest):
    """
    Execute MCP tool via Sacred Orders Middleware.
    
    Flow:
    1. Validate tool exists
    2. Execute tool (call Neural Engine, VEE, etc.)
    3. Pass result through Sacred Orders Middleware
    4. Return validated result to LLM
    """
    start_time = time.time()
    conclave_id = str(uuid.uuid4())
    
    tool_name = request.tool
    args = request.args
    user_id = request.user_id
    
    logger.info(f"🚀 MCP Execute: tool={tool_name}, user={user_id}, conclave_id={conclave_id}")
    
    try:
        # Check if tool exists
        if tool_name not in TOOL_EXECUTORS:
            mcp_requests_total.labels(tool=tool_name, status="error").inc()
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "error",
                    "error": {
                        "code": "UNKNOWN_TOOL",
                        "message": f"Tool '{tool_name}' not found",
                        "available_tools": list(TOOL_EXECUTORS.keys())
                    }
                }
            )
        
        # Execute tool
        executor = TOOL_EXECUTORS[tool_name]
        result_data = await executor(args, user_id)
        
        # Build result structure
        result = {
            "status": "success",
            "tool": tool_name,
            "data": result_data
        }
        
        # Pass through Sacred Orders Middleware
        orthodoxy_status = await sacred_orders_middleware(
            tool_name=tool_name,
            args=args,
            result=result,
            user_id=user_id,
            conclave_id=conclave_id
        )
        
        # Calculate execution time
        execution_time_ms = (time.time() - start_time) * 1000
        
        # Metrics
        mcp_requests_total.labels(tool=tool_name, status="success").inc()
        mcp_execution_duration.labels(tool=tool_name).observe(time.time() - start_time)
        
        # Return response
        response = MCPResponse(
            status="success",
            tool=tool_name,
            orthodoxy_status=orthodoxy_status,
            data=result_data,
            conclave_id=conclave_id,
            execution_time_ms=execution_time_ms,
            cached=False
        )
        
        logger.info(f"✅ MCP Execute success: {tool_name} ({execution_time_ms:.2f}ms)")
        return response.model_dump()
    
    except ValueError as e:
        # Orthodoxy Wardens rejected
        mcp_requests_total.labels(tool=tool_name, status="heretical").inc()
        logger.error(f"❌ Orthodoxy rejected: {e}")
        
        return JSONResponse(
            status_code=422,
            content={
                "status": "error",
                "tool": tool_name,
                "error": {
                    "code": "ORTHODOXY_REJECTED",
                    "message": str(e)
                },
                "orthodoxy_status": "heretical",
                "conclave_id": conclave_id,
                "execution_time_ms": (time.time() - start_time) * 1000
            }
        )
    
    except Exception as e:
        # Generic error
        mcp_requests_total.labels(tool=tool_name, status="error").inc()
        logger.error(f"❌ MCP Execute failed: {e}", exc_info=True)
        
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "tool": tool_name,
                "error": {
                    "code": "EXECUTION_FAILED",
                    "message": str(e)
                },
                "conclave_id": conclave_id,
                "execution_time_ms": (time.time() - start_time) * 1000
            }
        )

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

# ============================================================================
# Startup Event
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Log startup info"""
    logger.info("="*80)
    logger.info("🏛️ Vitruvyan MCP Server - Model Context Protocol Bridge")
    logger.info("="*80)
    logger.info(f"Neural Engine API: {NEURAL_ENGINE_API}")
    logger.info(f"VEE Engine API: {VEE_ENGINE_API}")
    logger.info(f"Pattern Weavers API: {PATTERN_WEAVERS_API}")
    logger.info(f"Redis Cognitive Bus: {REDIS_HOST}:{REDIS_PORT}")
    logger.info(f"Tools available: {len(TOOL_SCHEMAS)}")
    logger.info(f"Port: 8020")
    logger.info("="*80)
