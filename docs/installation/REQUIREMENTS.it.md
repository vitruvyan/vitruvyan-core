# Requisiti

Questa pagina definisce i **requisiti minimi** per far girare Vitruvyan OS via Docker (KB + servizi core).

## Baseline hardware

Questi numeri assumono un deploy **single-node** con lo stack core (Redis, Postgres, Qdrant, Nginx, MkDocs e le API principali).

| Profilo | CPU | RAM | Disco | Note |
|---|---:|---:|---:|---|
| **Minimo (dev / piccolo uso interno)** | 8 vCPU | 16 GB | 250 GB SSD | Ok per demo e carichi leggeri. Headroom RAM ridotto. |
| **Consigliato (istituzionale / team)** | 16 vCPU | 32 GB | 500 GB NVMe | Più margine per Qdrant + Postgres + log + rebuild. |
| **Intenso (multi-tenant / ingestion alta)** | 32 vCPU | 64 GB | 1 TB NVMe | Quando embeddings + ingestion + retention crescono in modo continuo. |

Note:
- Preferire **NVMe** rispetto a HDD (latenza importante per Qdrant e Postgres).
- Il sizing disco dipende da **retention** (eventi, audit, snapshot) e crescita dei vettori.

## Sistema operativo supportato

- **Ubuntu 24.04 LTS** (baseline consigliata)

Altre distro Linux possono funzionare, ma le note di hardening e i percorsi di riferimento assumono Ubuntu.

## Servizi infrastrutturali richiesti

Vitruvyan si appoggia a questi componenti (in container o managed equivalent):

- **PostgreSQL** (Archivarium) — storage strutturato, audit, metadata
- **Qdrant** (Mnemosyne) — storage vettoriale per retrieval semantico
- **Redis** — Streams transport (Cognitive Bus) e coordinamento
- **Nginx** — reverse proxy, TLS termination, access control (Basic Auth oggi; Keycloak più avanti)

## Runtime richiesto

- **Docker Engine** + **Docker Compose**
- Possibilità di pull/build immagini (accesso a registry privati se applicabile)

Opzionale ma utile sull'host:
- `curl`, `git`, `make`, `jq`
- `python3` (per script locali e verifiche rapide)

## Requisiti di rete

### Inbound (utenti)

- `80/tcp` (HTTP) e `443/tcp` (HTTPS) verso Nginx

### Interno (container-to-container)

I servizi comunicano nella network Docker; evitare di esporre le porte interne pubblicamente salvo necessità.

### Outbound (dal server)

A seconda della configurazione, può servire accesso outbound per:
- install di pacchetti e pull immagini
- emissione/rinnovo certificati TLS (se Let's Encrypt)
- provider LLM opzionali (se non tutto self-hosted)

## DNS / TLS

- Hostname stabile per la KB (es. `kb.vitruvyan.com`)
- Certificato TLS valido (terminazione su Nginx)

## Hardening produzione (consigliato)

- Backup per PostgreSQL e Qdrant (snapshot + storage off-box)
- Rotazione log e monitoraggio disco
- Regole firewall: esporre pubblicamente solo `80/443`
- Separazione nodi (opzionale): DB/vector/bus separati dalle API quando cresce il carico
