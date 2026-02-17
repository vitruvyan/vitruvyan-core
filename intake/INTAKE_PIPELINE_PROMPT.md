# AEGIS Intake Pipeline — Complete Data Flow Reference

> **Purpose**: Comprehensive prompt for Copilot refactoring Intake in vitruvyan-core  
> **Date**: Feb 16, 2026  
> **Source**: aegis vertical → vitruvyan-core integration  
> **Target**: Implement Intake node in LangGraph orchestration

---

## 📋 Executive Summary

**Intake** is the **pre-epistemic acquisition layer** responsible for:
1. Accepting file uploads (documents, images, audio, video, CAD, geo data)
2. Extracting **literal, descriptive text** (NO semantic interpretation)
3. Creating **immutable Evidence Packs** (append-only PostgreSQL storage)
4. Emitting **`intake.evidence.created`** events to Redis Cognitive Bus
5. Triggering downstream processing (Codex Hunters → Pattern Weavers → Memory Orders)

**Critical Constraint**: Intake MUST NOT perform semantic analysis, entity extraction, or relevance judgment. It is **purely acquisitional**.

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│  USER / EXTERNAL SYSTEM                                             │
└─────────────────────────────────────────────────────────────────────┘
                          │
                          │ HTTP POST /api/intake/{type}
                          │ (multipart/form-data)
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│  INTAKE API SERVICE (FastAPI)                                       │
│  Port: 8050 (external: 9050)                                        │
│                                                                      │
│  Endpoints:                                                          │
│  - POST /api/intake/document                                        │
│  - POST /api/intake/image                                           │
│  - POST /api/intake/audio                                           │
│  - POST /api/intake/video                                           │
│  - POST /api/intake/landscape                                       │
│  - POST /api/intake/geo                                             │
│  - POST /api/intake/cad                                             │
│  - GET  /api/intake/evidence/{evidence_id}                          │
└─────────────────────────────────────────────────────────────────────┘
                          │
                          │ File saved to /app/uploads/
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│  INTAKE AGENT (Media-Specific)                                      │
│                                                                      │
│  Agents:                                                             │
│  - DocumentIntakeAgent      (PDF, DOCX, MD, TXT, JSON, XML)        │
│  - ImageIntakeAgent         (JPG, PNG, TIFF + OCR)                 │
│  - AudioIntakeAgent         (MP3, WAV + Whisper STT)               │
│  - VideoStreamIntakeAgent   (MP4, AVI + keyframes + audio)         │
│  - LandscapeIntakeAgent     (Satellite imagery + geo metadata)     │
│  - GeoIntakeAgent           (GeoJSON, KML, Shapefiles)             │
│  - CADIntakeAgent           (DXF, IFC, RVT + literal extraction)   │
│                                                                      │
│  Operations:                                                         │
│  1. Compute source_hash (SHA-256)                                   │
│  2. Extract text/metadata (format-specific logic)                   │
│  3. Apply chunking (if sampling_policy requires)                    │
│  4. Generate evidence_id (UUID)                                     │
│  5. Create Evidence Pack (JSON structure)                           │
└─────────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│  POSTGRESQL (Append-Only Storage)                                   │
│                                                                      │
│  Tables:                                                             │
│  - evidence_packs          (core immutable storage)                 │
│  - intake_event_log        (audit trail for events)                │
│  - intake_event_failures   (retry diagnostics)                     │
│  - intake_sessions         (session metadata, optional)            │
│                                                                      │
│  INSERT Evidence Pack:                                               │
│  - evidence_id: EVD-{UUID}                                          │
│  - chunk_id: CHK-{N}                                                │
│  - source_ref: {source_type, source_uri, source_hash, mime_type}   │
│  - normalized_text: "literal extracted text..."                     │
│  - technical_metadata: {extraction_method, language, confidence}    │
│  - integrity: {evidence_hash, immutable: true}                      │
│  - sampling_policy_ref: SAMPPOL-DOC-DEFAULT-V1                      │
│  - tags: []                                                          │
└─────────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│  EVENT EMITTER (IntakeEventEmitter)                                 │
│                                                                      │
│  Generate idempotency_key:                                           │
│  - SHA-256(evidence_id + chunk_id + source_hash)                    │
│                                                                      │
│  Build event payload:                                                │
│  {                                                                   │
│    "event_id": "EVT-{UUID}",                                        │
│    "event_version": "1.0.0",                                        │
│    "schema_ref": "aegis://intake/events/evidence_created/v1.0",    │
│    "timestamp": "2026-02-16T20:00:00Z",                            │
│    "evidence_id": "EVD-12345678...",                               │
│    "chunk_id": "CHK-0",                                            │
│    "idempotency_key": "abc123...",                                 │
│    "payload": {                                                     │
│      "source_type": "document",                                    │
│      "source_uri": "/uploads/report.pdf",                          │
│      "evidence_pack_ref": "postgres://evidence_packs/12345",       │
│      "source_hash": "sha256:...",                                  │
│      "byte_size": 1024000,                                         │
│      "language_detected": "en",                                    │
│      "sampling_policy_ref": "SAMPPOL-DOC-DEFAULT-V1"               │
│    },                                                               │
│    "metadata": {                                                    │
│      "intake_agent_id": "document-intake-v1",                      │
│      "intake_agent_version": "1.0.0",                              │
│      "correlation_id": "trace-12345",                              │
│      "retry_count": 0                                              │
│    }                                                                │
│  }                                                                   │
└─────────────────────────────────────────────────────────────────────┘
                          │
                          │ redis_client.publish("intake.evidence.created", event_json)
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│  REDIS COGNITIVE BUS (Synaptic Conclave)                            │
│                                                                      │
│  Channel: intake.evidence.created                                   │
│  Transport: Redis Pub/Sub OR Redis Streams                          │
│                                                                      │
│  Event flows to downstream consumers (async, eventual consistency)  │
└─────────────────────────────────────────────────────────────────────┘
                          │
                          │ Event consumed by subscribers
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│  CODEX HUNTERS (Epistemic Enrichment)                               │
│                                                                      │
│  Consumer: codex_hunters_listener.py                                │
│                                                                      │
│  1. Consume event from Redis (intake.evidence.created)              │
│  2. Check idempotency_key (skip if duplicate)                       │
│  3. Retrieve Evidence Pack from PostgreSQL (by evidence_id)         │
│  4. Perform semantic enrichment:                                     │
│     - Named Entity Recognition (NER)                                │
│     - Relationship extraction                                       │
│     - Embedding generation (SentenceTransformer)                    │
│     - Language detection refinement                                 │
│  5. Store enriched entities in:                                     │
│     - PostgreSQL (entities table)                                   │
│     - Qdrant (vector embeddings)                                    │
│  6. Emit downstream event:                                          │
│     - codex.entity.created                                          │
└─────────────────────────────────────────────────────────────────────┘
                          │
                          │ codex.entity.created event
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PATTERN WEAVERS (Ontology Mapping)                                 │
│                                                                      │
│  1. Consume codex.entity.created event                              │
│  2. Map entities to ontology (industry, domain, category)           │
│  3. Extract concepts and relationships                              │
│  4. Update Knowledge Graph                                          │
│  5. Emit pattern.concept.linked event                               │
└─────────────────────────────────────────────────────────────────────┘
                          │
                          │ pattern.concept.linked event
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│  MEMORY ORDERS (Long-Term Memory)                                   │
│                                                                      │
│  1. Consume pattern.concept.linked event                            │
│  2. Assess memory coherence (semantic clustering)                   │
│  3. Store in long-term memory (episodic + semantic)                 │
│  4. Update memory indexes                                           │
│  5. Emit memory.stored event                                        │
└─────────────────────────────────────────────────────────────────────┘
                          │
                          │ memory.stored event
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│  VAULT KEEPERS (Archival & Persistence)                             │
│                                                                      │
│  1. Consume memory.stored event                                     │
│  2. Archive evidence + enriched metadata                            │
│  3. Create backup snapshots                                         │
│  4. Emit vault.archived event                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Step-by-Step Data Flow (Document Example)

### **STEP 1: User Upload**
```http
POST /api/intake/document
Content-Type: multipart/form-data

file: Q4_2025_Financial_Report.pdf
sampling_policy_ref: SAMPPOL-DOC-DEFAULT-V1
correlation_id: trace-user-12345
```

### **STEP 2: Intake API Receives Request**
```python
# intake/service/main.py
@app.post("/api/intake/document")
async def intake_document(
    file: UploadFile = File(...),
    sampling_policy_ref: str = Form(None),
    correlation_id: str = Form(None)
):
    # Save file to /app/uploads/
    file_path = f"/app/uploads/{file.filename}"
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    # Initialize agent
    postgres = PostgresAgent()
    event_emitter = IntakeEventEmitter(redis_client, postgres)
    agent = DocumentIntakeAgent(event_emitter, postgres)
    
    # Ingest document
    evidence_ids = agent.ingest_document(
        source_path=file_path,
        sampling_policy_ref=sampling_policy_ref,
        correlation_id=correlation_id
    )
    
    return {"evidence_ids": evidence_ids}
```

### **STEP 3: Document Agent Extracts Text**
```python
# intake/core/agents/document_intake.py
def ingest_document(self, source_path, sampling_policy_ref, correlation_id):
    # 1. Compute source_hash
    source_hash = hashlib.sha256(open(source_path, 'rb').read()).hexdigest()
    
    # 2. Extract text (format-specific)
    if source_path.suffix == '.pdf':
        with pdfplumber.open(source_path) as pdf:
            text = "\n".join([page.extract_text() for page in pdf.pages])
    elif source_path.suffix == '.docx':
        doc = DocxDocument(source_path)
        text = "\n".join([para.text for para in doc.paragraphs])
    # ... other formats
    
    # 3. Detect language
    language = detect(text)  # langdetect
    
    # 4. Apply chunking (if policy requires)
    chunks = self._chunk_text(text, strategy="size", chunk_size=4000)
    
    # 5. Create Evidence Packs
    evidence_ids = []
    for idx, chunk_text in enumerate(chunks):
        evidence_id = f"EVD-{uuid.uuid4()}"
        chunk_id = f"CHK-{idx}"
        
        # Insert into PostgreSQL
        self._persist_evidence_pack(
            evidence_id=evidence_id,
            chunk_id=chunk_id,
            source_ref={
                "source_type": "document",
                "source_uri": source_path,
                "source_hash": f"sha256:{source_hash}",
                "mime_type": "application/pdf",
                "byte_size": os.path.getsize(source_path)
            },
            normalized_text=chunk_text,
            technical_metadata={
                "extraction_method": "pdfplumber",
                "language_detected": language,
                "chunk_position": {"index": idx, "total": len(chunks)}
            },
            integrity={"evidence_hash": hashlib.sha256(chunk_text.encode()).hexdigest()},
            sampling_policy_ref=sampling_policy_ref
        )
        
        # Emit event
        self.event_emitter.emit_evidence_created(
            evidence_id=evidence_id,
            chunk_id=chunk_id,
            source_type="document",
            source_uri=source_path,
            evidence_pack_ref=f"postgres://evidence_packs/{evidence_id}",
            source_hash=f"sha256:{source_hash}",
            intake_agent_id="document-intake-v1",
            intake_agent_version="1.0.0",
            byte_size=os.path.getsize(source_path),
            language_detected=language,
            sampling_policy_ref=sampling_policy_ref,
            correlation_id=correlation_id
        )
        
        evidence_ids.append(evidence_id)
    
    return evidence_ids
```

### **STEP 4: Event Emission to Redis**
```python
# intake/core/event_emitter.py
def emit_evidence_created(self, evidence_id, chunk_id, source_type, ...):
    # Generate idempotency key
    idempotency_key = hashlib.sha256(
        f"{evidence_id}{chunk_id}{source_hash}".encode()
    ).hexdigest()
    
    # Build event
    event = {
        "event_id": f"EVT-{uuid.uuid4()}",
        "event_version": "1.0.0",
        "schema_ref": "aegis://intake/events/evidence_created/v1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "evidence_id": evidence_id,
        "chunk_id": chunk_id,
        "idempotency_key": idempotency_key,
        "payload": {
            "source_type": source_type,
            "source_uri": source_uri,
            "evidence_pack_ref": evidence_pack_ref,
            "source_hash": source_hash,
            "byte_size": byte_size,
            "language_detected": language_detected,
            "sampling_policy_ref": sampling_policy_ref
        },
        "metadata": {
            "intake_agent_id": intake_agent_id,
            "intake_agent_version": intake_agent_version,
            "correlation_id": correlation_id,
            "retry_count": 0
        }
    }
    
    # Emit to Redis
    self.redis_client.publish("intake.evidence.created", json.dumps(event))
    
    # Log to PostgreSQL audit
    self._log_event_emission(event)
```

### **STEP 5: Codex Hunters Consume Event**
```python
# services/api_codex_hunters/streams_listener.py
def consume_intake_events():
    while True:
        message = redis_client.subscribe("intake.evidence.created")
        event = json.loads(message['data'])
        
        # Check idempotency
        if is_duplicate(event['idempotency_key']):
            continue  # Skip duplicate
        
        # Retrieve Evidence Pack from PostgreSQL
        evidence_pack = postgres.fetch_one(
            "SELECT * FROM evidence_packs WHERE evidence_id = %s",
            (event['evidence_id'],)
        )
        
        # Perform NER + embeddings
        entities = ner_extract(evidence_pack['normalized_text'])
        embeddings = sentence_transformer.encode(evidence_pack['normalized_text'])
        
        # Store in Qdrant + PostgreSQL
        qdrant.upsert(collection="evidence", points=[{
            "id": event['evidence_id'],
            "vector": embeddings.tolist(),
            "payload": {"text": evidence_pack['normalized_text'], "entities": entities}
        }])
        
        # Emit downstream event
        redis_client.publish("codex.entity.created", json.dumps({
            "evidence_id": event['evidence_id'],
            "entities": entities,
            "embedding_stored": True
        }))
```

### **STEP 6: Pattern Weavers Map Ontology**
```python
# services/api_pattern_weavers/streams_listener.py
def consume_codex_events():
    message = redis_client.subscribe("codex.entity.created")
    event = json.loads(message['data'])
    
    # Map entities to ontology
    for entity in event['entities']:
        ontology_class = ontology_mapper.map(entity['text'], entity['type'])
        
        # Update Knowledge Graph
        knowledge_graph.add_node(entity['text'], ontology_class=ontology_class)
    
    # Emit downstream
    redis_client.publish("pattern.concept.linked", json.dumps({
        "evidence_id": event['evidence_id'],
        "concepts_linked": len(event['entities'])
    }))
```

### **STEP 7: Memory Orders Store Long-Term**
```python
# services/api_memory_orders/streams_listener.py
def consume_pattern_events():
    message = redis_client.subscribe("pattern.concept.linked")
    event = json.loads(message['data'])
    
    # Assess coherence
    coherence_score = compute_coherence(event['evidence_id'])
    
    # Store in long-term memory
    memory_store.insert(event['evidence_id'], coherence=coherence_score)
    
    # Emit downstream
    redis_client.publish("memory.stored", json.dumps({
        "evidence_id": event['evidence_id'],
        "coherence": coherence_score
    }))
```

### **STEP 8: Vault Keepers Archive**
```python
# services/api_vault_keepers/streams_listener.py
def consume_memory_events():
    message = redis_client.subscribe("memory.stored")
    event = json.loads(message['data'])
    
    # Archive evidence + metadata
    vault.archive(event['evidence_id'], backup=True)
    
    # Emit final event
    redis_client.publish("vault.archived", json.dumps({
        "evidence_id": event['evidence_id'],
        "archived_at": datetime.utcnow().isoformat()
    }))
```

---

## 🎯 Integration with LangGraph (vitruvyan-core)

### **Objective**
Add an **`intake_node`** to the LangGraph orchestration pipeline that:
1. Accepts file uploads via HTTP or direct path
2. Routes to appropriate Intake Agent
3. Returns Evidence Pack IDs
4. Emits events to Cognitive Bus

### **Implementation Plan**

#### **1. Create intake_node.py**

```python
# vitruvyan_core/core/orchestration/langgraph/node/intake_node.py

from typing import Dict, Any
from core.orchestration.langgraph.state import OrchestratorState
import logging

logger = logging.getLogger(__name__)

def intake_node(state: OrchestratorState) -> Dict[str, Any]:
    """
    Intake node: Ingest files and create Evidence Packs
    
    Triggered when:
    - user_message contains file upload intent
    - params contain file_path or file_url
    
    Returns:
    - evidence_ids: List of created Evidence Pack IDs
    - intake_status: "success" | "error"
    - intake_message: Status message
    """
    logger.info("Executing intake_node")
    
    # Extract file info from state
    file_path = state.get("params", {}).get("file_path")
    file_type = state.get("params", {}).get("file_type", "document")
    sampling_policy = state.get("params", {}).get("sampling_policy_ref", "SAMPPOL-DOC-DEFAULT-V1")
    correlation_id = state.get("conversation_id")
    
    if not file_path:
        return {
            "intake_status": "error",
            "intake_message": "No file provided for intake",
            "evidence_ids": []
        }
    
    # Import intake agents
    from intake.core.agents.document_intake import DocumentIntakeAgent
    from intake.core.agents.image_intake import ImageIntakeAgent
    from intake.core.event_emitter import IntakeEventEmitter
    from core.agents.postgres_agent import PostgresAgent
    from core.synaptic_conclave.transport.streams import StreamBus
    
    # Initialize dependencies
    postgres = PostgresAgent()
    stream_bus = StreamBus()
    event_emitter = IntakeEventEmitter(stream_bus.redis_client, postgres)
    
    # Select agent based on file_type
    if file_type == "document":
        agent = DocumentIntakeAgent(event_emitter, postgres)
    elif file_type == "image":
        agent = ImageIntakeAgent(event_emitter, postgres)
    # ... other agents
    else:
        return {
            "intake_status": "error",
            "intake_message": f"Unsupported file type: {file_type}",
            "evidence_ids": []
        }
    
    # Ingest file
    try:
        evidence_ids = agent.ingest_document(
            source_path=file_path,
            sampling_policy_ref=sampling_policy,
            correlation_id=correlation_id
        )
        
        logger.info(f"Created {len(evidence_ids)} Evidence Packs: {evidence_ids}")
        
        return {
            "intake_status": "success",
            "intake_message": f"Ingested {len(evidence_ids)} Evidence Packs",
            "evidence_ids": evidence_ids,
            "response": f"File processed successfully. Created {len(evidence_ids)} Evidence Packs."
        }
    
    except Exception as e:
        logger.error(f"Intake failed: {e}")
        return {
            "intake_status": "error",
            "intake_message": str(e),
            "evidence_ids": []
        }
```

#### **2. Add intake_node to graph_flow.py**

```python
# vitruvyan_core/core/orchestration/langgraph/graph_flow.py

from .node.intake_node import intake_node

# ... existing imports ...

def build_graph() -> StateGraph:
    graph = StateGraph(OrchestratorState)
    
    # ... existing nodes ...
    
    # Add intake node
    graph.add_node("intake", intake_node)
    
    # Add edge from intent_detection to intake (when intent == "file_upload")
    graph.add_conditional_edges(
        "intent_detection",
        lambda state: "intake" if state.get("intent") == "file_upload" else "decide",
        {
            "intake": "intake",
            "decide": "decide"
        }
    )
    
    # After intake, continue to orchestration
    graph.add_edge("intake", "compose")
    
    return graph
```

#### **3. Update intent_detection to recognize file uploads**

```python
# vitruvyan_core/core/orchestration/langgraph/node/intent_detection_node.py

# Add intent pattern
INTENT_PATTERNS = {
    "file_upload": [
        r"upload.*file",
        r"process.*document",
        r"ingest.*pdf",
        r"analyze.*image",
        r"convert.*audio"
    ],
    # ... existing patterns
}
```

#### **4. Add HTTP endpoint for file upload**

```python
# services/api_graph/api/routes.py

from fastapi import File, UploadFile

@router.post("/intake/upload")
async def intake_upload(
    file: UploadFile = File(...),
    file_type: str = "document"
):
    """
    Upload file for intake processing
    """
    # Save file
    file_path = f"/tmp/uploads/{file.filename}"
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    # Trigger graph with intake params
    response = graph_adapter.run_graph(
        user_message=f"Process uploaded file: {file.filename}",
        params={
            "file_path": file_path,
            "file_type": file_type,
            "intent": "file_upload"
        }
    )
    
    return response
```

---

## 🚨 Critical Constraints (DO NOT VIOLATE)

### **Intake Layer MUST NOT**:
❌ Perform NER (Named Entity Recognition)  
❌ Extract entities or concepts  
❌ Generate embeddings  
❌ Apply semantic interpretation  
❌ Evaluate relevance or importance  
❌ Filter content by domain logic  
❌ Call Codex/Pattern Weavers/Memory Orders directly  
❌ Modify Evidence Packs after creation (append-only)

### **Intake Layer MUST**:
✅ Extract literal text only (descriptive, not interpretative)  
✅ Preserve source hash + integrity  
✅ Emit `intake.evidence.created` events to Redis  
✅ Log all operations to PostgreSQL audit trail  
✅ Support idempotency (duplicate detection via source_hash)  
✅ Apply external Sampling Policy (chunking, frame rate, etc.)

---

## 📦 Evidence Pack Schema (Canonical)

```json
{
  "evidence_id": "EVD-12345678-1234-5678-1234-567812345678",
  "chunk_id": "CHK-0",
  "schema_version": "1.0.0",
  "created_utc": "2026-02-16T20:00:00Z",
  "source_ref": {
    "source_type": "document",
    "source_uri": "/uploads/report.pdf",
    "source_hash": "sha256:abc123def456...",
    "mime_type": "application/pdf",
    "byte_size": 1024000
  },
  "normalized_text": "Q4 2025 Financial Report...",
  "technical_metadata": {
    "extraction_method": "pdfplumber",
    "extraction_version": "1.0.0",
    "language_detected": "en",
    "confidence_score": 0.95,
    "chunk_position": {
      "start_offset": 0,
      "end_offset": 4000,
      "total_chunks": 3
    }
  },
  "integrity": {
    "evidence_hash": "sha256:def456abc123...",
    "immutable": true,
    "signature": null
  },
  "sampling_policy_ref": "SAMPPOL-DOC-DEFAULT-V1",
  "tags": []
}
```

---

## 🔗 Event Schema: `intake.evidence.created`

```json
{
  "event_id": "EVT-12345678-1234-5678-1234-567812345678",
  "event_version": "1.0.0",
  "schema_ref": "aegis://intake/events/evidence_created/v1.0",
  "timestamp": "2026-02-16T20:00:00Z",
  "evidence_id": "EVD-12345678-1234-5678-1234-567812345678",
  "chunk_id": "CHK-0",
  "idempotency_key": "abc123def456...",
  "payload": {
    "source_type": "document",
    "source_uri": "/uploads/report.pdf",
    "evidence_pack_ref": "postgres://evidence_packs/12345",
    "source_hash": "sha256:abc123...",
    "byte_size": 1024000,
    "language_detected": "en",
    "sampling_policy_ref": "SAMPPOL-DOC-DEFAULT-V1"
  },
  "metadata": {
    "intake_agent_id": "document-intake-v1",
    "intake_agent_version": "1.0.0",
    "correlation_id": "trace-12345",
    "retry_count": 0
  }
}
```

**Idempotency Key**: `SHA-256(evidence_id + chunk_id + source_hash)`

---

## 🧪 Testing the Pipeline

### **1. Manual Test (curl)**
```bash
curl -X POST http://localhost:9050/api/intake/document \
  -F "file=@/path/to/report.pdf" \
  -F "sampling_policy_ref=SAMPPOL-DOC-DEFAULT-V1" \
  -F "correlation_id=test-12345"
```

**Expected Response**:
```json
{
  "evidence_ids": [
    "EVD-12345678-1234-5678-1234-567812345678",
    "EVD-87654321-4321-8765-4321-876543218765"
  ]
}
```

### **2. Verify Evidence Pack in PostgreSQL**
```sql
SELECT evidence_id, chunk_id, source_ref, normalized_text
FROM evidence_packs
WHERE evidence_id = 'EVD-12345678-1234-5678-1234-567812345678';
```

### **3. Verify Event Emission in Redis**
```bash
redis-cli SUBSCRIBE intake.evidence.created
```

**Expected Output**:
```json
{
  "event_id": "EVT-...",
  "evidence_id": "EVD-...",
  "payload": {
    "source_type": "document",
    "source_uri": "/uploads/report.pdf",
    ...
  }
}
```

### **4. Verify Codex Consumption**
```bash
docker logs core_codex_hunters --tail=50 | grep "EVD-12345678"
```

**Expected Output**:
```
[INFO] Consumed intake.evidence.created event: EVD-12345678...
[INFO] Extracted 15 entities from Evidence Pack
[INFO] Stored embeddings in Qdrant collection: evidence
```

---

## 📚 References

- **Core README**: [intake/core/README.md](core/README.md)
- **Boundary Contract**: [intake/core/INTAKE_CODEX_BOUNDARY_CONTRACT.md](core/INTAKE_CODEX_BOUNDARY_CONTRACT.md)
- **Compliance Checklist**: [intake/core/COMPLIANCE_CHECKLIST.md](core/COMPLIANCE_CHECKLIST.md)
- **Event Schema**: [intake/core/event_evidence_created_v1.json](core/event_evidence_created_v1.json)
- **Evidence Pack Schema**: [intake/core/evidence_pack_schema_v1.json](core/evidence_pack_schema_v1.json)
- **Database Schema**: [intake/core/schema.sql](core/schema.sql)

---

## ✅ Deployment Checklist

- [ ] Create PostgreSQL tables: `psql -f intake/core/schema.sql`
- [ ] Build Docker image: `docker build -f intake/service/Dockerfile -t aegis_intake:latest .`
- [ ] Run container: `docker run -d --name aegis_intake --network vitruvyan_core_net -p 9050:8050 aegis_intake:latest`
- [ ] Verify health: `curl http://localhost:9050/health`
- [ ] Test document upload: `curl -F "file=@test.pdf" http://localhost:9050/api/intake/document`
- [ ] Verify event emission: `redis-cli SUBSCRIBE intake.evidence.created`
- [ ] Check Codex consumption: `docker logs core_codex_hunters --tail=50`
- [ ] Integrate intake_node into LangGraph: Add node + conditional edges
- [ ] Update intent_detection: Add "file_upload" pattern
- [ ] Add HTTP endpoint: `/intake/upload` in api_graph/routes.py
- [ ] Run integration test: Upload file via LangGraph → verify Evidence Pack → verify Codex enrichment

---

**Last Updated**: Feb 16, 2026  
**Author**: AEGIS Team → vitruvyan-core integration  
**Status**: Ready for implementation
