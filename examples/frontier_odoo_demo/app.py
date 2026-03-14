"""
Vitruvyan Frontier — Odoo Demo Backend.

FastAPI service bridging Odoo data to a cognitive-analysis demo UI.
Serves the React frontend from static/ and exposes /api/* endpoints.

Usage:
    uvicorn app:app --port 8888 --reload
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from odoo_connector import OdooConfig, OdooConnector

logger = logging.getLogger("frontier_demo")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")

# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

connector: OdooConnector | None = None


@asynccontextmanager
async def lifespan(application: FastAPI):
    global connector
    cfg = OdooConfig(
        url=os.getenv("ODOO_URL", "http://localhost:8069"),
        db=os.getenv("ODOO_DB", "vitruvyan_demo"),
        user=os.getenv("ODOO_USER", "admin"),
        password=os.getenv("ODOO_PASSWORD", "admin"),
    )
    connector = OdooConnector(cfg)
    logger.info("Frontier demo started — Odoo %s/%s", cfg.url, cfg.db)
    yield
    connector = None


app = FastAPI(
    title="Vitruvyan Frontier — Odoo Demo",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _conn() -> OdooConnector:
    if connector is None:
        raise HTTPException(503, "Odoo connector not ready")
    return connector


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health():
    try:
        info = _conn().ping()
        return {"status": "ok", "odoo": info, "timestamp": datetime.utcnow().isoformat()}
    except Exception as exc:
        raise HTTPException(503, f"Odoo unreachable: {exc}")


@app.get("/api/overview")
def overview():
    return _conn().overview()


@app.get("/api/partners")
def partners(
    type: str = Query("customer", pattern="^(customer|supplier)$"),
    limit: int = Query(50, ge=1, le=500),
):
    return _conn().partners(partner_type=type, limit=limit)


@app.get("/api/invoices")
def invoices(limit: int = Query(50, ge=1, le=500)):
    return _conn().invoices(limit=limit)


@app.get("/api/orders/sale")
def sale_orders(limit: int = Query(50, ge=1, le=500)):
    return _conn().sale_orders(limit=limit)


@app.get("/api/orders/purchase")
def purchase_orders(limit: int = Query(50, ge=1, le=500)):
    return _conn().purchase_orders(limit=limit)


@app.get("/api/crm")
def crm_leads(limit: int = Query(50, ge=1, le=500)):
    return _conn().crm_leads(limit=limit)


@app.get("/api/employees")
def employees(limit: int = Query(50, ge=1, le=500)):
    return _conn().employees(limit=limit)


@app.get("/api/products")
def products(limit: int = Query(50, ge=1, le=500)):
    return _conn().products(limit=limit)


# -- Analysis endpoints ----------------------------------------------------

@app.get("/api/analysis/invoices")
def analyze_invoices():
    return _conn().invoice_analysis()


@app.get("/api/analysis/crm")
def analyze_crm():
    return _conn().crm_pipeline()


@app.get("/api/analysis/customers")
def analyze_customers():
    return _conn().customer_segmentation()


@app.get("/api/analysis/full")
def full_analysis():
    """Complete business intelligence snapshot."""
    c = _conn()
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "overview": c.overview(),
        "invoices": c.invoice_analysis(),
        "crm": c.crm_pipeline(),
        "customers": c.customer_segmentation(),
    }


# ---------------------------------------------------------------------------
# Static frontend (production mode)
# ---------------------------------------------------------------------------

STATIC_DIR = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.isdir(STATIC_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")

    @app.get("/{path:path}")
    def serve_spa(path: str):
        file_path = os.path.join(STATIC_DIR, path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
