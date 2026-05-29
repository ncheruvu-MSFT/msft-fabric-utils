"""Create Unified Catalog custom metadata attributes for the demo domain.

These appear at: Unified Catalog -> Catalog management -> Custom metadata.
"""
from __future__ import annotations
import os, sys, uuid, time, pathlib, subprocess, requests
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

TENANT = os.environ.get("TENANT_ID") or sys.exit("TENANT_ID missing")
DOMAIN = os.environ.get("DEMO_DOMAIN_ID", "708a1358-d626-47cf-96ce-2cc29254e147")
BASE   = f"https://{TENANT}-api.purview-service.microsoft.com"
V      = "2026-03-20-preview"

S = requests.Session()
S.mount("https://", HTTPAdapter(max_retries=Retry(
    total=6, backoff_factor=1.5, status_forcelist=(429,500,502,503,504),
    allowed_methods=frozenset(["GET","POST","PUT","DELETE"]))))

def tok():
    return subprocess.check_output(
        "az account get-access-token --resource https://purview.azure.net --query accessToken -o tsv",
        shell=True, text=True).strip()

def H():
    return {"Authorization": f"Bearer {tok()}", "Content-Type": "application/json"}

# Candidate endpoints — UC has moved this around between previews.
ENDPOINTS = [
    "/datagovernance/catalog/attributes",
    "/datagovernance/catalog/customattributes",
    "/datagovernance/catalog/customMetadata",
    "/datagovernance/catalog/metadata/attributes",
]

def discover_endpoint() -> str:
    for p in ENDPOINTS:
        r = S.get(f"{BASE}{p}?api-version={V}", headers=H(), timeout=30)
        print(f"  probe GET {p} -> {r.status_code}")
        if r.status_code in (200, 405):  # 405 = wrong method but path exists
            # if 405, still try POST against it
            return p
    sys.exit("No custom-metadata endpoint reachable on this tenant; create one from the portal once and re-run.")

ATTRIBUTES = [
    {"name":"Cost Center",         "fieldType":"String",  "description":"Owning cost center"},
    {"name":"Retention Days",      "fieldType":"Int",     "description":"Data retention horizon (days)"},
    {"name":"Contains PII",        "fieldType":"Boolean", "description":"Whether the asset contains PII"},
    {"name":"Data Classification", "fieldType":"String",  "description":"Confidentiality (Public|Internal|Confidential|Restricted)"},
]

def main():
    # Endpoint is known: /datagovernance/catalog/attributes  (PUT with UUID)
    base_url = f"{BASE}/datagovernance/catalog/attributes"
    print(f"Using endpoint: {base_url}\n")
    # List existing to make idempotent
    existing = {}
    r = S.get(f"{base_url}?api-version={V}", headers=H(), timeout=30)
    if r.ok:
        for a in r.json().get("value", []):
            existing[a.get("name")] = a.get("id")
    for a in ATTRIBUTES:
        aid = existing.get(a["name"]) or str(uuid.uuid4())
        body = {
            "id": aid,
            "name": a["name"],
            "description": a["description"],
            "fieldType": a["fieldType"],
            "appliesTo": ["DataProduct", "Term", "CriticalDataElement"],
            "domain": DOMAIN,
            "status": "Published",
            "isOptional": True,
        }
        r = S.put(f"{base_url}/{aid}?api-version={V}", headers=H(), json=body, timeout=60)
        tag = "+" if r.status_code in (200, 201) else "!"
        print(f"  {tag} {a['name']}: {r.status_code} {r.text[:300] if not r.ok else ''}")

if __name__ == "__main__":
    main()
