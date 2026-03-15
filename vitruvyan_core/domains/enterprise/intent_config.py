"""
Enterprise Domain — Intent Configuration
==========================================

Registers enterprise/ERP-specific intents and screening filters
into the IntentRegistry for intent_detection_node.

This is the ONLY place where enterprise vocabulary lives.
The core intent_detection_node is domain-agnostic.

Vertical: Enterprise (Odoo/ERP connectors)
Contract: VERTICAL_CONTRACT_V1

Usage:
    from domains.enterprise.intent_config import create_enterprise_registry

    registry = create_enterprise_registry()
    prompt = registry.build_classification_prompt(user_input)

    # Or via environment selection:
    # INTENT_DOMAIN=enterprise

Coverage:
    - Clienti e fornitori (partner, contatti, anagrafiche)
    - Fatturazione (invoice analysis, revenue, AR/AP)
    - CRM (pipeline, lead, opportunità)
    - Ordini (vendita, acquisto, procurement)
    - Prodotti e catalogo
    - Risorse umane (dipendenti, organizzazione)
    - Analisi e reporting (KPI, dashboard, trend)
    - Documenti e knowledge base

Created: March 2026
"""

from core.orchestration.intent_registry import (
    IntentDefinition,
    IntentRegistry,
    ScreeningFilter,
)


def register_enterprise_intents(registry: IntentRegistry) -> IntentRegistry:
    """
    Register all enterprise-domain intents and screening filters.

    Args:
        registry: IntentRegistry to populate

    Returns:
        The same registry (for chaining)
    """
    # ------------------------------------------------------------------
    # INTENTS
    # ------------------------------------------------------------------
    intents = [
        # ── Analisi clienti / partner ────────────────────────────────
        IntentDefinition(
            name="partner_query",
            description="Ricerca e analisi clienti, fornitori, contatti (anagrafiche ERP)",
            examples=[
                "Mostrami i clienti principali",
                "Chi sono i nostri fornitori?",
                "Cerca il contatto di Acme Corp",
                "Top customers by revenue",
                "Quanti clienti abbiamo in Italia?",
                "Partner con fatturato maggiore",
                "Show me all suppliers",
            ],
            synonyms=[
                "cliente", "customer", "fornitore", "supplier",
                "contatto", "contact", "partner", "anagrafica",
                "azienda", "company", "vendor",
            ],
            requires_entities=False,
            route_type="exec",
        ),
        # ── Analisi fatture ──────────────────────────────────────────
        IntentDefinition(
            name="invoice_analysis",
            description="Analisi fatture: ricavi, margini, scadenze, AR/AP",
            examples=[
                "Analizza le fatture del mese",
                "Fatturato totale Q1",
                "Invoice analysis",
                "Quante fatture non pagate?",
                "Revenue breakdown per cliente",
                "Mostrami le fatture scadute",
                "Aging report crediti",
            ],
            synonyms=[
                "fattura", "invoice", "fatturato", "revenue",
                "ricavi", "crediti", "debiti", "scadenza",
                "pagamento", "payment", "AR", "AP",
                "accounts receivable", "accounts payable",
            ],
            requires_entities=False,
            route_type="exec",
        ),
        # ── CRM / Pipeline ──────────────────────────────────────────
        IntentDefinition(
            name="crm_pipeline",
            description="Gestione pipeline commerciale: lead, opportunità, conversioni",
            examples=[
                "Stato della pipeline commerciale",
                "Quanti lead abbiamo questo mese?",
                "CRM pipeline overview",
                "Opportunità in fase di negoziazione",
                "Tasso di conversione lead",
                "Mostrami le opportunità aperte",
                "Sales funnel analysis",
            ],
            synonyms=[
                "pipeline", "lead", "opportunità", "opportunity",
                "CRM", "commerciale", "sales", "vendita",
                "prospect", "deal", "trattativa", "funnel",
                "conversione", "conversion",
            ],
            requires_entities=False,
            route_type="exec",
        ),
        # ── Ordini di vendita ────────────────────────────────────────
        IntentDefinition(
            name="sales_orders",
            description="Analisi ordini di vendita: volumi, trend, stato",
            examples=[
                "Ordini di vendita del trimestre",
                "Quanti ordini confermati?",
                "Sales orders analysis",
                "Trend ordini ultimi 6 mesi",
                "Ordini per prodotto",
                "Valore medio ordini",
            ],
            synonyms=[
                "ordine di vendita", "sale order", "sales order",
                "ordine confermato", "confirmed order", "SO",
                "vendite", "sales",
            ],
            requires_entities=False,
            route_type="exec",
        ),
        # ── Ordini di acquisto ───────────────────────────────────────
        IntentDefinition(
            name="purchase_orders",
            description="Analisi ordini di acquisto e procurement",
            examples=[
                "Ordini di acquisto aperti",
                "Purchase order analysis",
                "Costo acquisti per fornitore",
                "Procurement status",
                "Quanti PO in attesa?",
            ],
            synonyms=[
                "ordine di acquisto", "purchase order", "PO",
                "procurement", "acquisto", "approvvigionamento",
                "buying", "purchasing",
            ],
            requires_entities=False,
            route_type="exec",
        ),
        # ── Prodotti e catalogo ──────────────────────────────────────
        IntentDefinition(
            name="product_catalog",
            description="Interrogazione catalogo prodotti: prezzi, stock, categorie",
            examples=[
                "Mostrami il catalogo prodotti",
                "Prezzo del prodotto X",
                "Prodotti in stock",
                "Product catalog overview",
                "Categorie prodotto",
                "Quanti prodotti abbiamo?",
            ],
            synonyms=[
                "prodotto", "product", "catalogo", "catalog",
                "articolo", "item", "SKU", "prezzo", "price",
                "stock", "inventario", "inventory", "magazzino",
            ],
            requires_entities=False,
            route_type="exec",
        ),
        # ── Risorse umane / Dipendenti ───────────────────────────────
        IntentDefinition(
            name="employee_query",
            description="Informazioni su dipendenti, organizzazione, HR",
            examples=[
                "Quanti dipendenti abbiamo?",
                "Lista dipendenti per dipartimento",
                "Employee overview",
                "Chi lavora nel reparto vendite?",
                "Organigramma aziendale",
            ],
            synonyms=[
                "dipendente", "employee", "personale", "staff",
                "HR", "risorse umane", "human resources",
                "dipartimento", "department", "organizzazione",
                "organico", "headcount",
            ],
            requires_entities=False,
            route_type="exec",
        ),
        # ── Analisi complessiva / KPI ────────────────────────────────
        IntentDefinition(
            name="business_analysis",
            description="Analisi aziendale complessiva: KPI, dashboard, overview",
            examples=[
                "Overview aziendale",
                "Business analysis completa",
                "KPI principali",
                "Dashboard direzionale",
                "Come sta andando l'azienda?",
                "Analisi completa del business",
                "Company performance overview",
            ],
            synonyms=[
                "analisi", "analysis", "overview", "dashboard",
                "KPI", "performance", "andamento", "trend",
                "report", "riassunto", "summary", "stato",
            ],
            requires_entities=False,
            route_type="exec",
        ),
        # ── Confronto / Comparazione ─────────────────────────────────
        IntentDefinition(
            name="comparison",
            description="Confronto tra entità: clienti, prodotti, periodi, fornitori",
            examples=[
                "Confronta i ricavi Q1 vs Q2",
                "Compare top 5 customers",
                "Differenza fatturato anno su anno",
                "Confronto fornitori per costo",
                "Quale cliente ha il margine migliore?",
            ],
            synonyms=[
                "confronta", "compare", "vs", "versus",
                "differenza", "difference", "meglio", "peggio",
                "migliore", "best", "worst",
            ],
            requires_entities=False,
            route_type="exec",
        ),
        # ── Ricerca documentale / KB ─────────────────────────────────
        IntentDefinition(
            name="document_search",
            description="Ricerca nella knowledge base aziendale e documenti",
            examples=[
                "Cerca nelle procedure aziendali",
                "Trova il documento sulla policy vendite",
                "Knowledge base su onboarding",
                "Documentazione interna su processi",
            ],
            synonyms=[
                "documento", "document", "procedura", "procedure",
                "policy", "knowledge base", "KB", "manuale",
                "guida", "guide", "cerca", "find", "search",
            ],
            requires_entities=False,
            route_type="exec",
        ),
        # ── Soft / conversazionale ───────────────────────────────────
        IntentDefinition(
            name="business_advice",
            description="Domande strategiche e consulenza aziendale generica",
            examples=[
                "Come posso migliorare il tasso di conversione?",
                "Suggerimenti per ridurre i costi",
                "Best practices per gestione fornitori",
                "Strategie di crescita",
            ],
            synonyms=[
                "consiglio", "advice", "suggerimento", "suggestion",
                "strategia", "strategy", "best practice",
                "migliorare", "improve", "ottimizzare", "optimize",
            ],
            requires_entities=False,
            route_type="soft",
        ),
    ]
    for intent in intents:
        registry.register_intent(intent)

    # ------------------------------------------------------------------
    # SCREENING FILTERS
    # ------------------------------------------------------------------
    filters = [
        ScreeningFilter(
            name="time_period",
            description="Periodo temporale di riferimento",
            value_type="enum",
            enum_values=["today", "week", "month", "quarter", "year", "custom"],
            keywords=[
                "oggi", "today", "settimana", "week", "mese", "month",
                "trimestre", "quarter", "Q1", "Q2", "Q3", "Q4",
                "anno", "year", "YTD", "ultimo", "last", "questo",
            ],
        ),
        ScreeningFilter(
            name="entity_type",
            description="Tipo di entità ERP",
            value_type="enum",
            enum_values=[
                "customer", "supplier", "product", "employee",
                "invoice", "order", "lead",
            ],
            keywords=[
                "cliente", "customer", "fornitore", "supplier",
                "prodotto", "product", "dipendente", "employee",
                "fattura", "invoice", "ordine", "order",
                "lead", "opportunità", "opportunity",
            ],
        ),
        ScreeningFilter(
            name="department",
            description="Dipartimento aziendale",
            value_type="enum",
            enum_values=[
                "sales", "purchasing", "accounting", "hr",
                "production", "logistics", "management",
            ],
            keywords=[
                "vendite", "sales", "acquisti", "purchasing",
                "contabilità", "accounting", "HR", "risorse umane",
                "produzione", "production", "logistica", "logistics",
                "direzione", "management",
            ],
        ),
        ScreeningFilter(
            name="status_filter",
            description="Filtro per stato documento/ordine",
            value_type="enum",
            enum_values=["draft", "confirmed", "done", "cancelled", "overdue"],
            keywords=[
                "bozza", "draft", "confermato", "confirmed",
                "completato", "done", "annullato", "cancelled",
                "scaduto", "overdue", "in ritardo", "late",
            ],
        ),
    ]
    for f in filters:
        registry.register_filter(f)

    return registry


# ------------------------------------------------------------------
# CONTEXT KEYWORDS — per intent (professional boundary enforcement)
# ------------------------------------------------------------------

CONTEXT_KEYWORDS: dict[str, list[str]] = {
    "partner_query": [
        "cliente", "customer", "fornitore", "supplier", "partner",
        "contatto", "contact", "anagrafica", "azienda", "company",
        "vendor", "top", "principali", "main",
    ],
    "invoice_analysis": [
        "fattura", "invoice", "fatturato", "revenue", "ricavi",
        "pagamento", "payment", "scadenza", "aging", "crediti",
        "debiti", "AR", "AP", "margine", "margin",
    ],
    "crm_pipeline": [
        "pipeline", "lead", "opportunità", "opportunity", "CRM",
        "sales", "conversione", "conversion", "funnel", "deal",
        "trattativa", "prospect", "commerciale",
    ],
    "sales_orders": [
        "ordine", "order", "vendita", "sale", "SO", "confermato",
        "confirmed", "volume", "trend",
    ],
    "purchase_orders": [
        "acquisto", "purchase", "PO", "procurement", "fornitore",
        "supplier", "costo", "cost",
    ],
    "product_catalog": [
        "prodotto", "product", "catalogo", "catalog", "prezzo",
        "price", "stock", "inventario", "inventory", "SKU",
        "articolo", "item", "magazzino",
    ],
    "employee_query": [
        "dipendente", "employee", "personale", "staff", "HR",
        "dipartimento", "department", "organico", "headcount",
    ],
    "business_analysis": [
        "analisi", "analysis", "KPI", "dashboard", "overview",
        "performance", "trend", "andamento", "report",
    ],
    "comparison": [
        "confronta", "compare", "vs", "versus", "differenza",
        "migliore", "peggiore", "best", "worst",
    ],
    "document_search": [
        "documento", "document", "cerca", "search", "trova", "find",
        "procedura", "policy", "knowledge base", "KB",
    ],
    "business_advice": [
        "consiglio", "advice", "strategia", "strategy",
        "migliorare", "improve", "ottimizzare", "optimize",
    ],
    # Always allowed (no keyword gate)
    "unknown": [],
}

# Patterns that indicate out-of-scope requests for an enterprise assistant
AMBIGUOUS_PATTERNS: list[str] = [
    r'\b(compra azioni|buy stocks|investi in borsa|trade)\b',
    r'\b(bitcoin|crypto|forex|trading)\b',
    r'\b(diagnosi medica|medical diagnosis|prescrizione|prescription)\b',
]


def create_enterprise_registry() -> IntentRegistry:
    """
    Factory: create a fully configured IntentRegistry for enterprise domain.

    Called by graph_flow.py when INTENT_DOMAIN=enterprise.

    Returns:
        IntentRegistry with all enterprise intents + filters registered.
    """
    registry = IntentRegistry(domain_name="enterprise")
    register_enterprise_intents(registry)
    return registry
