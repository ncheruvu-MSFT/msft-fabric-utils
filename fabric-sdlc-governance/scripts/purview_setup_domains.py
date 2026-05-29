"""Create Purview Unified Catalog governance domains + subdomains + map ontology terms.

Uses the new Purview Data Governance (Unified Catalog) APIs at /datagovernance/catalog/.
Idempotent: domain creation by name, term upsert.
"""
from __future__ import annotations
import os, sys, json, uuid, requests, pathlib, yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
for env in (ROOT/".env",):
    if env.exists():
        for ln in env.read_text().splitlines():
            if "=" in ln and not ln.startswith("#"):
                k,v=ln.split("=",1); os.environ.setdefault(k,v)

PURVIEW = os.environ.get("PURVIEW_ACCOUNT","ngpurview")
TENANT  = os.environ.get("TENANT_ID","00000000-0000-0000-0000-000000000000")
# Unified Catalog data plane endpoint (per-tenant)
BASE = f"https://{TENANT}-api.purview-service.microsoft.com"
API  = "2026-03-20-preview"

def tok():
    from azure.identity import DefaultAzureCredential
    return DefaultAzureCredential().get_token("https://purview.azure.net/.default").token
def H(): return {"Authorization":f"Bearer {tok()}","Content-Type":"application/json"}

DOMAINS = [
    {"name":"Contoso Retail",     "description":"Customer-facing retail commerce: customers, orders, products",
     "ownerEmails":["admin@MngEnvMCAP219373.onmicrosoft.com"]},
    {"name":"Contoso HR",         "description":"Workforce + compensation (high-sensitivity)",
     "ownerEmails":["admin@MngEnvMCAP219373.onmicrosoft.com"]},
    {"name":"Contoso Telemetry",  "description":"Behavioural / clickstream / IoT events",
     "ownerEmails":["admin@MngEnvMCAP219373.onmicrosoft.com"]},
    {"name":"Contoso Finance",    "description":"Revenue, GL, treasury (restricted)",
     "ownerEmails":["admin@MngEnvMCAP219373.onmicrosoft.com"]},
]

def upsert_domain(d):
    r = requests.get(f"{BASE}/datagovernance/catalog/businessdomains?api-version={API}", headers=H())
    if r.ok:
        for x in r.json().get("value",[]):
            if x.get("name","").lower()==d["name"].lower():
                print(f"  exists: {d['name']} ({x['id']})"); return x["id"]
    payload = {"id": str(uuid.uuid4()), "name":d["name"], "description":d["description"],
               "type":"FunctionalUnit", "status":"Draft", "isRestricted": False}
    r = requests.post(f"{BASE}/datagovernance/catalog/businessdomains?api-version={API}",
                      headers=H(), json=payload)
    if r.status_code in (200,201):
        did = r.json()["id"]; print(f"  created: {d['name']} -> {did}")
        return did
    print(f"  FAILED {d['name']}: {r.status_code} {r.text[:300]}")

def map_to_collection(domain_id, domain_name, description, collection_name=None):
    """Link a UC governance domain to a Data Map collection (Data estate mapping).
    Uses PUT on the businessdomains resource with `domains[].relatedCollections[]`.
    """
    collection_name = collection_name or os.environ.get("PURVIEW_COLLECTION_ID", PURVIEW)
    payload = {
        "id": domain_id,
        "name": domain_name,
        "description": description,
        "type": "FunctionalUnit",
        "status": "Draft",
        "isRestricted": False,
        "domains": [{
            "name": collection_name,
            "friendlyName": collection_name,
            "relatedCollections": [{
                "name": collection_name,
                "friendlyName": collection_name,
                "parentCollection": {"type": "CollectionReference", "refName": collection_name},
            }],
        }],
    }
    r = requests.put(f"{BASE}/datagovernance/catalog/businessdomains/{domain_id}?api-version={API}",
                     headers=H(), json=payload)
    if r.status_code in (200, 201):
        print(f"  mapped: {domain_name} -> collection '{collection_name}'")
    else:
        print(f"  MAP FAILED {domain_name}: {r.status_code} {r.text[:300]}")

def map_ontology(domain_id, domain_name):
    """Push terms from contracts/ontology/retail.yml into the matching domain."""
    onto = ROOT / "contracts" / "ontology" / "retail.yml"
    if not onto.exists(): return
    data = yaml.safe_load(onto.read_text())
    for term in data.get("terms", []):
        # only push terms aligned to this domain (simple keyword match)
        if domain_name.split()[1].lower() not in (term.get("domain","retail").lower()+"retail"):
            continue
        payload = {"id": str(uuid.uuid4()), "name":term["name"], "description":term.get("definition",""),
                   "domain": domain_id, "status":"Draft", "acronyms":[]}
        r=requests.post(f"{BASE}/datagovernance/catalog/terms?api-version={API}",
                        headers=H(), json=payload)
        print(f"   term {term['name']}: {r.status_code}")

def main():
    print(f"Purview: {BASE}")
    ids = {}
    descs = {d["name"]: d["description"] for d in DOMAINS}
    for d in DOMAINS:
        did = upsert_domain(d)
        if did: ids[d["name"]] = did
    print("\nLinking governance domains to Data Map collection...")
    for name, did in ids.items():
        map_to_collection(did, name, descs[name])
    print("\nMapping ontology terms to 'Contoso Retail' domain...")
    if "Contoso Retail" in ids:
        map_ontology(ids["Contoso Retail"], "Contoso Retail")
    print("\nDomains ready. Self-service catalog visible at:")
    print(f"  https://purview.microsoft.com/{PURVIEW}/catalog")

if __name__=="__main__": main()
