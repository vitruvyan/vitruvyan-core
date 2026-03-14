#!/usr/bin/env python3
"""
Seed script for Vitruvyan Frontier Odoo demo.

Creates database 'vitruvyan_demo', installs business modules,
and populates realistic Italian business data for connector demos.

Usage:
    python seed_demo_data.py [--url http://localhost:8069]
"""

import argparse
import sys
import time
import xmlrpc.client


MODULES = [
    "sale_management", "purchase", "account", "stock",
    "crm", "hr", "project", "contacts", "l10n_it",
]

SUPPLIERS = [
    {"name": "Acciaio Brescia S.r.l.", "city": "Brescia", "vat": "IT01234560170", "phone": "+39 030 1234567"},
    {"name": "Tessuti Prato S.p.A.", "city": "Prato", "vat": "IT02345670480", "phone": "+39 0574 234567"},
    {"name": "Elettronica Torino S.r.l.", "city": "Torino", "vat": "IT03456780011", "phone": "+39 011 3456789"},
    {"name": "Meccanica Bergamo S.r.l.", "city": "Bergamo", "vat": "IT04567890163", "phone": "+39 035 4567890"},
    {"name": "Chimica Ravenna S.p.A.", "city": "Ravenna", "vat": "IT05678900398", "phone": "+39 0544 567890"},
    {"name": "Logistica Verona S.r.l.", "city": "Verona", "vat": "IT06789010239", "phone": "+39 045 6789012"},
    {"name": "Alimentari Parma S.r.l.", "city": "Parma", "vat": "IT07890120344", "phone": "+39 0521 789012"},
    {"name": "Ceramiche Sassuolo S.p.A.", "city": "Sassuolo", "vat": "IT08901230366", "phone": "+39 0536 890123"},
]

CUSTOMERS = [
    {"name": "Studio Legale Bianchi & Associati", "city": "Milano"},
    {"name": "Ristorante Da Giovanni", "city": "Roma"},
    {"name": "Farmacia San Marco", "city": "Venezia"},
    {"name": "Hotel Belvedere", "city": "Firenze"},
    {"name": "Panificio Artusi", "city": "Bologna"},
    {"name": "Clinica Veterinaria Animalia", "city": "Napoli"},
    {"name": "Autofficina Rossi", "city": "Torino"},
    {"name": "Libreria Dante", "city": "Padova"},
    {"name": "Ottica Galileo", "city": "Pisa"},
    {"name": "Pasticceria Dolci Sogni", "city": "Palermo"},
    {"name": "Ferramenta Vulcano", "city": "Catania"},
    {"name": "Cantina Montepulciano", "city": "Siena"},
]

PRODUCTS = [
    {"name": "Consulenza IT Avanzata", "type": "service", "list_price": 150.0},
    {"name": "Licenza Software Enterprise", "type": "service", "list_price": 2500.0},
    {"name": "Server Rack 42U", "type": "consu", "list_price": 3200.0},
    {"name": "Sensore IoT Industriale", "type": "consu", "list_price": 450.0},
    {"name": "Pannello Solare 400W", "type": "consu", "list_price": 280.0},
    {"name": "Audit Sicurezza Informatica", "type": "service", "list_price": 5000.0},
    {"name": "Cablaggio Strutturato Cat.6A", "type": "consu", "list_price": 85.0},
    {"name": "Firewall Next-Gen", "type": "consu", "list_price": 1800.0},
    {"name": "Hosting Cloud Managed", "type": "service", "list_price": 199.0},
    {"name": "Formazione Cybersecurity", "type": "service", "list_price": 800.0},
    {"name": "Switch PoE 24 Porte", "type": "consu", "list_price": 650.0},
    {"name": "UPS 3000VA Online", "type": "consu", "list_price": 1200.0},
]

CRM_LEADS = [
    {"name": "Migrazione ERP — Gruppo Tessile Nord", "expected_revenue": 45000},
    {"name": "Progetto IoT — Stabilimento Automotive", "expected_revenue": 32000},
    {"name": "Infrastruttura Cloud — Catena Alberghiera", "expected_revenue": 28000},
    {"name": "Audit Sicurezza — Banca Locale", "expected_revenue": 15000},
    {"name": "Digital Transformation — Comune di Brescia", "expected_revenue": 55000},
    {"name": "E-commerce B2B — Distributore Alimentare", "expected_revenue": 22000},
    {"name": "Smart Factory — Ceramiche Emilia", "expected_revenue": 38000},
    {"name": "Disaster Recovery — Ospedale Regionale", "expected_revenue": 18000},
    {"name": "CRM Integration — Gruppo Assicurativo", "expected_revenue": 12000},
    {"name": "Data Analytics — Azienda Vinicola Toscana", "expected_revenue": 9500},
]

EMPLOYEES = [
    {"name": "Marco Ferretti", "job_title": "Chief Technology Officer"},
    {"name": "Laura Conti", "job_title": "Sales Manager"},
    {"name": "Alessandro Moretti", "job_title": "Senior Developer"},
    {"name": "Giulia Romano", "job_title": "Project Manager"},
    {"name": "Davide Colombo", "job_title": "DevOps Engineer"},
    {"name": "Sara Benedetti", "job_title": "UX Designer"},
    {"name": "Elena Marchetti", "job_title": "HR Manager"},
    {"name": "Luca Fontana", "job_title": "System Administrator"},
]


def wait_for_odoo(url: str, retries: int = 30) -> None:
    """Wait until Odoo XML-RPC is reachable."""
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    for i in range(retries):
        try:
            common.version()
            return
        except Exception:
            print(f"  Waiting for Odoo... ({i + 1}/{retries})")
            time.sleep(2)
    print("ERROR: Odoo not reachable", file=sys.stderr)
    sys.exit(1)


def create_database(url: str, db: str) -> None:
    """Create database with demo data if it does not exist."""
    db_rpc = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/db")
    existing = db_rpc.list()
    if db in existing:
        print(f"  Database '{db}' already exists — skipping creation")
        return
    print(f"  Creating database '{db}' (with demo data)...")
    db_rpc.create_database("admin", db, True, "en_US", "admin", "admin")
    print("  Done")


def authenticate(url: str, db: str) -> int:
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    uid = common.authenticate(db, "admin", "admin", {})
    if not uid:
        print("ERROR: Authentication failed", file=sys.stderr)
        sys.exit(1)
    return uid


def install_modules(url: str, db: str, uid: int) -> None:
    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
    for mod in MODULES:
        ids = models.execute_kw(db, uid, "admin", "ir.module.module", "search",
                                [[("name", "=", mod)]])
        if not ids:
            print(f"  Module '{mod}' not found — skipping")
            continue
        state = models.execute_kw(db, uid, "admin", "ir.module.module", "read",
                                  [ids, ["state"]])[0]["state"]
        if state == "installed":
            print(f"  {mod} — already installed")
            continue
        print(f"  Installing {mod}...")
        models.execute_kw(db, uid, "admin", "ir.module.module",
                          "button_immediate_install", [ids])
        print(f"  {mod} — installed")


def seed_partners(models, db: str, uid: int) -> None:
    for s in SUPPLIERS:
        exists = models.execute_kw(db, uid, "admin", "res.partner", "search_count",
                                   [[("name", "=", s["name"])]])
        if exists:
            continue
        models.execute_kw(db, uid, "admin", "res.partner", "create", [{
            "name": s["name"], "city": s["city"], "country_id": 112,  # Italy
            "supplier_rank": 1, "is_company": True,
            "vat": s.get("vat", False), "phone": s.get("phone", False),
        }])
        print(f"  + {s['name']}")

    for c in CUSTOMERS:
        exists = models.execute_kw(db, uid, "admin", "res.partner", "search_count",
                                   [[("name", "=", c["name"])]])
        if exists:
            continue
        models.execute_kw(db, uid, "admin", "res.partner", "create", [{
            "name": c["name"], "city": c["city"], "country_id": 112,
            "customer_rank": 1, "is_company": True,
        }])
        print(f"  + {c['name']}")


def seed_products(models, db: str, uid: int) -> None:
    for p in PRODUCTS:
        exists = models.execute_kw(db, uid, "admin", "product.template", "search_count",
                                   [[("name", "=", p["name"])]])
        if exists:
            continue
        models.execute_kw(db, uid, "admin", "product.template", "create", [{
            "name": p["name"], "type": p["type"], "list_price": p["list_price"],
        }])
        print(f"  + {p['name']}")


def seed_crm(models, db: str, uid: int) -> None:
    for lead in CRM_LEADS:
        exists = models.execute_kw(db, uid, "admin", "crm.lead", "search_count",
                                   [[("name", "=", lead["name"])]])
        if exists:
            continue
        models.execute_kw(db, uid, "admin", "crm.lead", "create", [{
            "name": lead["name"], "expected_revenue": lead["expected_revenue"],
            "type": "opportunity",
        }])
        print(f"  + {lead['name']}")


def seed_employees(models, db: str, uid: int) -> None:
    for emp in EMPLOYEES:
        exists = models.execute_kw(db, uid, "admin", "hr.employee", "search_count",
                                   [[("name", "=", emp["name"])]])
        if exists:
            continue
        models.execute_kw(db, uid, "admin", "hr.employee", "create", [{
            "name": emp["name"], "job_title": emp["job_title"],
        }])
        print(f"  + {emp['name']}")


def audit(models, db: str, uid: int) -> None:
    print("\n--- Final Audit ---")
    for model, label in [
        ("res.partner", "Partners"), ("product.template", "Products"),
        ("sale.order", "Sale Orders"), ("purchase.order", "Purchase Orders"),
        ("account.move", "Invoices"), ("crm.lead", "CRM Leads"),
        ("hr.employee", "Employees"), ("project.task", "Tasks"),
    ]:
        try:
            c = models.execute_kw(db, uid, "admin", model, "search_count", [[]])
            print(f"  {label}: {c}")
        except Exception:
            pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed Odoo demo for Vitruvyan Frontier")
    parser.add_argument("--url", default="http://localhost:8069")
    parser.add_argument("--db", default="vitruvyan_demo")
    args = parser.parse_args()

    print("=== Vitruvyan Frontier — Odoo Demo Seeder ===\n")

    print("[1/6] Connecting to Odoo...")
    wait_for_odoo(args.url)

    print("[2/6] Ensuring database exists...")
    create_database(args.url, args.db)

    print("[3/6] Authenticating...")
    uid = authenticate(args.url, args.db)

    print("[4/6] Installing business modules...")
    install_modules(args.url, args.db, uid)

    models = xmlrpc.client.ServerProxy(f"{args.url}/xmlrpc/2/object")

    print("[5/6] Seeding Italian business data...")
    print("  — Suppliers")
    seed_partners(models, args.db, uid)
    print("  — Products")
    seed_products(models, args.db, uid)
    print("  — CRM Opportunities")
    seed_crm(models, args.db, uid)
    print("  — Employees")
    seed_employees(models, args.db, uid)

    print("[6/6] Audit...")
    audit(models, args.db, uid)

    print("\n✅ Odoo demo ready!")
    print(f"   URL: {args.url}")
    print(f"   Database: {args.db}")
    print(f"   Login: admin / admin")


if __name__ == "__main__":
    main()
