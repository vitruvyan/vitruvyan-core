# api_edge_dse _legacy

Pre-refactoring aegis implementation (read-only frozen archive).

Origin: `/home/caravaggio/aegis/services/core/api_aegis_dse/`
Archived: Feb 26, 2026

Key changes in refactoring:
- Replaced `redis.asyncio` PubSub with `StreamBus` (Redis Streams, consumer groups, acknowledgment)
- Replaced raw `psycopg2` / `redis_client` with `PostgresAgent` + `StreamBus` vitruvyan-core agents
- Moved Pareto + sampling algorithms to LIVELLO 1 pure domain (`infrastructure/edge/dse/`)
- Contracts moved from `aegis_contracts` (Pydantic) to frozen dataclasses in `domain/schemas.py`
- main.py reduced from 259 → 76 lines
