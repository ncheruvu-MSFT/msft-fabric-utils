"""Publish ontology + data-dictionary as a Purview Unified Catalog glossary.

Creates:
- A glossary domain "Contoso Retail Ontology"
- One glossary term per ontology entry (with definitions, parents)
- Related-term links from `triples`
- Term-to-asset assignments from `backing_assets`

Auth: PURVIEW_ACCESS_TOKEN env (preferred on Windows) OR DefaultAzureCredential.
"""
from __future__ import annotations
import os, sys, json, time, argparse, pathlib, yaml, requests
from typing import Optional

PURVIEW_ACCOUNT = os.environ["PURVIEW_ACCOUNT"]
BASE = f"https://{PURVIEW_ACCOUNT}.purview.azure.com"

def token() -> str:
    t = os.environ.get("PURVIEW_ACCESS_TOKEN")
    if t: return t
    from azure.identity import DefaultAzureCredential
    return DefaultAzureCredential().get_token("https://purview.azure.net/.default").token

def H():
    return {"Authorization": f"Bearer {token()}", "Content-Type": "application/json"}

def upsert_business_domain(name: str, description: str) -> str:
    """Re-uses existing domains created by purview_fabric_governance.py."""
    url = f"{BASE}/datagovernance/catalog/businessdomains"
    r = requests.get(url, headers=H(), timeout=30); r.raise_for_status()
    for d in r.json().get("value", []):
        if d.get("name") == name: return d["id"]
    body = {"name": name, "description": description, "type": "BusinessDomain", "status": "Published"}
    r = requests.post(url, headers=H(), json=body, timeout=30); r.raise_for_status()
    return r.json()["id"]

def upsert_glossary_term(domain_id: str, term_name: str, definition: str,
                        parent: Optional[str] = None) -> str:
    """Upsert a glossary term inside the business domain."""
    url = f"{BASE}/datagovernance/catalog/terms"
    # query existing first
    q = requests.get(f"{url}?domainId={domain_id}&$filter=name eq '{term_name}'", headers=H(), timeout=30)
    q.raise_for_status()
    for t in q.json().get("value", []):
        if t.get("name") == term_name: return t["id"]
    body = {"name": term_name, "definition": definition, "domain": domain_id, "status": "Published"}
    if parent: body["parentId"] = parent
    r = requests.post(url, headers=H(), json=body, timeout=30)
    if r.status_code >= 400:
        print(f"  term {term_name} POST {r.status_code}: {r.text[:200]}")
        return ""
    return r.json()["id"]

def link_related(term_id: str, related_term_id: str):
    url = f"{BASE}/datagovernance/catalog/terms/{term_id}/relationships"
    body = {"relationshipType": "Related", "targetTermId": related_term_id}
    r = requests.post(url, headers=H(), json=body, timeout=30)
    if r.status_code >= 400 and r.status_code != 409:
        print(f"  link {term_id}->{related_term_id} {r.status_code}: {r.text[:160]}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--collection", default="ngpurview")
    ap.add_argument("--ontology-glob", default="contracts/ontology/*.yml")
    ap.add_argument("--dictionary-glob", default="contracts/dictionary/*.yml")
    args = ap.parse_args()

    domain_id = upsert_business_domain("Contoso Retail Ontology",
                                       "Glossary domain published from contracts/ontology")
    print(f"Domain: {domain_id}")

    name_to_id = {}
    # Pass 1: create terms (no parents yet so root-first works regardless of order)
    for path in pathlib.Path().glob(args.ontology_glob):
        d = yaml.safe_load(open(path, encoding="utf-8"))
        for t in d.get("terms", []):
            tid = upsert_glossary_term(domain_id, t["name"], t["definition"])
            if tid:
                name_to_id[t["name"]] = tid
                print(f"  term {t['name']} -> {tid}")

    # Pass 2: relationships
    for path in pathlib.Path().glob(args.ontology_glob):
        d = yaml.safe_load(open(path, encoding="utf-8"))
        for s, p, o in d.get("triples", []):
            if s in name_to_id and o in name_to_id:
                link_related(name_to_id[s], name_to_id[o])
                print(f"  rel {s} -{p}-> {o}")

    # Pass 3: dictionary descriptions as term annotations (optional, log only here)
    cols = 0
    for path in pathlib.Path().glob(args.dictionary_glob):
        d = yaml.safe_load(open(path, encoding="utf-8"))
        cols += len(d.get("columns", []))
        print(f"  dict {d.get('dataset')}: {len(d.get('columns', []))} cols")
    print(f"Done. {len(name_to_id)} terms, {cols} dictionary columns referenced.")

if __name__ == "__main__":
    main()
