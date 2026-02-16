# AEGIS Intake — Evidence Pack Ingestion System

> **Vertical**: AEGIS (Autonomous Evidence-Gathering and Intelligence System)  
> **Layer**: Perception (Ingestion)  
> **Status**: Imported from aegis vertical (Feb 16, 2026)

---

## Purpose

Intake is a **domain-agnostic Evidence Pack ingestion system** responsible for:

- Acquiring and normalizing external inputs (documents, media, sensors, APIs)
- Creating immutable **Evidence Packs** with literal, descriptive content
- Emitting events to the Cognitive Bus for downstream processing
- Enforcing append-only persistence and integrity guarantees

**Sacred Order**: Perception (BABEL GARDENS domain — but vertical-specific implementation for AEGIS)

---

## Directory Structure

```
intake/
├── core/                           # Core intake module (domain logic)
│   ├── README.md                   # Intake system documentation
│   ├── COMPLIANCE_CHECKLIST.md     # Compliance verification checklist
│   ├── INTAKE_CODEX_BOUNDARY_CONTRACT.md  # Contract with Codex Hunters
│   ├── schema.sql                  # PostgreSQL schema (append-only tables)
│   ├── event_emitter.py            # Event emission to Cognitive Bus
│   ├── guardrails.py               # Validation and integrity checks
│   ├── agents/                     # Intake agents (document, API, sensor)
│   ├── event_evidence_created_v1.json      # Event schema
│   └── evidence_pack_schema_v1.json        # Evidence Pack schema
├── service/                        # API service (FastAPI)
│   ├── main.py                     # HTTP endpoints for intake operations
│   ├── Dockerfile                  # Container definition
│   └── requirements.txt            # Python dependencies
└── dse_bridge/                     # DSE integration bridge (if needed)
    ├── main.py                     # Bridge service
    └── README.md                   # Bridge documentation
```

---

## Database Setup

### 1. Create Intake Tables

Run the schema.sql file to create the required tables in PostgreSQL:

```bash
psql -h <POSTGRES_HOST> -U <POSTGRES_USER> -d vitruvyan_core -f intake/core/schema.sql
```

**Tables created**:
- `evidence_packs` — Append-only storage for Evidence Packs
- `intake_event_log` — Audit trail for event emissions
- `intake_failures` — Failed intake attempts (diagnostics)
- `intake_sessions` — Intake session metadata (if applicable)

**Design Principles**:
- **Append-only**: INSERT only, NO UPDATE/DELETE
- **Immutability**: Enforced via RBAC (application user has INSERT+SELECT only)
- **JSONB**: Flexible metadata storage
- **Integrity**: Evidence hash verification, optional signatures

---

## Service Deployment

### 1. Build Docker Image

```bash
docker build -f intake/service/Dockerfile -t aegis_intake:latest .
```

### 2. Run Container

```bash
docker run -d \
  --name aegis_intake \
  --network vitruvyan_core_net \
  -p 9050:8050 \
  -e POSTGRES_HOST=core_postgres \
  -e POSTGRES_PORT=5432 \
  -e POSTGRES_DB=vitruvyan_core \
  -e POSTGRES_USER=vitruvyan_core_user \
  -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD} \
  -e REDIS_HOST=core_redis \
  -e REDIS_PORT=6379 \
  aegis_intake:latest
```

### 3. Health Check

```bash
curl http://localhost:9050/health
```

Expected response:
```json
{"status": "healthy", "service": "aegis_intake", "version": "1.0.0"}
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/intake/document` | Ingest a document (PDF, TXT, etc.) |
| POST | `/intake/media` | Ingest media (image, video, audio) |
| POST | `/intake/api` | Ingest from external API |
| GET | `/evidence/{evidence_id}` | Retrieve Evidence Pack by ID |
| GET | `/health` | Service health check |
| GET | `/metrics` | Prometheus metrics |

---

## Integration with Vitruvyan Core

### Event Emission

Intake emits `intake.evidence.created` events to the Cognitive Bus (Redis Streams):

**Event Schema** (`event_evidence_created_v1.json`):
```json
{
  "evidence_id": "EVD-<UUID>",
  "chunk_id": "CHK-1",
  "source_type": "document",
  "normalized_text": "...",
  "created_utc": "2026-02-16T19:30:00Z",
  "schema_ref": "aegis://intake/evidence_pack/v1.0"
}
```

**Event Bus Channel**: `intake.evidence.created`

### Downstream Consumers

- **Codex Hunters**: Index Evidence Packs for semantic search
- **Memory Orders**: Store Evidence Packs in long-term memory
- **Pattern Weavers**: Extract entities and ontology mappings
- **Orthodoxy Wardens**: Validate integrity and compliance

---

## Compliance

All intake operations MUST comply with:

- **ACCORDO-FONDATIVO-INTAKE-V1.1**: Foundational contract
- **INTAKE_CODEX_BOUNDARY_CONTRACT.md**: Codex Hunters integration rules
- **COMPLIANCE_CHECKLIST.md**: Pre-deployment verification

---

## Documentation

- **Core README**: [intake/core/README.md](core/README.md)
- **Compliance Checklist**: [intake/core/COMPLIANCE_CHECKLIST.md](core/COMPLIANCE_CHECKLIST.md)
- **Codex Contract**: [intake/core/INTAKE_CODEX_BOUNDARY_CONTRACT.md](core/INTAKE_CODEX_BOUNDARY_CONTRACT.md)

---

## Development Notes

- **Origin**: Imported from `aegis` vertical (Feb 16, 2026)
- **Python Version**: 3.11+
- **Dependencies**: FastAPI, psycopg2-binary, redis, pydantic
- **Testing**: Unit tests pending (import from aegis/tests)

---

## Next Steps

1. ✅ Import core module from aegis
2. ✅ Import service API from aegis
3. ✅ Import database schema
4. ⏳ Add intake service to vitruvyan-core docker-compose.yml
5. ⏳ Configure environment variables
6. ⏳ Run integration tests
7. ⏳ Deploy to production VPS

---

**Last Updated**: Feb 16, 2026  
**Maintainer**: AEGIS Team  
**Status**: Imported, pending integration
