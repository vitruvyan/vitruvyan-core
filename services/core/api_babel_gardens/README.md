# 🧠 Gemma Cognitive Layer - Unified Container

## Panoramica

Il **Gemma Cognitive Layer Unificato** rappresenta la **Fase 2** del nostro piano di transizione ibrido, combinando 4 moduli specializzati in un singolo container ottimizzato per l'architettura Vitruvyan OS Blueprint 2026.

### 🏗️ Architettura Unificata

```
📦 Container Gemma Cognitive Layer (Port 8009)
├── 🧮 EmbeddingEngine      - Generazione embeddings multilingue
├── 🎭 SentimentFusion      - Analisi sentiment multi-modello  
├── 👤 ProfileProcessor     - Profilazione utenti e personalizzazione
├── 🌉 CognitiveBridge      - Orchestrazione e routing intelligente
└── 🔧 SharedInfrastructure - Cache, modelli, monitoraggio
```

## 🚀 Deployment Rapido

### Prerequisiti
- Docker & Docker Compose
- Almeno 2GB RAM disponibili
- File `.env` configurato

### Deployment Automatico
```bash
# Deploy completo con un comando
./scripts/deploy_gemma_cognitive.sh full

# Oppure step-by-step
./scripts/deploy_gemma_cognitive.sh deploy
```

### Deployment Manuale
```bash
# Build e start
docker-compose -f docker-compose.gemma-cognitive.yml up -d --build

# Test
python3 scripts/test_gemma_cognitive_unified.py
```

## 📋 API Endpoints

### 🧮 Embedding Engine
```http
POST /embedding/create          # Singolo embedding
POST /embedding/batch           # Batch embeddings
POST /embedding/similarity      # Similarità tra testi
GET  /health/embedding          # Health check modulo
```

### 🎭 Sentiment Fusion
```http
POST /sentiment/analyze         # Analisi sentiment singola
POST /sentiment/batch           # Batch sentiment analysis
POST /sentiment/calibrate       # Calibrazione modelli
GET  /health/sentiment          # Health check modulo
```

### 👤 Profile Processor
```http
POST /profile/create            # Creazione profilo utente
POST /profile/adapt             # Adattamento contenuto
POST /profile/recommend         # Raccomandazioni
GET  /health/profile            # Health check modulo
```

### 🌉 Cognitive Bridge
```http
POST /bridge/event              # Gestione eventi
POST /bridge/route              # Routing intelligente
GET  /bridge/services/health    # Status servizi esterni
GET  /bridge/analytics          # Analytics routing
GET  /health/bridge             # Health check modulo
```

### 🔧 Admin & Monitoring
```http
GET  /health                    # Health check generale
GET  /admin/metrics             # Metriche sistema
GET  /admin/cache/stats         # Statistiche cache
GET  /admin/models/status       # Status modelli
GET  /admin/integrity/report    # Report integrità
```

## 🧪 Testing

### Test Automatici
```bash
# Test completo di tutti i moduli
python3 scripts/test_gemma_cognitive_unified.py

# Test specifico endpoint
curl http://localhost:8009/health
```

### Test Manuali
```bash
# Test embedding
curl -X POST http://localhost:8009/embedding/create \
  -H "Content-Type: application/json" \
  -d '{"text": "Apple entity analysis", "language": "en"}'

# Test sentiment
curl -X POST http://localhost:8009/sentiment/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Excellent quarterly results", "fusion_mode": "enhanced"}'
```

## 🔧 Configurazione

### Variabili d'Ambiente
```bash
# Database
DATABASE_URL=postgresql://user:pass@postgres:5432/vitruvyan
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Cache
REDIS_URL=redis://redis:6379/0

# Vector DB  
QDRANT_URL=http://qdrant:6333

# Modelli
HUGGINGFACE_HUB_CACHE=/app/models
TRANSFORMERS_CACHE=/app/models

# Performance
CUDA_VISIBLE_DEVICES=0  # Se GPU disponibile
OMP_NUM_THREADS=4
```

### Limiti Risorse
```yaml
deploy:
  resources:
    limits:
      memory: 2G
    reservations:
      memory: 1G
```

## 📊 Monitoring

### Health Checks
```bash
# Container health
docker healthcheck vitruvyan-gemma-cognitive

# Endpoint health  
curl http://localhost:8009/health
```

### Metriche
```bash
# Resource usage
docker stats vitruvyan-gemma-cognitive

# Application metrics
curl http://localhost:8009/admin/metrics
```

### Logs
```bash
# Real-time logs
docker logs -f vitruvyan-gemma-cognitive

# Logs con compose
docker-compose -f docker-compose.gemma-cognitive.yml logs -f
```

## 🔄 Integrazione Vitruvyan

### Backward Compatibility
- Mantiene compatibilità con `api_sentiment:8005` (enhanced endpoints)
- Integra con `api_semantic:8003`, `api_neural:8004`, `api_crewai:8002`
- Connessione diretta a PostgreSQL, Redis, Qdrant

### Service Discovery
```bash
# Il container è disponibile nella rete Vitruvyan come:
gemma-cognitive:8009
```

### Database Integration
```python
# Automaticamente integrato con:
- log_agent (PostgreSQL)        # Logging agenti
- phrases (PostgreSQL)          # Dati semantici  
- embeddings (Qdrant)          # Vettori embedding
- cache (Redis)                # Cache distribuita
```

## 🎯 Use Cases

### 1. Analisi Multilingue
```python
# Embedding multilingue
embedding_request = {
    "text": "Analisi tecnica del mercato azionario",
    "language": "it", 
    "model_type": "financial"
}
```

### 2. Sentiment Fusion Avanzato
```python
# Multi-model sentiment con calibrazione
sentiment_request = {
    "text": "Quarterly earnings exceeded expectations",
    "fusion_mode": "deep",
    "use_cache": True
}
```

### 3. Personalizzazione Utente
```python
# Profilazione e adattamento contenuto
profile_request = {
    "user_id": "trader_001",
    "interaction_data": [...],
    "preferences": {...}
}
```

### 4. Routing Intelligente
```python
# Instradamento automatico richieste
routing_request = {
    "content": "I need market sentiment analysis",
    "strategy": "intelligent",
    "user_context": {"user_id": "trader_001"}
}
```

## 🔍 Troubleshooting

### Problemi Comuni

#### Container non si avvia
```bash
# Check logs
docker logs vitruvyan-gemma-cognitive

# Check ports
netstat -tlnp | grep 8009

# Check dependencies
docker-compose -f docker-compose.gemma-cognitive.yml ps
```

#### Performance Issues
```bash
# Check resource usage
docker stats vitruvyan-gemma-cognitive

# Check model loading
curl http://localhost:8009/admin/models/status

# Check cache performance
curl http://localhost:8009/admin/cache/stats
```

#### Connectivity Issues
```bash
# Test network
docker network inspect vitruvyan-network

# Test service connectivity
docker exec vitruvyan-gemma-cognitive curl http://postgres:5432
```

### Recovery Actions
```bash
# Restart service
docker-compose -f docker-compose.gemma-cognitive.yml restart

# Rebuild from scratch
docker-compose -f docker-compose.gemma-cognitive.yml up -d --build --force-recreate

# Clean restart
./scripts/deploy_gemma_cognitive.sh cleanup
./scripts/deploy_gemma_cognitive.sh deploy
```

## 📈 Performance Benchmarks

### Targets di Performance
- **Embedding Generation**: < 200ms per testo
- **Sentiment Analysis**: < 150ms per testo  
- **Profile Processing**: < 300ms per profilo
- **Cache Hit Rate**: > 60%
- **Memory Usage**: < 2GB
- **Container Size**: < 800MB

### Ottimizzazioni
- **Lazy Loading**: Modelli caricati on-demand
- **Model Sharing**: Condivisione modelli tra moduli
- **Redis Caching**: Cache distribuita multi-layer
- **Batch Processing**: Supporto elaborazione batch
- **Resource Limits**: Limiti memoria configurabili

## 🔮 Roadmap

### Fase 2 (Attuale)
- ✅ Container unificato con 4 moduli
- ✅ Shared infrastructure ottimizzata
- ✅ Backward compatibility mantenuta
- ✅ Testing e monitoring completi

### Fase 3 (Prossima)
- 🔄 Integrazione completa LangGraph
- 🔄 Ottimizzazioni performance GPU
- 🔄 Multi-tenancy support
- 🔄 Advanced analytics

### Fase 4-5 (Future)
- 🔮 Auto-scaling basato su carico
- 🔮 ML model versioning
- 🔮 Advanced user profiling
- 🔮 Real-time adaptation

---

**🎯 Il Gemma Cognitive Layer Unificato rappresenta l'evoluzione dell'architettura Vitruvyan verso un sistema cognitivo completo, mantenendo semplicità operativa e performance ottimali.**