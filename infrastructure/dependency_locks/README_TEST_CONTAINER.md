# LangGraph 1.x Isolated Test Container

This directory contains the setup for running an **isolated test container** of the Graph Orchestrator with LangGraph upgraded to version 1.0.8, without affecting production.

## Purpose
- Safely test LangGraph 1.x compatibility and behavior
- Compare with production (0.5.4) in a controlled environment
- Enable immediate rollback if issues are found

## Files
- `Dockerfile.api_graph_test`: Dockerfile for the test container (LangGraph 1.0.8)
- `requirements_graph_0_5_4_freeze.txt`: Frozen dependencies from production (rollback anchor)

## Usage

### 1. Build the Test Container
```
docker compose -f infrastructure/docker/docker-compose.yml build vitruvyan_api_graph_test
```

### 2. Create the Docker Network (if missing)
```
docker network create vitruvyan_core_net
```

### 3. Start the Test Container
```
docker compose -f infrastructure/docker/docker-compose.yml up -d vitruvyan_api_graph_test
```

- The test container will run on port **9010** (internal 8010).
- It uses the same environment, network, and volumes as production, but is fully isolated.

### 4. Run Validation Tests
- Use the same API endpoints as production, but on port 9010.
- Compare logs, outputs, and dependency trees.

### 5. Rollback
- To rollback, simply stop and remove the test container:
```
docker compose -f infrastructure/docker/docker-compose.yml down vitruvyan_api_graph_test
```
- Production is **never** affected.

## Notes
- Do **not** modify production requirements or containers.
- All changes are local to the test container.
- See main repo README for validation suite instructions.
