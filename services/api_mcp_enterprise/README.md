# MCP Enterprise Server

> **Last updated**: Mar 15, 2026 14:00 UTC

Enterprise-specialized Model Context Protocol server. Wraps the core MCP server
(port 8020) with ERP-domain tool schemas, argument normalization, and enterprise
entity field aliasing.

## Architecture

```
Client → MCP Enterprise (8021) → Core MCP (8020) → Sacred Orders
           ↓
   Enterprise Adapter
   (tool aliasing, arg normalization)
           ↓
   Enterprise Config Pack
   (domains/enterprise/mcp_server/)
```

**Key principle**: Core MCP stays 100% domain-agnostic. This server runs as a
standalone proxy that adds enterprise semantics before delegating to core.

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check (includes core MCP connectivity) |
| `/tools` | GET | Merged tool schemas (generic + enterprise) |
| `/execute` | POST | Execute tool (normalize → proxy to core MCP) |
| `/v1/enterprise/config` | GET | Enterprise MCP configuration |
| `/v1/enterprise/tools` | GET | Enterprise-only tool schemas |
| `/v1/enterprise/normalize` | POST | Normalize enterprise args to canonical |

## Enterprise Tools

| Tool | Canonical Executor | Description |
|------|--------------------|-------------|
| `query_partners` | `screen_entities` | Rank customers/suppliers |
| `analyze_invoices` | `screen_entities` | Score invoices |
| `compare_partners` | `compare_entities` | Compare partners side-by-side |
| `query_business_health` | `query_signals` | Business health signals |
| `generate_business_report` | `generate_vee_summary` | Narrative business report |
| `analyze_erp_context` | `extract_semantic_context` | Semantic ERP query analysis |

## Deployment

```bash
# Standalone (outside core docker-compose)
cd infrastructure/docker
docker compose -f docker-compose.enterprise.yml up -d

# Verify
curl http://localhost:8021/health
curl http://localhost:8021/v1/enterprise/config
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8021` | Server port |
| `MCP_CORE_URL` | `http://localhost:8020` | Core MCP server URL |
| `LANGGRAPH_URL` | `http://localhost:9004` | LangGraph orchestrator |
| `POSTGRES_HOST` | `localhost` | PostgreSQL host |
| `POSTGRES_PORT` | `9432` | PostgreSQL port |
| `REDIS_HOST` | `localhost` | Redis host |
