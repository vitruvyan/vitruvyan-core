# Orthodoxy Wardens API Reference

**Last Updated**: February 8, 2026  
**Base URL**: `http://localhost:9006` (production), `http://localhost:8006` (container-internal)  
**API Version**: 1.3.0

---

## Table of Contents

1. [Authentication](#authentication)
2. [Health & Monitoring](#health--monitoring)
3. [Audit Endpoints](#audit-endpoints)
4. [Event Emission](#event-emission)
5. [Query Endpoints](#query-endpoints)
6. [Error Handling](#error-handling)
7. [Rate Limiting](#rate-limiting)
8. [Webhooks](#webhooks)

---

## 1. Authentication

### Current Status
**No authentication required** (internal service, protected by network isolation).

### Future Roadmap (Q2 2026)
- JWT-based authentication
- API key support for external integrations
- Role-based access control (RBAC)

---

## 2. Health & Monitoring

### GET /divine-health

**Description**: Check service health and Sacred Roles status.

**Request**:
```http
GET /divine-health HTTP/1.1
Host: localhost:9006
```

**Response** (200 OK):
```json
{
  "sacred_status": "blessed",
  "divine_council": {
    "confessor": "blessed",
    "penitent": "blessed",
    "chronicler": "blessed",
    "inquisitor": "blessed",
    "abbot": "blessed",
    "sacred_interface": "blessed",
    "orthodoxy_db": "corrupted",
    "sacred_guardrails": "unprotected"
  },
  "timestamp": "2026-02-08T18:48:00.123456Z",
  "blessing_level": 0.875
}
```

**Response Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `sacred_status` | string | Overall status: `blessed` (90%+), `purifying` (70-90%), `cursed` (<70%) |
| `divine_council` | object | Status map for each component |
| `divine_council.<role>` | string | Role status: `blessed` (operational), `absent_from_prayers` (not initialized), `silent` (LLM unavailable), `corrupted` (DB connection failed), `unprotected` (feature not enabled) |
| `timestamp` | string | ISO 8601 timestamp |
| `blessing_level` | number | Percentage of operational components (0.0-1.0) |

**Status Interpretation**:
- `blessing_level >= 0.9` → `sacred_status = "blessed"` (production-ready)
- `0.7 <= blessing_level < 0.9` → `sacred_status = "purifying"` (degraded, non-critical failures)
- `blessing_level < 0.7` → `sacred_status = "cursed"` (major failures, service unusable)

**cURL Example**:
```bash
curl http://localhost:9006/divine-health | jq .
```

**Python Example**:
```python
import requests

response = requests.get("http://localhost:9006/divine-health")
data = response.json()

if data["sacred_status"] == "blessed":
    print("✅ Service healthy")
elif data["sacred_status"] == "purifying":
    print("⚠️ Service degraded")
else:
    print("❌ Service unhealthy")
```

**Error Responses**:
- `503 Service Unavailable`: Service not fully initialized (startup in progress)

---

## 3. Audit Endpoints

### POST /confession/initiate

**Description**: Initiate compliance audit workflow (asynchronous).

**Request**:
```http
POST /confession/initiate HTTP/1.1
Host: localhost:9006
Content-Type: application/json

{
  "confession_type": "system_compliance",
  "sacred_scope": "neural_engine",
  "urgency": "divine_routine",
  "penitent_service": "neural_engine"
}
```

**Request Fields**:
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `confession_type` | string | No | `"system_compliance"` | Audit type. Values: `system_compliance`, `security_audit`, `performance_review` |
| `sacred_scope` | string | No | `"complete_realm"` | Scope of audit. Values: `complete_realm`, service name (e.g., `neural_engine`, `babel_gardens`) |
| `urgency` | string | No | `"divine_routine"` | Priority level. Values: `divine_routine` (low), `sacred_priority` (medium), `holy_emergency` (high) |
| `penitent_service` | string | No | `null` | Service requesting audit (for tracking) |

**Response** (200 OK):
```json
{
  "confession_id": "confession_20260208_184800",
  "sacred_status": "confessing",
  "penance_progress": 0.0,
  "divine_results": null,
  "timestamp": "2026-02-08T18:48:00.123456Z",
  "assigned_warden": "Confessor"
}
```

**Response Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `confession_id` | string | Unique audit identifier (format: `confession_YYYYMMDD_HHMMSS`) |
| `sacred_status` | string | Audit state: `confessing` (in progress), `purifying` (corrections running), `absolved` (passed), `condemned` (failed) |
| `penance_progress` | number | Completion percentage (0.0-1.0) |
| `divine_results` | object\|null | Audit results (null while in progress) |
| `timestamp` | string | ISO 8601 audit initiation timestamp |
| `assigned_warden` | string | Sacred Role handling audit (typically `Confessor`) |

**Event Flow**:
```
POST /confession/initiate
  ↓
Emit: orthodoxy.audit.requested
  ↓
Inquisitor investigates (evidence gathering)
  ↓
Confessor audits (validation)
  ↓
Abbot finalizes (verdict)
  ↓
Emit: orthodoxy.audit.completed
```

**Polling for Results**:
Use `GET /confession/status/{confession_id}` to poll audit progress.

**cURL Example**:
```bash
curl -X POST http://localhost:9006/confession/initiate \
  -H "Content-Type: application/json" \
  -d '{
    "confession_type": "system_compliance",
    "sacred_scope": "babel_gardens",
    "urgency": "sacred_priority"
  }' | jq .
```

**Python Example**:
```python
import requests

response = requests.post(
    "http://localhost:9006/confession/initiate",
    json={
        "confession_type": "system_compliance",
        "sacred_scope": "neural_engine",
        "urgency": "divine_routine"
    }
)

data = response.json()
confession_id = data["confession_id"]
print(f"Audit initiated: {confession_id}")
```

**Error Responses**:
- `503 Service Unavailable`: Confessor not initialized
- `500 Internal Server Error`: Audit initiation failed (check logs)

---

### GET /confession/status/{confession_id}

**Description**: Query audit status and results.

**Request**:
```http
GET /confession/status/confession_20260208_184800 HTTP/1.1
Host: localhost:9006
```

**Response** (200 OK - In Progress):
```json
{
  "confession_id": "confession_20260208_184800",
  "sacred_status": "confessing",
  "penance_progress": 0.65,
  "divine_results": null,
  "timestamp": "2026-02-08T18:48:30.123456Z",
  "assigned_warden": "Confessor"
}
```

**Response** (200 OK - Completed):
```json
{
  "confession_id": "confession_20260208_184800",
  "sacred_status": "absolved",
  "penance_progress": 1.0,
  "divine_results": {
    "compliance_level": 0.85,
    "findings": [
      {
        "severity": "warning",
        "category": "data_quality",
        "message": "35% of sentiment scores are neutral (expected: <20%)",
        "evidence": {"neutral_count": 3500, "total": 10000}
      },
      {
        "severity": "info",
        "category": "performance",
        "message": "Average response time within acceptable range (150ms)",
        "evidence": {"avg_latency_ms": 150, "p95_latency_ms": 280}
      }
    ],
    "recommendations": [
      "Review sentiment model calibration",
      "Monitor neutral classification rate",
      "Investigate input data distribution"
    ],
    "verdict": "approved",
    "rationale": "Compliance within acceptable range (85%), no critical findings"
  },
  "timestamp": "2026-02-08T18:49:15.123456Z",
  "assigned_warden": "Abbot"
}
```

**Response Fields** (divine_results):
| Field | Type | Description |
|-------|------|-------------|
| `compliance_level` | number | Overall compliance score (0.0-1.0) |
| `findings` | array | List of issues discovered |
| `findings[].severity` | string | Issue severity: `critical`, `warning`, `info` |
| `findings[].category` | string | Issue category: `data_quality`, `performance`, `security`, `architecture` |
| `findings[].message` | string | Human-readable description |
| `findings[].evidence` | object | Supporting data (metrics, logs) |
| `recommendations` | array | Actionable next steps |
| `verdict` | string | Final decision: `approved`, `requires_action`, `rejected` |
| `rationale` | string | Explanation for verdict |

**cURL Example**:
```bash
curl http://localhost:9006/confession/status/confession_20260208_184800 | jq .
```

**Python Example**:
```python
import requests
import time

confession_id = "confession_20260208_184800"

# Poll until complete
while True:
    response = requests.get(f"http://localhost:9006/confession/status/{confession_id}")
    data = response.json()
    
    if data["sacred_status"] in ["absolved", "condemned"]:
        print(f"Audit complete: {data['divine_results']['verdict']}")
        break
    
    print(f"Audit in progress: {data['penance_progress']:.0%}")
    time.sleep(5)
```

**Error Responses**:
- `404 Not Found`: Confession ID invalid or expired
- `500 Internal Server Error`: Status query failed

---

### POST /confession/cancel/{confession_id}

**Description**: Cancel ongoing audit (TODO - not implemented yet).

**Planned Implementation** (Q2 2026):
```http
POST /confession/cancel/confession_20260208_184800 HTTP/1.1
Host: localhost:9006
```

**Response** (200 OK):
```json
{
  "confession_id": "confession_20260208_184800",
  "cancelled": true,
  "timestamp": "2026-02-08T18:50:00.123456Z"
}
```

---

## 4. Event Emission

### GET /sacred-channels

**Description**: List active Synaptic Conclave channels and consumer status.

**Request**:
```http
GET /sacred-channels HTTP/1.1
Host: localhost:9006
```

**Response** (200 OK):
```json
{
  "channels": [
    {
      "name": "orthodoxy.audit.requested",
      "handler": "handle_audit_request",
      "consumer_group": "group:orthodoxy_main",
      "consumer_id": "orthodoxy_main:worker_1",
      "status": "active",
      "pending_events": 0,
      "processed_events": 1253
    },
    {
      "name": "neural_engine.screening.completed",
      "handler": "handle_system_events",
      "consumer_group": "group:orthodoxy_main",
      "consumer_id": "orthodoxy_main:worker_1",
      "status": "active",
      "pending_events": 2,
      "processed_events": 8947
    }
  ],
  "total_channels": 7,
  "active_channels": 7,
  "listener_thread": "running"
}
```

**Response Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `channels` | array | List of Redis Streams channels |
| `channels[].name` | string | Stream name (e.g., `orthodoxy.audit.requested`) |
| `channels[].handler` | string | Python function handling events |
| `channels[].consumer_group` | string | Redis Streams consumer group |
| `channels[].consumer_id` | string | Consumer identifier |
| `channels[].status` | string | Channel status: `active`, `paused`, `error` |
| `channels[].pending_events` | number | Unacknowledged events count |
| `channels[].processed_events` | number | Total processed since startup |
| `total_channels` | number | Configured channel count |
| `active_channels` | number | Channels currently consuming |
| `listener_thread` | string | Background thread status: `running`, `stopped`, `error` |

**cURL Example**:
```bash
curl http://localhost:9006/sacred-channels | jq .
```

**Error Responses**:
- `503 Service Unavailable`: Listener thread not started

---

## 5. Query Endpoints

### GET /logs/recent

**Description**: Query recent compliance events from PostgreSQL.

**Request**:
```http
GET /logs/recent?service=neural_engine&limit=20 HTTP/1.1
Host: localhost:9006
```

**Query Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `service` | string | No | All | Filter by service name |
| `event_type` | string | No | All | Filter by event type |
| `limit` | number | No | `50` | Max results (1-500) |
| `offset` | number | No | `0` | Pagination offset |

**Response** (200 OK):
```json
{
  "logs": [
    {
      "id": 12345,
      "event_type": "neural_engine.screening.completed",
      "service": "neural_engine",
      "payload": {
        "tickers": ["AAPL", "NVDA"],
        "composite_z": 1.85,
        "profile": "momentum_focus"
      },
      "timestamp": "2026-02-08T18:45:30.123456Z"
    },
    {
      "id": 12344,
      "event_type": "babel.sentiment.completed",
      "service": "babel_gardens",
      "payload": {
        "ticker": "AAPL",
        "sentiment_z": 0.65,
        "confidence": 0.85
      },
      "timestamp": "2026-02-08T18:44:15.987654Z"
    }
  ],
  "total": 8947,
  "limit": 20,
  "offset": 0,
  "service_filter": "neural_engine"
}
```

**Response Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `logs` | array | List of compliance events |
| `logs[].id` | number | Database primary key |
| `logs[].event_type` | string | Event classification |
| `logs[].service` | string | Originating service |
| `logs[].payload` | object | Event data (JSONB) |
| `logs[].timestamp` | string | ISO 8601 event timestamp |
| `total` | number | Total matching logs |
| `limit` | number | Applied limit |
| `offset` | number | Applied offset |
| `service_filter` | string | Applied service filter |

**cURL Example**:
```bash
curl "http://localhost:9006/logs/recent?service=neural_engine&limit=10" | jq .
```

**Python Example**:
```python
import requests

response = requests.get(
    "http://localhost:9006/logs/recent",
    params={"service": "babel_gardens", "limit": 50}
)

data = response.json()
for log in data["logs"]:
    print(f"{log['timestamp']} - {log['event_type']}")
```

**Error Responses**:
- `400 Bad Request`: Invalid query parameters
- `500 Internal Server Error`: Database query failed

---

### GET /analytics/compliance-trend

**Description**: Get compliance level trend over time (TODO - not implemented yet).

**Planned Implementation** (Q2 2026):
```http
GET /analytics/compliance-trend?service=neural_engine&days=7 HTTP/1.1
Host: localhost:9006
```

**Response** (200 OK):
```json
{
  "service": "neural_engine",
  "timeframe_days": 7,
  "data_points": [
    {"date": "2026-02-02", "compliance_level": 0.82},
    {"date": "2026-02-03", "compliance_level": 0.85},
    {"date": "2026-02-04", "compliance_level": 0.87},
    {"date": "2026-02-05", "compliance_level": 0.83},
    {"date": "2026-02-06", "compliance_level": 0.86},
    {"date": "2026-02-07", "compliance_level": 0.88},
    {"date": "2026-02-08", "compliance_level": 0.90}
  ],
  "trend": "improving",
  "average_compliance": 0.86
}
```

---

## 6. Error Handling

### Error Response Format

**Standard Error Structure**:
```json
{
  "detail": "Human-readable error message",
  "error_code": "ERROR_CODE",
  "timestamp": "2026-02-08T18:48:00.123456Z",
  "request_id": "req_abc123def456"
}
```

**Error Response Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `detail` | string | Error message |
| `error_code` | string | Machine-readable error code |
| `timestamp` | string | ISO 8601 error timestamp |
| `request_id` | string | Unique request identifier (for debugging) |

### HTTP Status Codes

| Code | Meaning | When Used |
|------|---------|-----------|
| `200 OK` | Success | Request completed successfully |
| `400 Bad Request` | Invalid input | Malformed request body or query parameters |
| `404 Not Found` | Resource missing | Confession ID not found |
| `422 Unprocessable Entity` | Validation error | Pydantic schema validation failed |
| `500 Internal Server Error` | Server error | Unexpected exception (check logs) |
| `503 Service Unavailable` | Service degraded | Sacred Roles not initialized |

### Example Error Responses

**400 Bad Request** (Invalid query parameter):
```json
{
  "detail": "Invalid limit parameter: must be between 1 and 500",
  "error_code": "INVALID_QUERY_PARAM",
  "timestamp": "2026-02-08T18:48:00.123456Z",
  "request_id": "req_abc123def456"
}
```

**404 Not Found** (Confession not found):
```json
{
  "detail": "Confession ID 'confession_99999999_999999' not found",
  "error_code": "CONFESSION_NOT_FOUND",
  "timestamp": "2026-02-08T18:48:00.123456Z",
  "request_id": "req_abc123def456"
}
```

**503 Service Unavailable** (Confessor absent):
```json
{
  "detail": "Confessor is absent from sacred duties",
  "error_code": "SERVICE_UNAVAILABLE",
  "timestamp": "2026-02-08T18:48:00.123456Z",
  "request_id": "req_abc123def456"
}
```

**Python Error Handling**:
```python
import requests

try:
    response = requests.post("http://localhost:9006/confession/initiate", json={...})
    response.raise_for_status()  # Raise HTTPError for bad status codes
    data = response.json()
except requests.exceptions.HTTPError as e:
    error_data = e.response.json()
    print(f"Error ({e.response.status_code}): {error_data['detail']}")
except requests.exceptions.ConnectionError:
    print("Service unreachable - check container status")
```

---

## 7. Rate Limiting

### Current Status
**No rate limiting** (internal service, trusted consumers).

### Future Roadmap (Q2 2026)

**Planned Limits**:
- `/confession/initiate`: 10 requests/minute per IP
- `/logs/recent`: 30 requests/minute per IP
- `/divine-health`: 60 requests/minute per IP

**Rate Limit Headers** (planned):
```http
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1707415680
```

**Rate Limit Exceeded Response** (429 Too Many Requests):
```json
{
  "detail": "Rate limit exceeded: 10 requests/minute allowed",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "retry_after_seconds": 45,
  "timestamp": "2026-02-08T18:48:00.123456Z"
}
```

---

## 8. Webhooks

### POST /webhooks/register

**Description**: Register webhook for audit completion events (TODO - not implemented yet).

**Planned Implementation** (Q3 2026):
```http
POST /webhooks/register HTTP/1.1
Host: localhost:9006
Content-Type: application/json

{
  "url": "https://external-service.com/webhook/orthodoxy",
  "events": ["audit.completed", "heresy.detected"],
  "secret": "webhook_secret_key"
}
```

**Response** (201 Created):
```json
{
  "webhook_id": "wh_abc123def456",
  "url": "https://external-service.com/webhook/orthodoxy",
  "events": ["audit.completed", "heresy.detected"],
  "status": "active",
  "created_at": "2026-02-08T18:48:00.123456Z"
}
```

**Webhook Payload** (when event fires):
```http
POST /webhook/orthodoxy HTTP/1.1
Host: external-service.com
Content-Type: application/json
X-Webhook-Signature: sha256=abc123...
X-Webhook-Event: audit.completed

{
  "event_type": "audit.completed",
  "confession_id": "confession_20260208_184800",
  "compliance_level": 0.85,
  "verdict": "approved",
  "timestamp": "2026-02-08T18:49:15.123456Z"
}
```

**Signature Verification** (HMAC SHA-256):
```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected, signature)
```

---

## API Changelog

### Version 1.3.0 (February 8, 2026)
- ✅ P1 FASE 3: Business logic separation (core/ created)
- ✅ Sacred Roles dependency injection via event_handlers
- ✅ Background listener thread (non-blocking startup)

### Version 1.2.0 (February 8, 2026)
- ✅ P1 FASE 2: English documentation
- ✅ Health check endpoint enhancements

### Version 1.1.0 (February 8, 2026)
- ✅ P1 FASE 1: Synaptic Conclave listeners (7 channels)
- ✅ Consumer group architecture

### Version 1.0.0 (January 2026)
- 🚀 Initial production deployment
- ✅ `/divine-health` endpoint
- ✅ `/confession/initiate` endpoint
- ✅ `/confession/status/{id}` endpoint
- ✅ Redis Streams integration

---

## Client Libraries

### Python SDK (Planned Q2 2026)

```python
from orthodoxy_wardens import OrthodoxyClient

client = OrthodoxyClient(base_url="http://localhost:9006")

# Check health
health = client.health()
print(f"Status: {health.sacred_status}")

# Initiate audit
audit = client.initiate_audit(
    scope="neural_engine",
    urgency="high"
)
print(f"Audit ID: {audit.confession_id}")

# Poll for completion
result = client.wait_for_audit(audit.confession_id, timeout=300)
print(f"Verdict: {result.verdict}")
```

### JavaScript SDK (Planned Q3 2026)

```javascript
import { OrthodoxyClient } from '@vitruvyan/orthodoxy-wardens';

const client = new OrthodoxyClient({ baseUrl: 'http://localhost:9006' });

// Check health
const health = await client.health();
console.log(`Status: ${health.sacred_status}`);

// Initiate audit
const audit = await client.initiateAudit({
  scope: 'neural_engine',
  urgency: 'high'
});
console.log(`Audit ID: ${audit.confession_id}`);

// Wait for completion
const result = await client.waitForAudit(audit.confession_id);
console.log(`Verdict: ${result.verdict}`);
```

---

## Support & Contact

**Issues**: Open GitHub issue at `vitruvyan-core` repository  
**Email**: orthodoxy-support@vitruvyan.ai (if email system exists)  
**Documentation**: [ORTHODOXY_WARDENS_GUIDE.md](./ORTHODOXY_WARDENS_GUIDE.md)  
**Architecture**: [ARCHITECTURAL_DECISIONS.md](./ARCHITECTURAL_DECISIONS.md)

---

**Last Updated**: February 8, 2026  
**Maintainer**: Vitruvyan Core Team  
**License**: Proprietary
