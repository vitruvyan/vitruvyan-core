# Vault Keepers API

<p class="kb-subtitle">LIVELLO 2 service for integrity checks, backup/recovery planning, and immutable audit records.</p>

## Location

- Service: `services/api_vault_keepers/`
- Pure core: `vitruvyan_core/core/governance/vault_keepers/`

## Quick reference

- Canonical service doc: `services/api_vault_keepers/README.md`
- Swagger: `/docs`
- Health: `/health` (implemented by the service)

## Endpoint groups (as documented)

See `services/api_vault_keepers/README.md` for the current endpoint list:

- Integrity monitoring (`/integrity/*`)
- Backup operations (`/backup/*`)
- Recovery operations (`/recovery/*`)
- Audit trail (`/audit/*`)

## Finance vertical (conditional)

When `VAULT_DOMAIN=finance`, additional endpoints are exposed:

- `/v1/finance/config`
- `/v1/finance/integrity`
- `/v1/finance/backup`
- `/v1/finance/archive`
- `/v1/finance/signal-timeseries/archive`
