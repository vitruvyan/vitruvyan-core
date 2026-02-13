# Keycloak — Knowledge Base (KB) SSO Setup

This repo supports a **login-based** Knowledge Base using:

- Keycloak (OIDC provider)
- Nginx (reverse proxy)
- oauth2-proxy (OIDC login + session cookie)

## High-level flow

1. User opens `https://kb.vitruvyan.com/docs/…`
2. Nginx calls `oauth2-proxy` via `auth_request`
3. If not authenticated, oauth2-proxy redirects to Keycloak login (`/auth/…`)
4. After login, user is redirected back to KB and a session cookie is set

## Bootstrap (realm/client/groups)

Use `bootstrap-kb.sh` to create:

- realm: `vitruvyan`
- groups:
  - `/kb-developers` (internal docs)
  - `/kb-admins` (advanced docs)
- client: `kb` (confidential OIDC client)
  - redirect URIs:
    - `https://kb.vitruvyan.com/oauth2/callback`
    - `https://kb.vitruvyan.com/oauth2-advanced/callback`

The script is idempotent and can be re-run safely.

## Notes

- Keycloak is served under the KB domain at `/auth/` to avoid a second TLS hostname.
- Secrets are **not** committed; oauth2-proxy reads them from a local env file.
- `bootstrap-kb.sh` expects `KEYCLOAK_ADMIN_PASSWORD` and `KB_OIDC_CLIENT_SECRET` (from `keycloak.env`).
