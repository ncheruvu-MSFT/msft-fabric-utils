"""Create classic Atlas typedefs in Purview Data Map.

These appear at: Unified Catalog -> Catalog management -> Classic types.
"""
from __future__ import annotations
import os, sys, pathlib, subprocess, requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
env = ROOT / ".env"
if env.exists():
    for ln in env.read_text().splitlines():
        if "=" in ln and not ln.startswith("#"):
            k, v = ln.split("=", 1)
            os.environ.setdefault(k, v)

ACCOUNT = os.environ.get("PURVIEW_ACCOUNT", "ngpurview")
BASE    = f"https://{ACCOUNT}.purview.azure.com"
URL     = f"{BASE}/catalog/api/atlas/v2/types/typedefs"

def tok():
    return subprocess.check_output(
        "az account get-access-token --resource https://purview.azure.net --query accessToken -o tsv",
        shell=True, text=True).strip()

TYPEDEFS = {
    "entityDefs": [
        {
            "name": "demo_fabric_lakehouse",
            "superTypes": ["DataSet"],
            "description": "Demo Atlas type representing a Microsoft Fabric Lakehouse",
            "serviceType": "Fabric",
            "typeVersion": "1.0",
            "attributeDefs": [
                {"name":"workspaceId","typeName":"string","cardinality":"SINGLE","isOptional":False,"isUnique":False,"isIndexable":True},
                {"name":"capacityId", "typeName":"string","cardinality":"SINGLE","isOptional":True, "isUnique":False,"isIndexable":True},
                {"name":"region",     "typeName":"string","cardinality":"SINGLE","isOptional":True, "isUnique":False,"isIndexable":False},
            ],
        },
        {
            "name": "demo_fabric_warehouse",
            "superTypes": ["DataSet"],
            "description": "Demo Atlas type representing a Microsoft Fabric Warehouse",
            "serviceType": "Fabric",
            "typeVersion": "1.0",
            "attributeDefs": [
                {"name":"workspaceId","typeName":"string","cardinality":"SINGLE","isOptional":False,"isUnique":False,"isIndexable":True},
                {"name":"sku",        "typeName":"string","cardinality":"SINGLE","isOptional":True, "isUnique":False,"isIndexable":False},
            ],
        },
    ],
    "classificationDefs": [
        {
            "name": "DEMO.Sensitive.Customer",
            "description": "Demo classification marking customer-sensitive data",
            "superTypes": [],
            "typeVersion": "1.0",
        }
    ],
}

def main():
    headers = {"Authorization": f"Bearer {tok()}", "Content-Type": "application/json"}
    r = requests.post(URL, headers=headers, json=TYPEDEFS, timeout=60)
    print(r.status_code, r.text[:800])
    if r.status_code == 409:
        print("  (one or more typedefs already exist; updating with PUT)")
        r = requests.put(URL, headers=headers, json=TYPEDEFS, timeout=60)
        print(r.status_code, r.text[:800])

if __name__ == "__main__":
    main()
