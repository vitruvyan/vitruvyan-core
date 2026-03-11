# Setup Locale (Installazione Manuale)

> **Ultimo aggiornamento**: 11 Mar 2026 14:00 UTC

Guida passo-passo per installare Vitruvyan OS manualmente, senza lo script one-liner.

## Prerequisiti

- **Ubuntu 24.04 LTS** (o distro Debian-compatibile)
- **Python 3.10+** (`python3 --version`)
- **git** e **curl**

```bash
# Installa prerequisiti se mancanti
sudo apt update && sudo apt install -y git curl python3
```

## Step 1: Clona il Repository

```bash
git clone https://github.com/dbaldoni/vitruvyan-core.git
cd vitruvyan-core
```

## Step 2: Rendi `vit` Disponibile

Il CLI `vit` funziona direttamente dal repo — nessun `pip install` necessario:

```bash
# Opzione A: symlink al PATH (consigliato)
sudo ln -s "$(pwd)/vit" /usr/local/bin/vit

# Opzione B: aggiungi il repo al PATH in ~/.bashrc
echo "export PATH=\"$(pwd):\$PATH\"" >> ~/.bashrc
source ~/.bashrc
```

Verifica:

```bash
vit --help
```

## Step 3: Lancia il Wizard di Setup

```bash
vit setup
```

Il wizard ti guida attraverso 5 step:

| Step | Cosa fa |
|------|---------|
| **1. Prerequisiti** | Verifica Python, git, Docker — propone di installare Docker se mancante |
| **2. Porte** | Configura le porte host (standard: 6379, 5432, 6333, 6334 — o personalizzate) |
| **3. Profilo** | Scegli un profilo di installazione (minimal, standard, finance, full, custom) |
| **4. Ambiente** | Raccoglie API key e password (OpenAI, PostgreSQL, ecc.) |
| **5. Installazione** | Installa i pacchetti selezionati e avvia i container dell'infrastruttura |

## Step 4: Verifica

```bash
# Controlla lo stato del sistema
vit status

# Verifica che i container Docker siano in esecuzione
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

## Modalità Non-Interattiva

Per deploy automatizzati (CI/CD, Ansible, ecc.):

```bash
# Installa con profilo minimal, senza prompt
vit setup --profile minimal --yes

# Solo controllo prerequisiti
vit setup --check

# Solo generazione file .env
vit setup --env-only
```

## Porte Personalizzate

Se le porte standard sono in conflitto, il wizard permette di scegliere alternative. Le porte sono configurate come variabili `HOST_*` in `infrastructure/docker/.env`:

| Variabile | Default | Descrizione |
|-----------|---------|-------------|
| `HOST_REDIS_PORT` | 6379 | Porta host Redis |
| `HOST_POSTGRES_PORT` | 5432 | Porta host PostgreSQL |
| `HOST_QDRANT_REST_PORT` | 6333 | Porta host Qdrant REST API |
| `HOST_QDRANT_GRPC_PORT` | 6334 | Porta host Qdrant gRPC |

Queste porte influenzano solo il **mapping lato host**. I servizi comunicano internamente via rete Docker usando le porte standard.

## Risoluzione Problemi

**Docker permission denied:**
```bash
sudo usermod -aG docker $USER
# Esci e rientra, poi riprova
```

**Porta già in uso:**
```bash
# Trova cosa sta usando una porta
sudo lsof -i :6379
# Scegli una porta diversa durante il setup
```

**Ri-eseguire il setup:**
```bash
vit setup  # Sicuro da ri-eseguire — preserva i valori .env esistenti
```
