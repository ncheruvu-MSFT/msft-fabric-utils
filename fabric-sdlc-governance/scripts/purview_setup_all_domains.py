"""Populate every governance domain with data products, terms, CDEs, and one objective.

Skips items that already exist (matched by name within the domain).
"""
from __future__ import annotations
import os, sys, uuid, pathlib, subprocess, requests
from requests.adapters import HTTPAdapter
try:
    from urllib3.util.retry import Retry
except ImportError:
    from requests.packages.urllib3.util.retry import Retry  # type: ignore

ROOT = pathlib.Path(__file__).resolve().parents[1]
env = ROOT / ".env"
if env.exists():
    for ln in env.read_text().splitlines():
        if "=" in ln and not ln.startswith("#"):
            k, v = ln.split("=", 1)
            os.environ.setdefault(k, v)

TENANT   = os.environ["TENANT_ID"]
SUB      = os.environ.get("AZ_SUBSCRIPTION_ID", "31613fe0-1e9b-4a97-b771-dc48fbaa0fbb")
APPROVER = os.environ.get("GOV_APPROVER_OID", "e5fde933-199e-4b54-917a-8e6741be6941")
BASE     = f"https://{TENANT}-api.purview-service.microsoft.com"
V        = "2026-03-20-preview"

S = requests.Session()
S.mount("https://", HTTPAdapter(max_retries=Retry(
    total=6, backoff_factor=1.5, status_forcelist=(429,500,502,503,504),
    allowed_methods=frozenset(["GET","POST","PUT","DELETE"]))))

_TOKEN = subprocess.check_output(
    f"az account get-access-token --subscription {SUB} --resource https://purview.azure.net --query accessToken -o tsv",
    shell=True, text=True).strip()

def H():
    return {"Authorization": f"Bearer {_TOKEN}", "Content-Type": "application/json"}

# domain-name (substring match) -> theme bundle
THEMES = {
    "finance": {
        "products": [
            ("Finance KPIs (Demo)", "Analytical", "Daily roll-up of revenue, margin and OPEX by business unit."),
            ("GL Trial Balance (Demo)", "Reference", "Cleansed trial-balance snapshots used by month-end close."),
        ],
        "terms": [
            ("Revenue",     "Recognized income from goods and services delivered in the period."),
            ("Gross Margin","Revenue minus cost of goods sold, expressed as a percentage."),
            ("OPEX",        "Operating expenses incurred to run the business, excluding COGS."),
        ],
        "cdes": [
            ("GL Account Code", "Text",   "Chart-of-accounts identifier."),
            ("Posting Period",  "Text",   "Fiscal period of the journal posting (YYYY-MM)."),
            ("Local Amount",    "Number", "Transaction amount in the entity's local currency."),
        ],
        "objective": ("Cut month-end close cycle to 3 business days",
                      "Reduce financial close from 6 to 3 business days by automating reconciliations.",
                      "Days from period-end to certified close = 3. Measured monthly."),
    },
    "hr": {
        "products": [
            ("Workforce Headcount (Demo)", "Operational", "Daily headcount, attrition and span-of-control metrics."),
            ("Compensation Bands (Demo)", "Reference", "Approved compensation bands by job family and region."),
        ],
        "terms": [
            ("Employee",  "An individual on the Contoso payroll, including full-time and part-time."),
            ("Attrition", "Voluntary or involuntary termination of an employment relationship."),
            ("Tenure",    "Length of continuous service measured in months."),
        ],
        "cdes": [
            ("Employee ID",   "Text",   "Globally unique identifier for an employee record."),
            ("Hire Date",     "DateTime","Effective date the employee joined Contoso."),
            ("Base Salary",   "Number", "Annualized base salary in employee's local currency."),
        ],
        "objective": ("Improve regretted attrition by 20% YoY",
                      "Reduce voluntary regretted attrition across all business units by 20% versus prior FY.",
                      "Trailing-12-month regretted-attrition rate <= 0.80 x prior-FY baseline, measured quarterly."),
    },
    "retail": {
        "products": [
            ("Store Sales (Demo)",       "Analytical", "Daily store-level POS sales with shrinkage adjustments."),
            ("Product Catalog (Demo)",   "Master",     "Authoritative master list of SKUs, categories and lifecycle status."),
        ],
        "terms": [
            ("Store",    "A physical or online Contoso retail location with its own ledger."),
            ("SKU",      "Stock-keeping unit; the lowest-level uniquely sellable item."),
            ("Shrinkage","Inventory loss due to theft, damage or administrative error."),
        ],
        "cdes": [
            ("Store ID",     "Text",   "Unique identifier for a retail location."),
            ("SKU",          "Text",   "Stock-keeping unit code."),
            ("Net Sales",    "Number", "Gross sales minus returns and discounts."),
        ],
        "objective": ("Lift same-store sales 5% in FY26",
                      "Grow same-store sales by 5% YoY through assortment and pricing optimization.",
                      "Comparable-store sales (52-week) >= 1.05 x prior period, measured monthly."),
    },
    "telemetry": {
        "products": [
            ("Service Health Signals (Demo)", "Operational", "Real-time platform telemetry: latency, error rate, saturation."),
            ("Customer Usage Events (Demo)",  "Analytical",  "Anonymized product-usage events powering adoption dashboards."),
        ],
        "terms": [
            ("SLO",        "Service-level objective: target reliability for a customer-facing surface."),
            ("Error Budget","Allowed unreliability over a rolling window before release freeze."),
            ("Saturation", "How full a resource is, expressed as percent of capacity."),
        ],
        "cdes": [
            ("Service ID",     "Text",   "Identifier of the production service emitting telemetry."),
            ("Event Timestamp","DateTime","UTC timestamp the telemetry event was emitted."),
            ("Latency P99",    "Number", "99th-percentile request latency in milliseconds."),
        ],
        "objective": ("Hold platform availability at 99.95%",
                      "Maintain >=99.95% monthly availability across customer-facing services.",
                      "Monthly availability = (1 - bad_minutes/total_minutes) >= 0.9995, computed per service."),
    },
}

# Map ANY substring in domain name -> theme key above. First match wins.
THEME_KEYS = [
    ("finance",          "finance"),
    ("revenue",          "finance"),
    ("treasury",         "finance"),
    ("hr",               "hr"),
    ("people operations","hr"),
    ("compensation",     "hr"),
    ("retail",           "retail"),
    ("online sales",     "retail"),
    ("store sales",      "retail"),
    ("sales",            "retail"),
    ("marketing",        "retail"),
    ("catalog",          "retail"),
    ("telemetry",        "telemetry"),
    ("device",           "telemetry"),
    ("web analytics",    "telemetry"),
]
SKIP_SUBSTRINGS = ("fabric demo - sales", ".stagingdomain")

def list_domains():
    r = S.get(f"{BASE}/datagovernance/catalog/businessdomains?api-version={V}", headers=H(), timeout=30)
    r.raise_for_status()
    return r.json().get("value", [])

def list_in_domain(path, domain_id):
    r = S.get(f"{BASE}/datagovernance/catalog/{path}?api-version={V}", headers=H(), timeout=30)
    if not r.ok: return []
    return [x for x in r.json().get("value", []) if x.get("domain") == domain_id]

def post(path, body):
    r = S.post(f"{BASE}/datagovernance/catalog/{path}?api-version={V}",
               headers=H(), json=body, timeout=60)
    return r

def seed_products(domain_id, items, status):
    have = {p["name"] for p in list_in_domain("dataproducts", domain_id)}
    for name, ptype, desc in items:
        if name in have: print(f"    = product exists: {name}"); continue
        pid = str(uuid.uuid4())
        body = {
            "id": pid, "name": name, "description": desc,
            "type": ptype, "status": status,
            "domain": domain_id, "updateFrequency": "Daily",
            "termsOfUse": [{"name": "Internal use only", "url": "https://contoso.example/terms"}],
            "documentation": [{"name": "Spec", "url": "https://contoso.example/docs"}],
            "contacts": {
                "owner":   [{"id": APPROVER, "description": "Domain owner"}],
                "expert":  [{"id": APPROVER, "description": "Domain expert"}],
                "steward": [{"id": APPROVER, "description": "Domain steward"}],
            },
        }
        r = post("dataproducts", body)
        tag = "+" if r.ok else "!"
        print(f"    {tag} product {name}: {r.status_code} {r.text[:160] if not r.ok else ''}")

def seed_terms(domain_id, items, status):
    have = {t["name"] for t in list_in_domain("terms", domain_id)}
    for name, desc in items:
        if name in have: print(f"    = term exists: {name}"); continue
        tid = str(uuid.uuid4())
        body = {"id": tid, "name": name, "description": desc,
                "domain": domain_id, "status": status,
                "contacts": {"steward": [{"id": APPROVER, "description": ""}]}}
        r = post("terms", body)
        tag = "+" if r.ok else "!"
        print(f"    {tag} term {name}: {r.status_code} {r.text[:160] if not r.ok else ''}")

def seed_cdes(domain_id, items, status):
    have = {c["name"] for c in list_in_domain("criticalDataElements", domain_id)}
    for name, dtype, desc in items:
        if name in have: print(f"    = CDE exists: {name}"); continue
        cid = str(uuid.uuid4())
        body = {"id": cid, "name": name, "description": desc,
                "dataType": dtype, "domain": domain_id, "status": status,
                "contacts": {"owner": [{"id": APPROVER, "description": "Domain owner"}]}}
        r = post("criticalDataElements", body)
        tag = "+" if r.ok else "!"
        print(f"    {tag} CDE {name}: {r.status_code} {r.text[:160] if not r.ok else ''}")

def seed_objective(domain_id, obj, status):
    if not obj: return
    name, desc, definition = obj
    have = {o.get("name") or o.get("definition") for o in list_in_domain("objectives", domain_id)}
    if name in have or definition in have:
        print(f"    = objective exists: {name}"); return
    oid = str(uuid.uuid4())
    body = {"id": oid, "name": name, "description": desc, "definition": definition,
            "domain": domain_id, "status": status,
            "targetDate": "2026-12-31",
            "contacts": {"owner": [{"id": APPROVER, "description": ""}]}}
    r = post("objectives", body)
    tag = "+" if r.ok else "!"
    print(f"    {tag} objective {name}: {r.status_code} {r.text[:160] if not r.ok else ''}")

def main():
    domains = list_domains()
    print(f"{len(domains)} domains found.\n")
    for d in domains:
        dn = d["name"].lower()
        if any(s in dn for s in SKIP_SUBSTRINGS):
            print(f"- {d['name']} ({d['id']})  [skipped]"); continue
        theme_key = next((tk for kw, tk in THEME_KEYS if kw in dn), None)
        if theme_key is None:
            print(f"- {d['name']} ({d['id']})  [no theme mapped, skipping]")
            continue
        theme = THEMES[theme_key]
        # Draft domain cannot host Published children; match parent status.
        child_status = "Published" if d.get("status") == "Published" else "Draft"
        print(f"- {d['name']} ({d['id']})  status={d.get('status')} -> children {child_status}")
        seed_products(d["id"], theme["products"], child_status)
        seed_terms(d["id"],    theme["terms"],    child_status)
        seed_cdes(d["id"],     theme["cdes"],     child_status)
        seed_objective(d["id"],theme["objective"],child_status)
    print("\nDone. Refresh https://purview.microsoft.com -> Enterprise glossary -> Governance Domains.")

if __name__ == "__main__":
    main()
