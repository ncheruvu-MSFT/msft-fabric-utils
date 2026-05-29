"""Build the lh_gold lakehouse from lh_silver CSVs (pure REST + pandas, no Spark).

Flow:
  1. Ensure lh_gold lakehouse exists in the target workspace.
  2. Read silver CSVs from data/sales/ (produced by seed_sales_samples.py).
  3. Apply each transform from items/lakehouse/lh_gold/transforms.py.
  4. Write each gold table as CSV to data/sales_gold/ and upload to
     lh_gold/Files/sales_gold/ via OneLake DFS.
  5. Call Fabric Load Table REST API for each CSV -> lh_gold/Tables/<name>.

Run AFTER seed_sales_samples.py --upload so the silver CSVs exist locally.
"""
from __future__ import annotations
import argparse, importlib.util, pathlib, sys, time
import pandas as pd
import requests
from azure.identity import DefaultAzureCredential

FABRIC = "https://api.fabric.microsoft.com/v1"
SILVER_DIR = pathlib.Path("data/sales")
GOLD_DIR   = pathlib.Path("data/sales_gold")
GOLD_DIR.mkdir(parents=True, exist_ok=True)


def _fab_tok() -> str:
    return DefaultAzureCredential().get_token("https://api.fabric.microsoft.com/.default").token

def _stg_tok() -> str:
    return DefaultAzureCredential().get_token("https://storage.azure.com/.default").token


def _resolve_workspace_id(name: str, tok: str) -> str:
    r = requests.get(f"{FABRIC}/workspaces", headers={"Authorization": f"Bearer {tok}"})
    r.raise_for_status()
    for w in r.json().get("value", []):
        if w["displayName"] == name:
            return w["id"]
    sys.exit(f"workspace not found: {name}")


def _ensure_lakehouse(ws_id: str, name: str, tok: str) -> str:
    h = {"Authorization": f"Bearer {tok}"}
    r = requests.get(f"{FABRIC}/workspaces/{ws_id}/items?type=Lakehouse", headers=h)
    r.raise_for_status()
    for it in r.json().get("value", []):
        if it["displayName"] == name:
            print(f"  lakehouse exists: {name}")
            return it["id"]
    print(f"  creating lakehouse: {name}")
    r = requests.post(f"{FABRIC}/workspaces/{ws_id}/lakehouses",
                      headers={**h, "Content-Type": "application/json"},
                      json={"displayName": name})
    if r.status_code not in (200, 201, 202):
        sys.exit(f"lakehouse create failed {r.status_code}: {r.text}")
    # re-resolve id
    r = requests.get(f"{FABRIC}/workspaces/{ws_id}/items?type=Lakehouse", headers=h)
    r.raise_for_status()
    for it in r.json().get("value", []):
        if it["displayName"] == name:
            return it["id"]
    sys.exit("lakehouse not found after create")


def _upload(ws_name: str, lh_name: str, files: list[pathlib.Path], folder: str) -> None:
    tok = _stg_tok()
    base = f"https://onelake.dfs.fabric.microsoft.com/{ws_name}/{lh_name}.Lakehouse/Files/{folder}"
    h = {"Authorization": f"Bearer {tok}"}
    for p in files:
        url = f"{base}/{p.name}"
        data = p.read_bytes()
        requests.put(url + "?resource=file", headers=h).raise_for_status()
        requests.patch(url + "?action=append&position=0",
                       headers={**h, "Content-Length": str(len(data))}, data=data).raise_for_status()
        requests.patch(url + f"?action=flush&position={len(data)}", headers=h).raise_for_status()
        print(f"  uploaded {p.name} -> Files/{folder}/{p.name}")


def _load_table(ws_id: str, lh_id: str, name: str, rel_path: str, tok: str) -> None:
    body = {
        "relativePath": rel_path,
        "pathType": "File",
        "mode": "Overwrite",
        "recursive": False,
        "formatOptions": {"format": "Csv", "header": True, "delimiter": ","},
    }
    h = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}
    r = requests.post(f"{FABRIC}/workspaces/{ws_id}/lakehouses/{lh_id}/tables/{name}/load",
                      headers=h, json=body)
    if r.status_code not in (200, 201, 202):
        print(f"  [skip] {name}: {r.status_code} {r.text[:200]}")
        return
    loc = r.headers.get("Location")
    for _ in range(40):
        time.sleep(3)
        rr = requests.get(loc, headers={"Authorization": f"Bearer {tok}"})
        if rr.status_code == 200:
            s = rr.json().get("status")
            if s in ("Succeeded", "Completed"):
                print(f"  loaded Tables/{name}")
                return
            if s == "Failed":
                print(f"  [fail] {name}: {rr.text[:200]}")
                return
    print(f"  [timeout] {name}")


def _load_transforms(path: pathlib.Path):
    spec = importlib.util.spec_from_file_location("gold_transforms", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.GOLD_TABLES


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--lakehouse", default="lh_gold")
    ap.add_argument("--transforms",
                    default="fabric-sdlc-governance/items/lakehouse/lh_gold/transforms.py")
    args = ap.parse_args()

    if not SILVER_DIR.exists():
        sys.exit(f"silver CSVs not found in {SILVER_DIR}/ — run seed_sales_samples.py first")

    silver = {p.stem: pd.read_csv(p) for p in SILVER_DIR.glob("*.csv")}
    print(f"loaded {len(silver)} silver tables: {sorted(silver)}")

    gold_specs = _load_transforms(pathlib.Path(args.transforms))
    print(f"transforms registered: {sorted(gold_specs)}")

    gold_paths = []
    for name, fn in gold_specs.items():
        df = fn(silver)
        p = GOLD_DIR / f"{name}.csv"
        df.to_csv(p, index=False)
        gold_paths.append(p)
        print(f"  built {name}  ({len(df)} rows, {len(df.columns)} cols)")

    tok = _fab_tok()
    ws_id = _resolve_workspace_id(args.workspace, tok)
    print(f"workspace = {args.workspace} ({ws_id})")
    lh_id = _ensure_lakehouse(ws_id, args.lakehouse, tok)
    print(f"lakehouse = {args.lakehouse} ({lh_id})")

    print(f"\nUploading to OneLake: {args.workspace} / {args.lakehouse}.Lakehouse / Files/sales_gold/")
    _upload(args.workspace, args.lakehouse, gold_paths, "sales_gold")

    print(f"\nMaterializing Delta tables in {args.lakehouse}.Lakehouse/Tables/")
    for p in gold_paths:
        _load_table(ws_id, lh_id, p.stem, f"Files/sales_gold/{p.name}", tok)


if __name__ == "__main__":
    main()
