"""Apply MIP sensitivity labels to scanned Fabric assets based on classification → label rules.

Reads contracts/labels/sensitivity-labels.yml `auto_label_rules` and for each scanned asset
in Purview, finds its classifications and assigns the highest-priority matching label.

Label assignment uses the Purview Data Map setLabels endpoint.
"""
from __future__ import annotations
import os, yaml, requests, pathlib
from typing import Optional

PURVIEW_ACCOUNT = os.environ["PURVIEW_ACCOUNT"]
BASE = f"https://{PURVIEW_ACCOUNT}.purview.azure.com"
API = "2023-09-01"

def token():
    t = os.environ.get("PURVIEW_ACCESS_TOKEN")
    if t: return t
    from azure.identity import DefaultAzureCredential
    return DefaultAzureCredential().get_token("https://purview.azure.net/.default").token

def H(): return {"Authorization": f"Bearer {token()}", "Content-Type":"application/json"}

def load_label_policy():
    p = pathlib.Path("contracts/labels/sensitivity-labels.yml")
    return yaml.safe_load(p.read_text(encoding="utf-8"))

def search_assets(keyword: str = "*", limit: int = 500):
    url = f"{BASE}/datamap/api/search/query?api-version={API}"
    body = {"keywords": keyword, "limit": limit}
    r = requests.post(url, headers=H(), json=body, timeout=60)
    r.raise_for_status()
    return r.json().get("value", [])

def asset_classifications(guid: str):
    url = f"{BASE}/datamap/api/atlas/v2/entity/guid/{guid}?api-version={API}"
    r = requests.get(url, headers=H(), timeout=30)
    if r.status_code >= 400: return []
    e = r.json().get("entity", {})
    cs = [c["typeName"] for c in e.get("classifications", [])]
    return cs

def pick_label(classifications, rules) -> Optional[str]:
    cs = set(classifications)
    default = None
    for r in rules:
        if "default" in r: default = r["default"]; continue
        any_cs = set(r.get("if_classifications_any", []))
        if any_cs & cs:
            return r.get("apply_label")
    return default

def assign_label(guid: str, label_name: str, default_label: str):
    """Stub — Purview label assignment via Data Map labels API.

    NOTE: Programmatic label application requires the MIP scanner-style API which is
    in preview. For demos we POST a tag annotation as a proxy so the label is visible
    in the asset details.
    """
    url = f"{BASE}/datamap/api/atlas/v2/entity/guid/{guid}/classifications?api-version={API}"
    body = [{"typeName": f"LABEL_{label_name.upper().replace('-','_')}", "attributes": {}, "propagate": True}]
    r = requests.post(url, headers=H(), json=body, timeout=30)
    print(f"  asset {guid}: {label_name} -> {r.status_code}")

def main():
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--default-label", default="Internal")
    args = ap.parse_args()
    pol = load_label_policy()
    rules = pol.get("auto_label_rules", [])
    print(f"Auto-label rules: {len(rules)}")
    assets = search_assets("contoso", 200)
    print(f"Scanned assets: {len(assets)}")
    counts = {}
    for a in assets[:50]:  # cap for demo run-time
        g = a.get("id"); 
        if not g: continue
        cs = asset_classifications(g)
        chosen = pick_label(cs, rules) or args.default_label
        counts[chosen] = counts.get(chosen,0)+1
        assign_label(g, chosen, args.default_label)
    print(f"Label distribution: {counts}")

if __name__ == "__main__":
    main()
