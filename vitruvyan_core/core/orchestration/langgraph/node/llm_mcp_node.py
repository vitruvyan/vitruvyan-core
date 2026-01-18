"""
LLM MCP Node - LangGraph Integration with Model Context Protocol

Sacred Order: Discourse (Linguistic Reasoning)
Purpose: Bridge between LangGraph and MCP Server via OpenAI Function Calling

Architecture:
    User Query → LangGraph → OpenAI Function Calling → llm_mcp_node → 
    MCP Server :8020 → Sacred Orders → Real APIs (Neural Engine, VEE, Pattern Weavers)

Key Features:
    - OpenAI Function Calling for tool selection
    - USE_MCP env flag for A/B testing (MCP vs legacy nodes)
    - Stateless: MCP server handles all business logic
    - Sacred Orders enforcement (Synaptic Conclave, Orthodoxy Wardens, Vault Keepers)

Author: Vitruvyan AI
Created: Dec 26, 2025 (Phase 4 - LangGraph Integration)
"""

import os
import json
import logging
import asyncio  # 🔧 For event loop access in sync context (Phase 4)
import nest_asyncio  # 🔧 Allow nested event loops (Phase 4 fix)
from typing import Dict, Any, List, Optional
import httpx
from openai import OpenAI

logger = logging.getLogger(__name__)

# nest_asyncio applied lazily to handle uvloop
_nest_applied = False

def _ensure_nest_asyncio():
    """Apply nest_asyncio patch once, handling uvloop gracefully"""
    global _nest_applied
    if not _nest_applied:
        try:
            nest_asyncio.apply()
            _nest_applied = True
            logger.debug("✅ nest_asyncio applied successfully")
        except ValueError as e:
            # uvloop doesn't support patching, use workaround
            logger.warning(f"⚠️ nest_asyncio failed (uvloop?): {e}")
            _nest_applied = True  # Don't retry

# Environment configuration
USE_MCP = os.getenv("USE_MCP", "0") == "1"  # Master switch for MCP integration
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://omni_mcp:8021")  # vitruvyan-os uses port 8021
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # Cost-optimized for tool calling

# OpenAI client (lazy init)
_openai_client: Optional[OpenAI] = None


def get_openai_client() -> OpenAI:
    """Get or initialize OpenAI client."""
    global _openai_client
    if _openai_client is None:
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        _openai_client = OpenAI(api_key=OPENAI_API_KEY)
    return _openai_client


async def get_mcp_tools() -> List[Dict[str, Any]]:
    """
    Fetch available tools from MCP Server.
    
    Returns:
        List of OpenAI Function Calling compatible tool definitions
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{MCP_SERVER_URL}/tools")
            response.raise_for_status()
            data = response.json()
            return data.get("tools", [])
    except Exception as e:
        logger.error(f"❌ Failed to fetch MCP tools: {e}")
        return []


async def execute_mcp_tool(tool_name: str, args: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """
    Execute a tool via MCP Server.
    
    Args:
        tool_name: Tool to execute (e.g., "screen_tickers")
        args: Tool arguments
        user_id: User identifier for audit trail
    
    Returns:
        Tool execution result with Sacred Orders metadata
    """
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:  # Long timeout for Neural Engine
            response = await client.post(
                f"{MCP_SERVER_URL}/execute",
                json={
                    "tool": tool_name,
                    "args": args,
                    "user_id": user_id
                }
            )
            
            if response.status_code == 422:
                # Orthodoxy Wardens rejected (heretical data)
                error_data = response.json()
                logger.warning(f"⚠️ Orthodoxy rejected {tool_name}: {error_data.get('detail')}")
                return {
                    "status": "rejected",
                    "error": "Orthodoxy Wardens validation failed",
                    "detail": error_data.get("detail"),
                    "data": None
                }
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(
                f"✅ MCP tool executed: {tool_name}, "
                f"orthodoxy={result.get('data', {}).get('orthodoxy_status', 'unknown')}"
            )
            
            return result
            
    except httpx.HTTPStatusError as e:
        logger.error(f"❌ MCP API error: {e.response.status_code} - {e.response.text}")
        return {
            "status": "error",
            "error": f"MCP API failed: {e.response.status_code}",
            "data": None
        }
    except Exception as e:
        logger.error(f"❌ MCP execution error: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "data": None
        }


def llm_mcp_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node for MCP integration via OpenAI Function Calling.
    
    Flow:
        1. Check USE_MCP flag (skip if disabled)
        2. Fetch available MCP tools
        3. Call OpenAI with Function Calling to select tool
        4. Execute tool via MCP Server
        5. Update LangGraph state with results
    
    Args:
        state: LangGraph state dict with keys:
            - input_text: User query
            - user_id: User identifier
            - entity_ids: Extracted entity_ids (optional)
            - language: Detected language (optional)
    
    Returns:
        Updated state dict with keys:
            - mcp_tool_used: Tool name executed (if any)
            - mcp_result: Tool execution result
            - mcp_orthodoxy: Orthodoxy validation status
            - [tool-specific state updates]
    """
    if not USE_MCP:
        logger.info("🔒 MCP disabled (USE_MCP=0), skipping llm_mcp_node")
        return state
    
    user_input = state.get("input_text", "")
    user_id = state.get("user_id", "anonymous")
    entity_ids = state.get("entity_ids", [])
    language = state.get("language", "en")
    
    logger.info(f"🧠 LLM MCP Node: input='{user_input[:50]}...', entity_ids={entity_ids}, language={language}")
    
    # Step 1: Fetch available tools (handle nested event loop with threading)
    _ensure_nest_asyncio()
    
    def _run_async_in_thread(coro):
        """Run async coroutine in new thread with fresh event loop"""
        import concurrent.futures
        def _run():
            # Create fresh event loop in this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(_run)
            return future.result(timeout=90)
    
    mcp_tools = _run_async_in_thread(get_mcp_tools())
    
    if not mcp_tools:
        logger.warning("⚠️ No MCP tools available, falling back to legacy nodes")
        return state
    
    logger.info(f"📋 Loaded {len(mcp_tools)} MCP tools: {[t['function']['name'] for t in mcp_tools]}")
    
    # Step 2: OpenAI Function Calling to select tool
    try:
        client = get_openai_client()
        
        # Construct system prompt with context
        system_prompt = f"""You are Vitruvyan AI, a financial analysis assistant.
User query language: {language}
Available entity_ids: {', '.join(entity_ids) if entity_ids else 'None extracted yet'}

Select the most appropriate tool to answer the user's question.
If no tool matches, respond directly without tool calling."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            tools=mcp_tools,
            tool_choice="auto",  # Let OpenAI decide if tool needed
            temperature=0.0  # Deterministic for tool selection
        )
        
        message = response.choices[0].message
        
        # Check if tool was called
        if not message.tool_calls:
            logger.info("🤷 OpenAI chose not to call any tool (direct response)")
            return {
                **state,
                "mcp_tool_used": None,
                "mcp_result": None,
                "response": {"narrative": message.content or "No response generated"}
            }
        
        # Step 3: Execute tool via MCP (using existing event loop)
        tool_call = message.tool_calls[0]
        tool_name = tool_call.function.name
        tool_args = json.loads(tool_call.function.arguments)
        
        logger.info(f"🔧 OpenAI selected tool: {tool_name} with args: {tool_args}")
        
        mcp_result = _run_async_in_thread(execute_mcp_tool(tool_name, tool_args, user_id))
        
        # Step 4: Update state based on tool result
        updated_state = {
            **state,
            "mcp_tool_used": tool_name,
            "mcp_result": mcp_result,
            "mcp_orthodoxy": mcp_result.get("data", {}).get("orthodoxy_status", "unknown")
        }
        
        # Map MCP result to LangGraph state keys
        if mcp_result.get("status") == "success":
            tool_data = mcp_result.get("data", {})
            
            if tool_name == "screen_tickers":
                # Update numerical_panel with screening results
                updated_state["numerical_panel"] = tool_data.get("entity_ids", [])
                updated_state["screening_data"] = {
                    "profile": tool_data.get("profile"),
                    "universe_size": tool_data.get("universe_size"),
                    "orthodoxy_status": tool_data.get("orthodoxy_status")
                }
            
            elif tool_name == "generate_vee_summary":
                # Update VEE explanations
                entity_id = tool_args.get("entity_id")
                if entity_id:
                    if "vee_explanations" not in updated_state:
                        updated_state["vee_explanations"] = {}
                    updated_state["vee_explanations"][entity_id] = {
                        "summary": tool_data.get("narrative", "")
                    }
            
            elif tool_name == "query_sentiment":
                # Update sentiment data
                updated_state["sentiment_data"] = {
                    "entity_id": tool_args.get("entity_id"),
                    "avg_sentiment": tool_data.get("avg_sentiment"),
                    "trend": tool_data.get("trend"),
                    "sample_count": tool_data.get("sample_count")
                }
            
            elif tool_name == "compare_tickers":
                # Update comparison matrix
                updated_state["comparison_matrix"] = {
                    "winner": tool_data.get("winner"),
                    "loser": tool_data.get("loser"),
                    "deltas": tool_data.get("deltas", {})
                }
            
            elif tool_name == "extract_semantic_context":
                # Update weaver context
                updated_state["weaver_context"] = {
                    "concepts": tool_data.get("concepts", []),
                    "regions": tool_data.get("regions", []),
                    "sectors": tool_data.get("sectors", []),
                    "risk_profile": tool_data.get("risk_profile", {})
                }
        
        else:
            # Tool execution failed
            logger.error(f"❌ MCP tool {tool_name} failed: {mcp_result.get('error')}")
            updated_state["error"] = mcp_result.get("error")
        
        logger.info(f"✅ LLM MCP Node complete: tool={tool_name}, status={mcp_result.get('status')}")
        return updated_state
    
    except Exception as e:
        logger.error(f"❌ LLM MCP Node error: {e}", exc_info=True)
        return {
            **state,
            "mcp_tool_used": None,
            "mcp_result": None,
            "error": f"MCP integration error: {str(e)}"
        }


# Health check function
async def mcp_health_check() -> Dict[str, Any]:
    """
    Check MCP Server health status.
    
    Returns:
        Health check result with status and metadata
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{MCP_SERVER_URL}/health")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"❌ MCP health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}
