"""Prepare a demo data product + governance domain so the two new-Unified-Catalog
workflows (Data product access + Catalog curation publish) can be attached to
them in the Purview portal.

Why a script instead of "create the workflows directly":
    The Unified Catalog public REST API (2026-03-20-preview) covers domains,
    data products, terms, CDEs, OKRs and access policies, but it does NOT yet
    expose endpoints for the new portal workflows you see at
    https://purview.microsoft.com/datacatalog/governance/main/catalog/workflows
    Those have to be created from the portal UI. This script provisions a
    demo data product in a demo domain so you have something to attach the
    two workflows to, then prints the exact click-path.

Idempotent: re-run safely; existing domain / data product are reused.
"""
from __future__ import annotations

import os
import sys
import time
import uuid
import pathlib
import requests
from requests.adapters import HTTPAdapter
try:
    from urllib3.util.retry import Retry
except ImportError:
    from requests.packages.urllib3.util.retry import Retry  # type: ignore

_SESSION = requests.Session()
_SESSION.mount("https://", HTTPAdapter(max_retries=Retry(
    total=6, connect=6, read=6, backoff_factor=1.5,
    status_forcelist=(429, 500, 502, 503, 504),
    allowed_methods=frozenset(["GET", "POST", "PUT", "DELETE"]),
    raise_on_status=False,
)))


def _req(method: str, url: str, *, json=None, tries: int = 4):
    last = None
    for i in range(tries):
        try:
            return _SESSION.request(method, url, headers=H(), json=json, timeout=60)
        except requests.exceptions.RequestException as e:
            last = e
            time.sleep(2 * (i + 1))
    raise last

ROOT = pathlib.Path(__file__).resolve().parents[1]
for env in (ROOT / ".env",):
    if env.exists():
        for ln in env.read_text().splitlines():
            if "=" in ln and not ln.startswith("#"):
                k, v = ln.split("=", 1)
                os.environ.setdefault(k, v)

TENANT = os.environ.get("TENANT_ID")
if not TENANT:
    sys.exit("TENANT_ID missing from .env")

UC_BASE = f"https://{TENANT}-api.purview-service.microsoft.com"
API     = "2026-03-20-preview"
PORTAL  = f"https://purview.microsoft.com/datacatalog/governance/main/catalog/workflows?tid={TENANT}"

DOMAIN_NAME      = "Fabric Demo - Sales"
DOMAIN_DESC      = "Demo governance domain used for Unified Catalog workflow walkthroughs."
PRODUCT_NAME     = "Sales Pipeline (Demo)"
PRODUCT_DESC     = (
    "Demo data product representing the curated Sales Pipeline gold tables in "
    "Fabric. Used to demonstrate the Data product access workflow and the "
    "Catalog curation publish workflow."
)
PRODUCT_USE_CASE = (
    "Sales analysts query this product to see week-over-week pipeline health, "
    "stage conversion, and rep-level forecast attainment."
)
PRODUCT_TYPE     = "Reference"   # valid enum: Reference|Master|Operational|Analytical|Dataset

EXTRA_PRODUCTS = [
    ("Customer 360 (Demo)",       "Master",      "Unified customer profile gold table"),
    ("Marketing Campaigns (Demo)", "Operational", "Campaign performance feed"),
    ("Finance KPIs (Demo)",        "Analytical",  "Daily finance KPI cube"),
]
OWNER_OID        = os.environ.get("GOV_APPROVER_OID", "e5fde933-199e-4b54-917a-8e6741be6941")


def _token() -> str:
    import subprocess
    return subprocess.check_output(
        "az account get-access-token --resource https://purview.azure.net "
        "--query accessToken -o tsv",
        text=True, shell=True,
    ).strip()


def H() -> dict:
    return {"Authorization": f"Bearer {_token()}", "Content-Type": "application/json"}


def ensure_domain() -> str:
    r = _req("GET", f"{UC_BASE}/datagovernance/catalog/businessdomains?api-version={API}")
    r.raise_for_status()
    for d in r.json().get("value", []):
        if d.get("name") == DOMAIN_NAME:
            print(f"  = domain exists: {DOMAIN_NAME} ({d['id']})")
            return d["id"]
    payload = {
        "id": str(uuid.uuid4()),
        "name": DOMAIN_NAME,
        "description": DOMAIN_DESC,
        "type": "FunctionalUnit",
        "status": "Published",
        "isRestricted": False,
    }
    r = _req("POST", f"{UC_BASE}/datagovernance/catalog/businessdomains?api-version={API}", json=payload)
    if r.status_code not in (200, 201):
        sys.exit(f"create domain failed: {r.status_code} {r.text[:400]}")
    did = r.json()["id"]
    print(f"  + domain created: {DOMAIN_NAME} ({did})")
    return did


def ensure_product(domain_id: str) -> str:
    r = _req("GET", f"{UC_BASE}/datagovernance/catalog/dataproducts?domainId={domain_id}&api-version={API}")
    if r.ok:
        for p in r.json().get("value", []):
            if p.get("name") == PRODUCT_NAME:
                print(f"  = data product exists: {PRODUCT_NAME} ({p['id']})")
                return p["id"]
    payload = {
        "id": str(uuid.uuid4()),
        "name": PRODUCT_NAME,
        "description": PRODUCT_DESC,
        "type": PRODUCT_TYPE,
        "status": "Published",
        "endorsed": False,
        "domain": domain_id,
        "businessUse": PRODUCT_USE_CASE,
        "updateFrequency": "Daily",
        "contacts": {
            "owner":   [{"id": OWNER_OID, "description": "Demo owner"}],
            "expert":  [{"id": OWNER_OID, "description": "Demo expert"}],
            "steward": [{"id": OWNER_OID, "description": "Demo steward"}],
        },
        "termsOfUse":    [{"description": "Demo terms",  "url": "https://contoso.example/terms"}],
        "documentation": [{"description": "Demo docs",   "url": "https://contoso.example/docs"}],
    }
    r = _req("POST", f"{UC_BASE}/datagovernance/catalog/dataproducts?api-version={API}", json=payload)
    if r.status_code not in (200, 201):
        sys.exit(f"create data product failed: {r.status_code} {r.text[:600]}")
    pid = r.json().get("id", payload["id"])
    print(f"  + data product created: {PRODUCT_NAME} ({pid})")
    return pid


def ensure_extras(domain_id: str) -> None:
    existing = set()
    r = _req("GET", f"{UC_BASE}/datagovernance/catalog/dataproducts?domainId={domain_id}&api-version={API}")
    if r.ok:
        existing = {p.get("name") for p in r.json().get("value", [])}
    for name, typ, desc in EXTRA_PRODUCTS:
        if name in existing:
            print(f"  = extra exists: {name}")
            continue
        payload = {
            "id": str(uuid.uuid4()), "name": name, "description": desc,
            "type": typ, "status": "Published", "endorsed": False,
            "domain": domain_id, "businessUse": desc, "updateFrequency": "Daily",
            "contacts": {"owner": [{"id": OWNER_OID, "description": "Demo owner"}]},
        }
        r = _req("POST", f"{UC_BASE}/datagovernance/catalog/dataproducts?api-version={API}", json=payload)
        status = "+" if r.status_code in (200,201) else "!"
        print(f"  {status} extra {name}: {r.status_code} {r.text[:200] if not r.ok else ''}")


def print_ui_steps(domain_id: str, product_id: str) -> None:
    print("\n" + "=" * 72)
    print("Demo objects are ready. Create the two workflows in the portal:")
    print("=" * 72)
    print(f"\nWorkflows page:\n  {PORTAL}\n")

    print("-" * 72)
    print("1. DATA PRODUCT ACCESS WORKFLOW  (sample)")
    print("-" * 72)
    print(f"""  - Open the Workflows page link above and click  + New
  - Name:            Demo - Data Product Access
  - Description:     Sample access workflow for the Sales Pipeline demo product
  - Workflow category: Data product access
  - Click Create
  - At "Start and wait for an approval":
        Approval type:   Pending on any
        Assigned to:     <your demo approver UPN, e.g. you@yourtenant.onmicrosoft.com>
  - Scope:
        Governance domain: {DOMAIN_NAME}
        Data product:      {PRODUCT_NAME}
        (domain id: {domain_id})
        (product id: {product_id})
  - Enable workflow, Save.
  - Demo as consumer:
        Unified Catalog -> Discovery -> Data products -> "{PRODUCT_NAME}"
        -> Request access -> fill form -> Send
        (your approver will get a Purview notification)
""")

    print("-" * 72)
    print("2. CATALOG CURATION (PUBLISH) WORKFLOW  (sample)")
    print("-" * 72)
    print(f"""  - Workflows page -> + New
  - Name:            Demo - Data Product Publish
  - Description:     Sample curation workflow that gates Draft -> Published
  - Workflow category: Catalog curation
  - Workflow type:     Data product publish
  - Click Create
  - At "Start and wait for an approval":
        Approval type:   Pending on any
        Assigned to:     <your demo approver UPN>
  - Scope:
        Governance domain: {DOMAIN_NAME}   (id: {domain_id})
  - Enable workflow, Save.
  - Demo as owner:
        Unified Catalog -> Catalog management -> Data products
        -> "{PRODUCT_NAME}" (currently Draft) -> Publish
        -> the workflow will route to the approver before it goes live.

Tip: create a second curation workflow with
     Workflow type = Term publish
     scoped to the same domain to demo glossary-term gating as well.
""")


def main() -> None:
    print(f"Tenant : {TENANT}")
    print(f"UC API : {UC_BASE}\n")
    did = ensure_domain()
    pid = ensure_product(did)
    ensure_extras(did)
    print_ui_steps(did, pid)


if __name__ == "__main__":
    main()
