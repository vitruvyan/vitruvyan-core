# domains/enterprise/pattern_weavers/enterprise_context.py
"""
Enterprise Context Detector — Pattern Weavers Domain Pack

Detects whether a user query belongs to the enterprise/ERP domain.
Supports EN, IT, ES, FR, DE — same pattern as FinancialContextDetector.
"""

from typing import Dict, Any, Set
import logging

logger = logging.getLogger(__name__)

# Multilingual enterprise terminology (40+ terms per language)
_ENTERPRISE_TERMS: Dict[str, Set[str]] = {
    "en": {
        "customer", "client", "partner", "supplier", "vendor",
        "invoice", "credit note", "payment", "receivable", "payable",
        "sales order", "purchase order", "order", "quotation",
        "pipeline", "lead", "opportunity", "CRM", "conversion",
        "product", "catalog", "inventory", "stock", "warehouse",
        "employee", "department", "payroll", "leave", "HR",
        "budget", "P&L", "balance sheet", "journal", "ledger",
        "project", "task", "timesheet", "milestone", "KPI",
        "procurement", "RFQ", "tender", "delivery", "shipping",
        "ERP", "Odoo", "SAP", "margin", "revenue", "headcount",
    },
    "it": {
        "cliente", "fornitore", "partner", "fattura", "pagamento",
        "crediti", "debiti", "ordine di vendita", "ordine di acquisto",
        "pipeline", "lead", "opportunità", "CRM", "conversione",
        "prodotto", "catalogo", "magazzino", "giacenza", "inventario",
        "dipendente", "reparto", "busta paga", "ferie", "organico",
        "bilancio", "conto economico", "budget", "centro di costo",
        "progetto", "attività", "scadenza", "KPI", "fatturato",
        "approvvigionamento", "preventivo", "consegna", "spedizione",
        "ERP", "Odoo", "margine", "ricavo", "nota di credito",
    },
    "es": {
        "cliente", "proveedor", "factura", "pago", "cobrar", "pagar",
        "pedido de venta", "orden de compra", "cotización",
        "pipeline", "oportunidad", "embudo", "CRM", "conversión",
        "producto", "catálogo", "almacén", "inventario",
        "empleado", "departamento", "nómina", "vacaciones",
        "balance", "presupuesto", "centro de coste", "KPI",
        "proyecto", "tarea", "plazo", "envío", "ERP",
    },
    "fr": {
        "client", "fournisseur", "facture", "paiement", "créance",
        "commande", "devis", "pipeline", "prospect", "CRM",
        "produit", "catalogue", "entrepôt", "stock", "inventaire",
        "employé", "département", "paie", "congé", "effectif",
        "bilan", "budget", "KPI", "projet", "tâche", "ERP",
    },
    "de": {
        "Kunde", "Lieferant", "Rechnung", "Zahlung", "Forderung",
        "Bestellung", "Angebot", "Pipeline", "CRM", "Vertrieb",
        "Produkt", "Katalog", "Lager", "Bestand", "Inventar",
        "Mitarbeiter", "Abteilung", "Gehalt", "Urlaub", "Personal",
        "Bilanz", "Budget", "KPI", "Projekt", "Aufgabe", "ERP",
    },
}


class EnterpriseContextDetector:
    """Detect enterprise/ERP domain queries via keyword matching."""

    def is_enterprise(
        self, text: str, language: str = "auto"
    ) -> Dict[str, Any]:
        """
        Check if text belongs to the enterprise domain.

        Args:
            text: User query text.
            language: ISO 639-1 code or "auto" for multi-language scan.

        Returns:
            {"is_enterprise": bool, "confidence": float, "matched_terms": list}
        """
        text_lower = text.lower()
        matched = []

        if language == "auto":
            languages = _ENTERPRISE_TERMS.keys()
        else:
            languages = [language] if language in _ENTERPRISE_TERMS else ["en"]

        for lang in languages:
            for term in _ENTERPRISE_TERMS.get(lang, set()):
                if term.lower() in text_lower:
                    matched.append(term)

        # Deduplicate (case-insensitive)
        seen = set()
        unique = []
        for m in matched:
            key = m.lower()
            if key not in seen:
                seen.add(key)
                unique.append(m)

        confidence = min(1.0, len(unique) * 0.25)
        return {
            "is_enterprise": len(unique) >= 1,
            "confidence": round(confidence, 2),
            "matched_terms": unique[:10],
        }
