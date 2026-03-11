# Installazione

> **Ultimo aggiornamento**: 11 Mar 2026 14:00 UTC

## Quick Start (One-Liner)

Su una **VPS Ubuntu** vergine (24.04 LTS consigliato):

```bash
curl -fsSL https://raw.githubusercontent.com/dbaldoni/vitruvyan-core/main/scripts/install.sh | bash
```

Questo comando:

1. Installa i prerequisiti di sistema (git, python3, curl)
2. Clona il repository in `/opt/vitruvyan-core`
3. Rende il comando `vit` disponibile a livello di sistema
4. Lancia il wizard di setup interattivo

Il wizard gestisce tutto il resto: installazione Docker, configurazione porte, variabili d'ambiente e avvio dell'infrastruttura.

!!! tip "Revisione prima dell'esecuzione"
    Se preferisci ispezionare lo script prima:
    ```bash
    curl -fsSL https://raw.githubusercontent.com/dbaldoni/vitruvyan-core/main/scripts/install.sh -o install.sh
    less install.sh
    bash install.sh
    ```

## Opzioni di Installazione

| Metodo | Ideale per | Guida |
|--------|-----------|-------|
| **One-liner** | VPS vergine, deploy rapido | Questa pagina |
| **Clone manuale** | Sviluppatori, setup custom | [Setup Locale](LOCAL.it.md) |
| **Solo Docker** | Host Docker esistente | [Setup Docker](DOCKER.it.md) |
| **Produzione** | Deploy istituzionale | [Produzione](PRODUCTION.it.md) |

## Opzioni dell'Installer

Lo script accetta variabili d'ambiente:

| Variabile | Default | Descrizione |
|-----------|---------|-------------|
| `INSTALL_DIR` | `/opt/vitruvyan-core` | Dove clonare il repository |
| `BRANCH` | `main` | Branch git da installare |
| `SKIP_SETUP` | `0` | `1` per saltare il wizard |
| `REPO_URL` | `github.com/dbaldoni/vitruvyan-core` | URL del repository Git |

## Cosa Viene Installato

```
┌─────────────────────────────────────────────┐
│  La tua VPS (Ubuntu)                        │
│                                             │
│  /opt/vitruvyan-core/        ← codice       │
│  /usr/local/bin/vit          ← CLI          │
│                                             │
│  Container Docker:                          │
│  ├── core_redis      (Bus Cognitivo)        │
│  ├── core_postgres   (Archivarium)          │
│  ├── core_qdrant     (Mnemosyne)            │
│  ├── core_graph      (LangGraph API)        │
│  ├── core_nginx      (Reverse Proxy)        │
│  └── ...servizi      (Ordini Sacri)         │
└─────────────────────────────────────────────┘
```

## Post-Installazione

```bash
vit status          # Panoramica del sistema
vit doctor          # Health check dettagliato
```

