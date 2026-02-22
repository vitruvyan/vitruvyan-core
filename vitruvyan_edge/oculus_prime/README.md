# Oculus Prime — Evidence Ingestion Gateway

> **Subtitle**: Multi-purpose edge ingestion gateway for H2M and M2M interoperability.

---

## Purpose

Oculus Prime is a **domain-agnostic Evidence Pack ingestion system** responsible for:

- Acquiring and normalizing external inputs (documents, media, sensors, APIs)
- Creating immutable **Evidence Packs** with literal, descriptive content
- Emitting events to the Cognitive Bus for downstream processing
- Enforcing append-only persistence and integrity guarantees

**Sacred Order**: Perception (domain-agnostic edge acquisition layer)

---

## Directory Structure

```
vitruvyan_edge/oculus_prime/
├── core/                           # Core Oculus Prime module (domain logic)
│   ├── README.md                   # Oculus Prime system documentation
│   ├── COMPLIANCE_CHECKLIST.md     # Compliance verification checklist
│   ├── INTAKE_CODEX_BOUNDARY_CONTRACT.md  # Contract with Codex Hunters
│   ├── schema.sql                  # PostgreSQL schema (append-only tables)
│   ├── event_emitter.py            # Event emission to Cognitive Bus
│   ├── guardrails.py               # Validation and integrity checks
│   ├── agents/                     # Oculus Prime agents (document, API, sensor)
│   ├── event_evidence_created_v1.json      # Event schema
│   └── evidence_pack_schema_v1.json        # Evidence Pack schema
└── dse_bridge/                     # DSE integration bridge (if needed)
    ├── main.py                     # Bridge service
    └── README.md                   # Bridge documentation

services/api_edge_oculus_prime/           # Canonical runtime service (LIVELLO 2)
├── main.py                         # FastAPI bootstrap
├── config.py                       # Centralized env configuration
├── api/routes.py                   # Thin HTTP endpoints
├── adapters/                       # Runtime + persistence adapters
├── Dockerfile
└── requirements.txt
```

Canonical runtime path is `services/api_edge_oculus_prime/*`.

---

## Database Setup

### 1. Create Oculus Prime Tables

Run the schema.sql file to create the required tables in PostgreSQL:

```bash
psql -h <POSTGRES_HOST> -U <POSTGRES_USER> -d vitruvyan_core -f vitruvyan_edge/oculus_prime/core/schema.sql
```

**Tables created**:
- `evidence_packs` — Append-only storage for Evidence Packs
- `intake_event_log` — Audit trail for event emissions
- `intake_event_failures` — Failed event emissions (diagnostics + retry candidates)

**Design Principles**:
- **Append-only**: INSERT only, NO UPDATE/DELETE
- **Immutability**: Enforced via RBAC (application user has INSERT+SELECT only)
- **JSONB**: Flexible metadata storage
- **Integrity**: Evidence hash verification, optional signatures

---

## Service Deployment

### 1. Build Docker Image

```bash
docker build -f services/api_edge_oculus_prime/Dockerfile -t vitruvyan_oculus_prime:latest .
```

### 2. Run Container

```bash
docker run -d \
  --name vitruvyan_oculus_prime \
  --network vitruvyan_core_net \
  -p 9050:8050 \
  -e POSTGRES_HOST=core_postgres \
  -e POSTGRES_PORT=5432 \
  -e POSTGRES_DB=vitruvyan_core \
  -e POSTGRES_USER=vitruvyan_core_user \
  -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD} \
  -e REDIS_HOST=core_redis \
  -e REDIS_PORT=6379 \
  vitruvyan_oculus_prime:latest
```

### 3. Health Check

```bash
curl http://localhost:9050/health
```

Expected response:
```json
{"status": "healthy", "service": "vitruvyan_oculus_prime_api", "version": "1.0.0"}
```

### 4. Troubleshooting Connection Errors

If you see `connection refused` on `localhost:5432` or `/health` returns `503`:

- Containerized run (recommended): keep Oculus Prime on `vitruvyan_core_net` and use
  `POSTGRES_HOST=core_postgres`, `REDIS_HOST=core_redis`.
- Host run (`uvicorn` outside Docker): use mapped host ports from core stack:
  `POSTGRES_HOST=localhost`, `POSTGRES_PORT=9432`, `REDIS_HOST=localhost`, `REDIS_PORT=9379`.
- Ensure schema is applied:
  `psql -h <POSTGRES_HOST> -U <POSTGRES_USER> -d vitruvyan_core -f vitruvyan_edge/oculus_prime/core/schema.sql`.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/oculus-prime/document` | Ingest a document |
| POST | `/api/oculus-prime/image` | Ingest image |
| POST | `/api/oculus-prime/audio` | Ingest audio |
| POST | `/api/oculus-prime/video` | Ingest video |
| POST | `/api/oculus-prime/cad` | Ingest CAD/BIM |
| POST | `/api/oculus-prime/landscape` | Ingest landscape raster/satellite |
| POST | `/api/oculus-prime/geo` | Ingest geospatial files |
| GET | `/api/oculus-prime/evidence/{evidence_id}` | Retrieve Evidence Pack by ID |
| GET | `/api/oculus-prime/pipeline` | Pipeline status snapshot |
| GET | `/api/oculus-prime/events` | Recent Oculus Prime events |
| GET | `/health` | Service health check |

Legacy compatibility:
- `/api/intake/*` remains available as deprecated alias.

---

## Integration with Vitruvyan Core

### Event Emission

Oculus Prime emits canonical `oculus_prime.evidence.created` events to the Cognitive Bus (Redis Streams), with versioned migration support for legacy channel `intake.evidence.created`.

**Event Schemas**:
- `event_evidence_created_v2.json` (canonical)
- `event_evidence_created_v1.json` (legacy compatibility)

**Canonical Event (v2)**:
```json
{
  "evidence_id": "EVD-<UUID>",
  "chunk_id": "CHK-1",
  "source_type": "document",
  "normalized_text": "...",
  "created_utc": "2026-02-16T19:30:00Z",
  "schema_ref": "vitruvyan://oculus_prime/events/evidence_created/v2.0"
}
```

**Event Bus Channels**:
- canonical: `oculus_prime.evidence.created`
- legacy alias: `intake.evidence.created`

**Migration mode env**:
- `OCULUS_PRIME_EVENT_MIGRATION_MODE=dual_write` (default)
- `OCULUS_PRIME_EVENT_MIGRATION_MODE=v2_only`
- `OCULUS_PRIME_EVENT_MIGRATION_MODE=v1_only`

### Downstream Consumers

- **Codex Hunters**: Index Evidence Packs for semantic search
- **Memory Orders**: Store Evidence Packs in long-term memory
- **Pattern Weavers**: Extract entities and ontology mappings
- **Orthodoxy Wardens**: Validate integrity and compliance

---

## Compliance

All Oculus Prime operations MUST comply with:

- **ACCORDO-FONDATIVO-INTAKE-V1.1**: Foundational contract
- **INTAKE_CODEX_BOUNDARY_CONTRACT.md**: Codex Hunters integration rules
- **COMPLIANCE_CHECKLIST.md**: Pre-deployment verification

---

## Documentation

- **Core README**: [vitruvyan_edge/oculus_prime/core/README.md](core/README.md)
- **Compliance Checklist**: [vitruvyan_edge/oculus_prime/core/COMPLIANCE_CHECKLIST.md](core/COMPLIANCE_CHECKLIST.md)
- **Codex Contract**: [vitruvyan_edge/oculus_prime/core/INTAKE_CODEX_BOUNDARY_CONTRACT.md](core/INTAKE_CODEX_BOUNDARY_CONTRACT.md)

---

## Development Notes

- **Origin**: Imported from `vitruvyan` vertical (Feb 16, 2026)
- **Python Version**: 3.11+
- **Dependencies**: FastAPI, psycopg2-binary, redis, pydantic
- **Testing**: Unit tests pending (import from vitruvyan/tests)

---

## Next Steps

1. ✅ Import core module from vitruvyan
2. ✅ Import service API from vitruvyan
3. ✅ Import database schema
4. ✅ Align runtime service to `services/api_edge_oculus_prime` (LIVELLO 2 structure)
5. ✅ Add Oculus Prime service to `infrastructure/docker/docker-compose.yml`
6. ⏳ Run integration tests
7. ⏳ Deploy to production VPS

---

**Last Updated**: Feb 16, 2026  
**Maintainer**: Vitruvyan Team  
**Status**: Imported, pending integration
