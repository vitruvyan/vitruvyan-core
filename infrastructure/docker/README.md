# Docker Infrastructure

**Status**: Imported from vitruvyan production (Day 5)  
**Purpose**: Container orchestration, Dockerfiles, and dependency management

## Directory Structure

```
infrastructure/docker/
├── dockerfiles/          # 12 Dockerfiles for all services
├── requirements/         # 21 requirements.txt files (Python dependencies)
└── docker-compose*.yml   # 4 compose orchestration files
```

## Dockerfiles (12 files)

All service Dockerfiles for container builds:

- `Dockerfile.api_graph` (port 8004) - LangGraph orchestration
- `Dockerfile.api_neural` (port 8003) - Neural Engine
- `Dockerfile.api_semantic` (port 8002) - Semantic parsing
- `Dockerfile.api_conclave` (port 8012) - Synaptic Conclave
- `Dockerfile.orthodoxy_wardens` (port 8006) - Schema validation
- `Dockerfile.vault_keepers` (port 8007) - Memory custodians
- `Dockerfile.portfolio_guardian` (port 8011) - Collection risk monitoring
- `Dockerfile.api_crewai` (port 8005) - CrewAI orchestration
- `Dockerfile.api_memory_orders` (port 8016) - Memory operations
- `Dockerfile.api_codex_hunters` (port 8008) - Data ingestion
- `Dockerfile.api_notion` - Notion integration
- `Dockerfile.api_conclave.backup` - Backup configuration

## Requirements (21 files)

Python dependency specifications for all services:

- Core services: api_graph, api_neural, api_semantic
- Governance services: vault_keepers, orthodoxy_wardens, api_conclave
- Trade services: portfolio_guardian, api_crewai
- Memory services: api_memory_orders
- Cognitive services: babel_gardens, api_embedding
- Perception services: codex_hunters

## Docker Compose Files (4 files)

Orchestration configurations:

- `docker-compose.yml` - Main production configuration
- `docker-compose.test.yml` - Testing environment
- `docker-compose.openmetadata.yml` - OpenMetadata integration
- `docker-compose.postgres.yml` - PostgreSQL configuration

## Migration Status

✅ **COMPLETE** - All Docker infrastructure imported from production  
📦 **Services migrated**: 10/13 active services  
⚠️ **Pending**: Update Dockerfile paths from `core.*` to `vitruvyan_os.*`

## Next Steps

1. Update all Dockerfiles to use new import paths
2. Rebuild all Docker images with new structure
3. Update docker-compose.yml service definitions
4. Test container orchestration with new architecture

---

**Imported**: November 7, 2025 (Day 5)  
**Source**: vitruvyan production `docker/` directory
