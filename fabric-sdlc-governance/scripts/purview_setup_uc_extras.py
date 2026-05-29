"""Seed UC supporting items in the Fabric Demo - Sales domain so all sections are populated.

Creates (idempotent by name):
  - Glossary terms in the demo domain
  - Critical Data Elements in the demo domain
  - Tries to create one Objective (preview API may reject - logged)

Endpoint host: {tenant}-api.purview-service.microsoft.com
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
DOMAIN   = "708a1358-d626-47cf-96ce-2cc29254e147"  # Fabric Demo - Sales

S = requests.Session()
S.mount("https://", HTTPAdapter(max_retries=Retry(
    total=6, backoff_factor=1.5, status_forcelist=(429,500,502,503,504),
    allowed_methods=frozenset(["GET","POST","PUT","DELETE"]))))

_TOKEN = subprocess.check_output(
    f"az account get-access-token --subscription {SUB} --resource https://purview.azure.net --query accessToken -o tsv",
    shell=True, text=True).strip()

def H():
    return {"Authorization": f"Bearer {_TOKEN}", "Content-Type": "application/json"}

TERMS = [
    ("Pipeline",     "Open sales opportunities that have not yet closed (won or lost)."),
    ("Lead",         "An unqualified prospect captured from marketing or self-service."),
    ("Opportunity",  "A qualified deal in the pipeline tracked from creation to close."),
    ("Quota",        "The revenue target assigned to a seller for a fiscal period."),
]

CDES = [
    ("Account ID",     "Text",   "Unique identifier for a Contoso customer account."),
    ("Opportunity ID", "Text",   "Unique identifier for a sales opportunity record."),
    ("Lead Score",     "Number", "Numeric score (0-100) ranking a lead's purchase likelihood."),
    ("Deal Stage",     "Text",   "Lifecycle stage of an opportunity: Prospect, Qualified, Proposal, Won, Lost."),
]

def list_terms():
    r = S.get(f"{BASE}/datagovernance/catalog/terms?api-version={V}", headers=H(), timeout=30)
    if not r.ok:
        print(f"  (list terms {r.status_code}: {r.text[:200]})")
        return []
    return r.json().get("value", [])

def ensure_terms():
    existing = {t["name"]: t for t in list_terms() if t.get("domain") == DOMAIN}
    for name, desc in TERMS:
        if name in existing:
            print(f"  = term exists: {name}")
            continue
        tid = str(uuid.uuid4())
        body = {
            "id": tid, "name": name, "description": desc,
            "domain": DOMAIN, "status": "Published",
            "contacts": {"steward": [{"id": APPROVER, "description": ""}]},
        }
        r = S.post(f"{BASE}/datagovernance/catalog/terms?api-version={V}",
                   headers=H(), json=body, timeout=60)
        tag = "+" if r.ok else "!"
        print(f"  {tag} term {name}: {r.status_code} {r.text[:200] if not r.ok else ''}")

def list_cdes():
    r = S.get(f"{BASE}/datagovernance/catalog/criticalDataElements?api-version={V}", headers=H(), timeout=30)
    if not r.ok:
        print(f"  (list CDEs {r.status_code}: {r.text[:200]})")
        return []
    return r.json().get("value", [])

def ensure_cdes():
    existing = {c["name"]: c for c in list_cdes() if c.get("domain") == DOMAIN}
    for name, dtype, desc in CDES:
        if name in existing:
            print(f"  = CDE exists: {name}")
            continue
        cid = str(uuid.uuid4())
        body = {
            "id": cid, "name": name, "description": desc,
            "dataType": dtype, "domain": DOMAIN, "status": "Published",
            "contacts": {"owner": [{"id": APPROVER, "description": "Domain owner"}]},
        }
        r = S.post(f"{BASE}/datagovernance/catalog/criticalDataElements?api-version={V}",
                   headers=H(), json=body, timeout=60)
        tag = "+" if r.ok else "!"
        print(f"  {tag} CDE {name}: {r.status_code} {r.text[:200] if not r.ok else ''}")

def ensure_objective():
    name = "Grow qualified pipeline coverage to 3.5x"
    oid = str(uuid.uuid4())
    body = {
        "id": oid, "name": name,
        "description": "Increase qualified opportunity coverage in the Sales demo domain to 3.5x of quota by end of FY26.",
        "definition": "Qualified pipeline coverage = (sum of qualified opportunity ACV) / (assigned quota). Target = 3.5x measured at end of each fiscal quarter, rolled up across the Sales demo domain.",
        "domain": DOMAIN, "status": "Published",
        "targetDate": "2026-12-31",
        "contacts": {"owner": [{"id": APPROVER, "description": ""}]},
    }
    r = S.post(f"{BASE}/datagovernance/catalog/objectives?api-version={V}",
               headers=H(), json=body, timeout=60)
    tag = "+" if r.ok else "!"
    print(f"  {tag} objective: {r.status_code} {r.text[:300] if not r.ok else ''}")

def main():
    print(f"Domain: Fabric Demo - Sales ({DOMAIN})\n")
    print("Terms:");      ensure_terms()
    print("\nCDEs:");     ensure_cdes()
    print("\nObjective:"); ensure_objective()
    print(f"\nView: https://purview.microsoft.com/datacatalog/governance/main/businessdomains/{DOMAIN}?tid={TENANT}")

if __name__ == "__main__":
    main()
