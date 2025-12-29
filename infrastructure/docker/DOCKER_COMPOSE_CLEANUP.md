# 🧹 Docker Compose Cleanup Analysis

**Date**: December 29, 2025  
**Issue**: Multiple docker-compose files causing confusion  
**Current Active**: `docker-compose.yml` (23 services, container prefix: `omni_`)

---

## 📋 Current Files Inventory

| File | Services | Purpose | Status |
|------|----------|---------|--------|
| **docker-compose.yml** | 23 | **ACTIVE** - Main stack (omni_* containers) | ✅ KEEP |
| docker-compose.omni.yml | 23 | Duplicate with minor network differences | ❌ REDUNDANT |
| docker-compose-postgres.yml | 5 | OpenMetadata/Collate license (external) | ❓ LEGACY |
| docker-compose.test.yml | 3 | Test containers (Synaptic Renaissance) | ⚠️ TESTING ONLY |
| docker-compose.craft.yml | 1 | Single craft API container | ⚠️ EXPERIMENTAL |

---

## 🔍 Detailed Analysis

### 1. docker-compose.yml (ACTIVE ✅)
- **Container Prefix**: `omni_*`
- **Network**: `vitruvyan_omni_net` (but defined as `omni-net` in file)
- **Services**: 23 including:
  - Infrastructure: postgres, redis, qdrant, keycloak
  - APIs: graph, neural, semantic, embedding, babel_gardens, etc.
  - Monitoring: prometheus, grafana, exporters
- **Volumes**: `redis_data_omni`, `postgres_data_omni`, `qdrant_data_omni`
- **Status**: Currently running 4 containers (postgres, redis, qdrant, neural)

### 2. docker-compose.omni.yml (REDUNDANT ❌)
- **Differences from main**:
  - Network name: `vitruvyan_omni_net` (vs `omni-net`)
  - Volume names: `redis_data` (vs `redis_data_omni`)
  - Some service configurations differ slightly
- **Issue**: Creates confusion - appears to be old version before consolidation
- **Recommendation**: **DELETE** - functionality covered by docker-compose.yml

### 3. docker-compose-postgres.yml (LEGACY ❓)
- **Purpose**: OpenMetadata/Apache Collate stack
- **Copyright**: Collate 2021 - external dependency
- **Services**: 5 (appears unrelated to vitruvyan-core)
- **Recommendation**: **MOVE TO ARCHIVE** - if not used for vitruvyan-core

### 4. docker-compose.test.yml (TESTING ⚠️)
- **Purpose**: "Synaptic Renaissance" test containers
- **Services**: 3 test-specific containers
- **Note**: "PostgreSQL locale (non containerizzato), porte diverse"
- **Recommendation**: **KEEP** but rename to `docker-compose.TEST.yml` (clear separation)

### 5. docker-compose.craft.yml (EXPERIMENTAL ⚠️)
- **Purpose**: Single experimental craft API
- **Services**: 1 (vitruvyan_api_craft)
- **Recommendation**: **KEEP** if actively used, otherwise **DELETE**

---

## ⚠️ Key Issue: Network Naming Inconsistency

**Problem**: docker-compose.yml defines network as `omni-net` but Docker creates `vitruvyan_omni_net`

```yaml
# In docker-compose.yml
networks:
  omni-net:  # Docker prefixes with project name: vitruvyan_omni_net
```

**Result**: 
- Containers use network: `vitruvyan_omni_net` (actual)
- File declares: `omni-net` (logical name)
- This is NORMAL Docker Compose behavior (project_networkname)

---

## 🎯 Recommended Actions

### Immediate Actions:

1. **DELETE docker-compose.omni.yml**
   ```bash
   mv docker-compose.omni.yml docker-compose.omni.yml.OBSOLETE
   ```
   - Redundant with docker-compose.yml
   - Creates confusion

2. **Clarify docker-compose.yml as PRIMARY**
   - Rename to keep clear: `docker-compose.yml` (already correct)
   - Add header comment: "Main Vitruvyan Core Stack"

3. **Archive docker-compose-postgres.yml**
   ```bash
   mkdir -p archive
   mv docker-compose-postgres.yml archive/docker-compose-openmetadata.yml
   ```
   - External OpenMetadata/Collate stack
   - Not vitruvyan-core related

4. **Rename test files for clarity**
   ```bash
   mv docker-compose.test.yml docker-compose.TEST.yml
   mv docker-compose.craft.yml docker-compose.CRAFT.yml
   ```
   - Uppercase = not main stack

### After Cleanup:

```
infrastructure/docker/
├── docker-compose.yml          # MAIN STACK (23 services)
├── docker-compose.TEST.yml     # Test containers only
├── docker-compose.CRAFT.yml    # Experimental craft API
└── archive/
    ├── docker-compose.omni.yml.OBSOLETE
    └── docker-compose-openmetadata.yml
```

---

## ✅ Cleanup Script

```bash
cd /home/caravaggio/projects/vitruvyan-core/infrastructure/docker

# Create archive directory
mkdir -p archive

# Move redundant omni file
mv docker-compose.omni.yml archive/docker-compose.omni.yml.OBSOLETE_DEC29

# Archive OpenMetadata stack
mv docker-compose-postgres.yml archive/docker-compose-openmetadata.yml

# Rename test files (optional - for clarity)
# mv docker-compose.test.yml docker-compose.TEST.yml
# mv docker-compose.craft.yml docker-compose.CRAFT.yml

echo "✅ Cleanup complete"
ls -lah *.yml
```

---

## 🚦 Verification After Cleanup

```bash
# Check active containers still running
docker ps

# Verify main compose file works
docker-compose config --quiet

# Ensure no breaking changes
docker-compose ps
```

---

## 📊 Expected Final State

**Active Docker Compose Files**:
- ✅ `docker-compose.yml` - Main vitruvyan-core stack (23 services)
- ⚠️ `docker-compose.test.yml` - Test containers (optional)
- ⚠️ `docker-compose.craft.yml` - Experimental (optional)

**Archived**:
- 🗄️ `archive/docker-compose.omni.yml.OBSOLETE_DEC29`
- 🗄️ `archive/docker-compose-openmetadata.yml`

**Running Containers** (unchanged):
- omni_postgres
- omni_redis
- omni_qdrant
- omni_api_neural
- (omni_api_graph when build completes)

---

**Approvazione richiesta prima di eseguire cleanup?**
