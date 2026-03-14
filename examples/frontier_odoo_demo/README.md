# Vitruvyan Frontier — Odoo Demo Environment

> **Last updated**: Mar 14, 2026 17:00 UTC

Full-stack demo: Odoo 17 ERP + FastAPI backend + React UI showing Vitruvyan Frontier's enterprise cognitive connector in action.

## Quick Start

```bash
# 1. Ensure vitruvyan_core_net exists
docker network create vitruvyan_core_net 2>/dev/null || true

# 2. Start Odoo + Postgres
docker compose up -d

# 3. Wait ~30s for Odoo to boot, then seed data
python3 seed_demo_data.py

# 4. Start the backend API (port 8888)
pip3 install fastapi uvicorn
python3 -m uvicorn app:app --port 8888 &

# 5. Start the frontend (port 5180)
cd frontend && npm install && npm run dev
```

Open **http://localhost:5180** — the demo is live.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌───────────────┐
│  React UI   │────▶│  FastAPI API  │────▶│  Odoo 17 ERP  │
│  :5180      │     │  :8888        │     │  :8069        │
│  Vite+TW    │     │  /api/*       │     │  XML-RPC      │
└─────────────┘     └──────────────┘     └───────────────┘
```

## Access

| Service | URL |
|---------|-----|
| **Demo UI** | http://localhost:5180 |
| **Backend API** | http://localhost:8888/docs |
| **Odoo ERP** | http://localhost:8069 (admin/admin, db: `vitruvyan_demo`) |

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/health` | Connection status |
| `GET /api/overview` | Dashboard counts |
| `GET /api/partners?type=customer\|supplier` | Partners list |
| `GET /api/invoices` | Invoices |
| `GET /api/orders/sale` | Sale orders |
| `GET /api/orders/purchase` | Purchase orders |
| `GET /api/crm` | CRM pipeline |
| `GET /api/employees` | Employees |
| `GET /api/products` | Products |
| `GET /api/analysis/invoices` | Invoice analytics |
| `GET /api/analysis/crm` | CRM pipeline analytics |
| `GET /api/analysis/customers` | Customer segmentation |
| `GET /api/analysis/full` | Complete BI snapshot |

## What Gets Seeded

The seed script installs 9 business modules and creates:

- **8 Italian suppliers** (Acciaio Brescia, Tessuti Prato, Elettronica Torino, etc.)
- **12 Italian customers** (Studio Legale, Ristorante, Farmacia, Hotel, etc.)
- **12 products/services** (IT consulting, software licenses, IoT sensors, etc.)
- **10 CRM opportunities** (~€275K pipeline value)
- **8 employees** (CTO, Sales Manager, DevOps, etc.)

Plus Odoo's built-in demo data: ~60 contacts, 35 products, 24 sale orders, 48 invoices, 39 CRM leads, etc.

**Final totals**: 101 partners, 51 products, 24 SO, 48 invoices, 59 CRM leads (€1.27M pipeline), 30 employees

## Cleanup

```bash
docker compose down -v   # removes containers AND data volumes
```
