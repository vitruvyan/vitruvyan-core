# Orthodoxy Wardens API

<p class="kb-subtitle">LIVELLO 2 epistemic tribunal: evaluate, classify, render verdicts, and publish audit trails.</p>

## Location

- Service: `services/api_orthodoxy_wardens/`
- Pure core: `vitruvyan_core/core/governance/orthodoxy_wardens/`

## Quick reference

- Canonical service doc: `services/api_orthodoxy_wardens/README.md`
- Swagger: `/docs`
- Health: `/health` (implemented by the service)

## Endpoint groups (as documented)

See `services/api_orthodoxy_wardens/README.md` for the current endpoint list:

- Judgment operations (`/judge/*`)
- Rules management (`/rules/*`)
- Evidence & audit (`/evidence/*`, `/audit/*`)
- Tribunal operations (`/tribunal/*`)

## Finance vertical (conditional)

When `ORTHODOXY_DOMAIN=finance`, additional endpoints are exposed:

- `/v1/finance/config`
- `/v1/finance/rules/stats`
- `/v1/finance/validate`
- `/v1/finance/audit`
