# Enterprise Domain
> **Last updated**: Mar 2026

## Overview

The Enterprise domain is a vertical for Vitruvyan Core that provides enterprise/ERP-specific
intent detection, prompt engineering, governance rules, and Sacred Orders domain specialization
for business data analysis.

It connects to ERP systems (Odoo, SAP, Oracle) via Vitruvyan Frontier connectors and enables
natural language interaction with business data: clients, invoicing, CRM pipeline, orders,
products, employees, and KPIs.

## Contract Conformance

- **Contract**: `VERTICAL_CONTRACT_V1.1`
- **Status**: Active
- **Domain name**: `enterprise`
- **Sacred Orders**: All 5 applicable packs implemented (§13)

## Architecture

```
vitruvyan_core/domains/enterprise/
├── __init__.py              # Domain registration
├── intent_config.py         # 11 intents + 4 filters + context keywords
├── compose_formatter.py     # Domain context for compose_node
├── governance_rules.py      # Compliance rules (finance claims, legal, GDPR)
├── graph_plugin.py          # LEGACY — superseded by graph_nodes/
├── vertical_manifest.yaml   # Contract manifest (V1.1)
├── README.md                # This file
├── graph_nodes/
│   ├── __init__.py
│   └── registry.py          # Canonical graph_nodes hook (Phase 2A)
├── prompts/
│   └── __init__.py          # Enterprise identity + scenarios (IT/EN/ES)
├── pattern_weavers/         # Sacred Order: Ontology (§13.1)
│   ├── __init__.py
│   ├── taxonomy_enterprise.yaml  # 11 ERP categories + multilingual aliases
│   ├── weave_config.py           # Thresholds, boosts per category
│   ├── enterprise_context.py     # 5-language context detector
│   └── tests/
├── babel_gardens/           # Sacred Order: Signals (§13.2)
│   ├── __init__.py
│   ├── signals_enterprise.yaml   # business_health, operational_urgency, compliance_risk
│   ├── sentiment_config.py       # LLM-first fusion (llm=0.65, multilingual=0.35)
│   ├── enterprise_context.py     # Re-exports from pattern_weavers
│   └── tests/
├── orthodoxy_wardens/       # Sacred Order: Compliance (§13.3)
│   ├── __init__.py
│   ├── compliance_config.py      # GDPR, legal, finance, data_integrity
│   └── tests/
├── memory_orders/           # Sacred Order: Coherence (§13.4)
│   ├── __init__.py
│   ├── enterprise_config.py      # Partners/invoices collections, drift thresholds
│   └── tests/
├── vault_keepers/           # Sacred Order: Archival (§13.5)
│   ├── __init__.py
│   ├── enterprise_config.py      # 10-year fiscal retention, tiered policies
│   └── tests/
│       └── test_enterprise_config.py
└── tests/
    └── test_vertical_contract.py  # Contract conformance tests
```

## Intents (11)

| Intent | Route | Description |
|--------|-------|-------------|
| `partner_query` | exec | Customer/supplier analysis |
| `invoice_analysis` | exec | Invoice, revenue, AR/AP analysis |
| `crm_pipeline` | exec | CRM pipeline, leads, conversion |
| `sales_orders` | exec | Sales order analysis |
| `purchase_orders` | exec | Purchase order / procurement |
| `product_catalog` | exec | Product catalog queries |
| `employee_query` | exec | HR / employee information |
| `business_analysis` | exec | Overall KPIs, dashboard |
| `comparison` | exec | Compare entities/periods |
| `document_search` | exec | Knowledge base search |
| `business_advice` | soft | Strategic advice (LLM) |

## Filters (4)

| Filter | Type | Values |
|--------|------|--------|
| `time_period` | enum | today, week, month, quarter, year, custom |
| `entity_type` | enum | customer, supplier, product, employee, invoice, order, lead |
| `department` | enum | sales, purchasing, accounting, hr, production, logistics, management |
| `status_filter` | enum | draft, confirmed, done, cancelled, overdue |

## Quick Start

```python
from domains.enterprise.intent_config import create_enterprise_registry

registry = create_enterprise_registry()
prompt = registry.build_classification_prompt("Mostrami i clienti principali")
```

## Environment Variables

```bash
INTENT_DOMAIN=enterprise     # Activate enterprise intent detection
ENTITY_DOMAIN=enterprise     # (optional) Enterprise entity resolver
GRAPH_DOMAIN=enterprise      # (optional) Enterprise graph extension
```

## Governance Rules

- **enterprise.finance.001-002**: No guaranteed financial projections
- **enterprise.legal.001-002**: Redirect legal/tax to professionals
- **enterprise.gdpr.001-002**: Protect PII (salary, tax ID, IBAN)

## Sacred Orders Domain Packs (Contract §13)

All 5 applicable Sacred Orders are specialized for the enterprise domain.

| Sacred Order | Pack | Key Configuration |
|---|---|---|
| **Pattern Weavers** | `pattern_weavers/` | 11 ERP categories (CRM, Sales, Invoicing, Accounting, Purchasing, Inventory, HR, Products, Projects, Operations, Compliance) with IT/ES aliases |
| **Babel Gardens** | `babel_gardens/` | 3 signals: `business_health` [-1,1], `operational_urgency` [0,1], `compliance_risk` [0,1]. LLM-first fusion (0.65 LLM, 0.35 multilingual) |
| **Orthodoxy Wardens** | `orthodoxy_wardens/` | strict_mode=True, confidence_floor=0.70, 4 categories (GDPR, legal, finance, data_integrity) |
| **Memory Orders** | `memory_orders/` | primary_table=partners, drift thresholds (healthy=5%, warning=15%), 5 source candidates |
| **Vault Keepers** | `vault_keepers/` | 10-year fiscal retention (Art. 2220 C.C.), tiered policies (invoices=10y, compliance=10y, partners=5y, logs=1y) |
| **Codex Hunters** | N/A | Source-agnostic by design (MAY) |

### Activation

```bash
PATTERN_DOMAIN=enterprise    # Pattern Weavers taxonomy
BABEL_DOMAIN=enterprise      # Babel Gardens signals
# Memory Orders, Vault Keepers, Orthodoxy Wardens: auto-loaded from domain pack
```
