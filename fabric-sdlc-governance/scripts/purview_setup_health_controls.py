"""Create a custom Health Management control group + control nodes for the demo.

Endpoint: /datagovernance/health/controls?api-version=2024-02-01-preview
Visible at: Unified Catalog -> Health management -> Controls
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

TENANT = os.environ.get("TENANT_ID") or sys.exit("TENANT_ID missing")
BASE   = f"https://{TENANT}-api.purview-service.microsoft.com"
V      = "2024-02-01-preview"
URL    = f"{BASE}/datagovernance/health/controls"

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

GROUP_NAME = "Demo - Fabric SDLC Governance"
GROUP_DESC = "Demo control group covering data product readiness, glossary coverage, and lineage health for the Fabric Sales demo."

NODES = [
    {
        "name": "Data product has owner",
        "description": "Every published data product must declare a contacts.owner.",
    },
    {
        "name": "Data product has documentation link",
        "description": "Published data products must include a documentation URL.",
    },
    {
        "name": "Glossary terms are reviewed",
        "description": "Every glossary term has at least one approved reviewer.",
    },
    {
        "name": "Critical assets have lineage",
        "description": "Assets tagged Confidential-PII must have upstream lineage scanned within 30 days.",
    },
]

PALETTE = {
    "targetScore": 0.8,
    "fallbackStatusPaletteId": "00000000-0000-0000-0000-000000000004",
    "statusPaletteRules": [
        {"statusPaletteId": "00000000-0000-0000-0000-000000000002",
         "rule": {"type": "SimpleRule",
                  "typeProperties": {"checkPoint": "Score", "operator": "GreaterThanOrEqual", "operand": "0.8"}}},
        {"statusPaletteId": "00000000-0000-0000-0000-000000000003",
         "rule": {"type": "RuleGroup",
                  "typeProperties": {"groupOperator": "And",
                                     "rules": [
                                         {"type": "SimpleRule",
                                          "typeProperties": {"checkPoint": "Score", "operator": "LessThan", "operand": "0.8"}},
                                         {"type": "SimpleRule",
                                          "typeProperties": {"checkPoint": "Score", "operator": "GreaterThanOrEqual", "operand": "0.6"}},
                                     ]}}},
    ],
}

def list_controls():
    r = S.get(f"{URL}?api-version={V}", headers=H(), timeout=30)
    r.raise_for_status()
    return r.json().get("value", [])

def ensure_group():
    for c in list_controls():
        if c.get("name") == GROUP_NAME and c.get("type") == "ControlGroup":
            print(f"  = group exists: {GROUP_NAME} ({c['id']})")
            return c["id"]
    gid = str(uuid.uuid4())
    body = {
        "id": gid,
        "name": GROUP_NAME,
        "description": GROUP_DESC,
        "type": "ControlGroup",
        "status": "Enabled",
        "typeProperties": {},
        "statusPaletteConfig": PALETTE,
    }
    r = S.post(f"{URL}?api-version={V}", headers=H(), json=body, timeout=60)
    if r.status_code not in (200, 201):
        sys.exit(f"create group failed: {r.status_code} {r.text[:600]}")
    print(f"  + group created: {GROUP_NAME} ({gid})")
    return gid

def list_assessments():
    r = S.get(f"{BASE}/datagovernance/health/controls/assessments?api-version={V}", headers=H(), timeout=30)
    r.raise_for_status()
    return r.json().get("value", [])

def ensure_nodes(group_id):
    existing = {c.get("name"): c for c in list_controls() if c.get("type") == "ControlNode"}
    assess = list_assessments()
    print(f"  ({len(assess)} system assessments available)")
    # Map our demo nodes to first N system assessments
    for n, a in zip(NODES, assess):
        node_name = f"{n['name']}"
        if node_name in existing:
            print(f"  = node exists: {node_name}")
            continue
        nid = str(uuid.uuid4())
        body = {
            "id": nid,
            "name": node_name,
            "description": n["description"],
            "type": "ControlNode",
            "status": "Enabled",
            "typeProperties": {"groupId": group_id, "assessmentId": a["id"]},
            "statusPaletteConfig": PALETTE,
        }
        r = S.post(f"{URL}?api-version={V}", headers=H(), json=body, timeout=60)
        tag = "+" if r.status_code in (200, 201) else "!"
        print(f"  {tag} node {node_name} -> assessment '{a['name']}': {r.status_code} {r.text[:300] if not r.ok else ''}")

def main():
    print(f"Tenant: {TENANT}")
    print(f"URL   : {URL}\n")
    gid = ensure_group()
    ensure_nodes(gid)
    print("\nOpen the portal to view:")
    print(f"  https://purview.microsoft.com/datacatalog/governance/main/healthmanagement/controls?tid={TENANT}")
    print("\nNotes:")
    print("  - Reports tab is read-only (Power BI embeds, system-generated)")
    print("  - Actions auto-populate from control violations and DQ failures")
    print("  - Data quality + Data observability require their own sub-services (portal only)")

if __name__ == "__main__":
    main()
