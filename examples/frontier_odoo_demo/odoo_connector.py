"""
Odoo Frontier Connector — Vitruvyan Oculus Prime plugin.

Implements AbstractAPIFetcher pattern for Odoo XML-RPC API.
Three concrete fetchers: invoices, sale orders, partners.
"""

from __future__ import annotations

import hashlib
import logging
import xmlrpc.client
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OdooConfig:
    """Odoo connection parameters."""
    url: str = "http://localhost:8069"
    db: str = "vitruvyan_demo"
    user: str = "admin"
    password: str = "admin"


class OdooConnector:
    """
    Unified Odoo XML-RPC connector for the Frontier demo.
    Wraps authentication + model queries with caching.
    """

    def __init__(self, config: OdooConfig | None = None):
        self.config = config or OdooConfig()
        self._uid: int | None = None
        self._models: xmlrpc.client.ServerProxy | None = None

    # -- connection ----------------------------------------------------------

    def _get_uid(self) -> int:
        if self._uid is None:
            common = xmlrpc.client.ServerProxy(
                f"{self.config.url}/xmlrpc/2/common"
            )
            uid = common.authenticate(
                self.config.db, self.config.user, self.config.password, {}
            )
            if not uid:
                raise ConnectionError("Odoo authentication failed")
            self._uid = uid
        return self._uid

    def _get_models(self) -> xmlrpc.client.ServerProxy:
        if self._models is None:
            self._models = xmlrpc.client.ServerProxy(
                f"{self.config.url}/xmlrpc/2/object"
            )
        return self._models

    def _call(
        self,
        model: str,
        method: str,
        domain: list | None = None,
        fields: list[str] | None = None,
        limit: int = 200,
        order: str | None = None,
    ) -> list[dict]:
        uid = self._get_uid()
        models = self._get_models()
        kwargs: dict[str, Any] = {}
        if fields:
            kwargs["fields"] = fields
        if limit:
            kwargs["limit"] = limit
        if order:
            kwargs["order"] = order
        return models.execute_kw(
            self.config.db, uid, self.config.password,
            model, method, [domain or []], kwargs,
        )

    # -- health --------------------------------------------------------------

    def ping(self) -> dict:
        common = xmlrpc.client.ServerProxy(
            f"{self.config.url}/xmlrpc/2/common"
        )
        version = common.version()
        return {
            "status": "connected",
            "server_version": version.get("server_version", "unknown"),
            "database": self.config.db,
        }

    # -- data endpoints ------------------------------------------------------

    def overview(self) -> dict:
        """Dashboard summary counts."""
        uid = self._get_uid()
        models = self._get_models()
        db, pwd = self.config.db, self.config.password
        counts = {}
        for model, label in [
            ("res.partner", "partners"),
            ("product.template", "products"),
            ("sale.order", "sale_orders"),
            ("purchase.order", "purchase_orders"),
            ("account.move", "invoices"),
            ("crm.lead", "crm_leads"),
            ("hr.employee", "employees"),
            ("project.task", "tasks"),
        ]:
            try:
                counts[label] = models.execute_kw(
                    db, uid, pwd, model, "search_count", [[]]
                )
            except Exception:
                counts[label] = 0
        return counts

    def partners(
        self,
        partner_type: str = "customer",
        limit: int = 50,
    ) -> list[dict]:
        if partner_type == "supplier":
            domain = [("supplier_rank", ">", 0)]
        else:
            domain = [("customer_rank", ">", 0)]
        return self._call(
            "res.partner", "search_read", domain,
            fields=["name", "city", "email", "phone", "vat",
                    "customer_rank", "supplier_rank", "is_company",
                    "country_id", "create_date"],
            limit=limit,
            order="name asc",
        )

    def invoices(self, limit: int = 50) -> list[dict]:
        return self._call(
            "account.move", "search_read",
            [("move_type", "in", ["out_invoice", "in_invoice"])],
            fields=["name", "partner_id", "move_type", "amount_total",
                    "amount_residual", "invoice_date", "invoice_date_due",
                    "payment_state", "state"],
            limit=limit,
            order="invoice_date desc",
        )

    def sale_orders(self, limit: int = 50) -> list[dict]:
        return self._call(
            "sale.order", "search_read", [],
            fields=["name", "partner_id", "date_order", "amount_total",
                    "state", "invoice_status"],
            limit=limit,
            order="date_order desc",
        )

    def purchase_orders(self, limit: int = 50) -> list[dict]:
        return self._call(
            "purchase.order", "search_read", [],
            fields=["name", "partner_id", "date_order", "amount_total",
                    "state"],
            limit=limit,
            order="date_order desc",
        )

    def crm_leads(self, limit: int = 50) -> list[dict]:
        return self._call(
            "crm.lead", "search_read", [],
            fields=["name", "partner_id", "expected_revenue", "probability",
                    "stage_id", "type", "create_date", "user_id"],
            limit=limit,
            order="expected_revenue desc",
        )

    def employees(self, limit: int = 50) -> list[dict]:
        return self._call(
            "hr.employee", "search_read", [],
            fields=["name", "job_title", "department_id", "work_email",
                    "work_phone"],
            limit=limit,
            order="name asc",
        )

    def products(self, limit: int = 50) -> list[dict]:
        return self._call(
            "product.template", "search_read", [],
            fields=["name", "type", "list_price", "standard_price",
                    "categ_id", "qty_available"],
            limit=limit,
            order="name asc",
        )

    # -- analysis helpers ----------------------------------------------------

    def invoice_analysis(self) -> dict:
        """Aggregate invoice metrics for cognitive analysis."""
        invoices = self.invoices(limit=500)
        out = [i for i in invoices if i.get("move_type") == "out_invoice"]
        inp = [i for i in invoices if i.get("move_type") == "in_invoice"]

        def _stats(records: list[dict]) -> dict:
            if not records:
                return {"count": 0, "total": 0, "avg": 0, "unpaid": 0, "unpaid_amount": 0}
            total = sum(r["amount_total"] for r in records)
            unpaid = [r for r in records if r.get("payment_state") != "paid"]
            return {
                "count": len(records),
                "total": round(total, 2),
                "avg": round(total / len(records), 2),
                "unpaid": len(unpaid),
                "unpaid_amount": round(sum(r["amount_residual"] for r in unpaid), 2),
            }

        return {
            "receivable": _stats(out),
            "payable": _stats(inp),
            "net_position": round(
                sum(r["amount_total"] for r in out) - sum(r["amount_total"] for r in inp), 2
            ),
        }

    def crm_pipeline(self) -> dict:
        """CRM pipeline analysis."""
        leads = self.crm_leads(limit=500)
        total_pipeline = sum(l.get("expected_revenue", 0) or 0 for l in leads)
        by_stage: dict[str, dict] = {}
        for lead in leads:
            stage = lead.get("stage_id")
            stage_name = stage[1] if isinstance(stage, (list, tuple)) else "Unknown"
            if stage_name not in by_stage:
                by_stage[stage_name] = {"count": 0, "revenue": 0}
            by_stage[stage_name]["count"] += 1
            by_stage[stage_name]["revenue"] += lead.get("expected_revenue", 0) or 0

        return {
            "total_opportunities": len(leads),
            "total_pipeline_value": round(total_pipeline, 2),
            "avg_deal_size": round(total_pipeline / len(leads), 2) if leads else 0,
            "by_stage": by_stage,
        }

    def customer_segmentation(self) -> dict:
        """Basic customer segmentation by city."""
        customers = self.partners("customer", limit=500)
        by_city: dict[str, int] = {}
        for c in customers:
            city = c.get("city") or "N/D"
            by_city[city] = by_city.get(city, 0) + 1
        return {
            "total_customers": len(customers),
            "by_city": dict(sorted(by_city.items(), key=lambda x: -x[1])),
            "cities_count": len(by_city),
        }
