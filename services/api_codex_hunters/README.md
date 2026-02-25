# Codex Hunters API (`api_codex_hunters`)

Servizio FastAPI per coordinare “expeditions” dei Codex Hunters (Perception / data collection).

Documentazione canonica (vitruvyan-core): `docs/services/codex_hunters.md`

## Quick pointers

- Codice servizio: `services/api_codex_hunters/main.py`
- Streams listener: `services/api_codex_hunters/streams_listener.py`
- Source registry DB: `codex_source_registry` + `codex_source_topics`
- Endpoint introspezione sorgenti: `GET /sources`
