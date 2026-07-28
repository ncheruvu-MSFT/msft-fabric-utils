"""Pull the full classic Purview Data Map (Atlas) estate into a single JSON export.

Reads the Atlas v2 / Data Map Search APIs and captures:
  * assets            - every catalogued entity, with attributes, classifications,
                        sensitivity labels and assigned glossary terms (meanings)
  * glossaries        - all business glossaries with their terms + categories
  * classificationDefs- classification type definitions (the label taxonomy)
  * lineage (opt-in)  - upstream/downstream process graph per asset (--with-lineage)

The export is the input for ``transform_to_onelake_catalog.py``, which converts it
into Microsoft Fabric OneLake catalog payloads (domains + tags + tag assignments).

Auth (in priority order):
  1. PURVIEW_ACCESS_TOKEN env var (a pre-acquired data-plane bearer token)
  2. ``az account get-access-token --resource https://purview.azure.net``
  3. azure.identity.DefaultAzureCredential

Usage:
  python pull_purview_datamap.py                 # full pull -> out/purview-datamap-export.json
  python pull_purview_datamap.py --with-lineage  # also capture lineage (slower)
  python pull_purview_datamap.py --out custom.json --max-assets 5000
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys
import time
from typing import Any, Iterable

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = pathlib.Path(__file__).resolve().parent
ATLAS_API_VERSION = "2023-09-01"
SEARCH_PAGE_SIZE = 1000   # max page size for the Data Map search/query API
BULK_BATCH = 100          # max guids per entity/bulk call
TIMEOUT = 90


# --------------------------------------------------------------------- env/auth
def _load_dotenv() -> None:
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def get_token() -> str:
    tok = os.environ.get("PURVIEW_ACCESS_TOKEN")
    if tok:
        return tok.strip()
    sub = os.environ.get("AZURE_SUBSCRIPTION_ID")
    cmd = ["az", "account", "get-access-token", "--resource",
           "https://purview.azure.net", "--query", "accessToken", "-o", "tsv"]
    if sub:
        cmd[2:2] = ["--subscription", sub]
    try:
        return subprocess.check_output(cmd, text=True, shell=(os.name == "nt")).strip()
    except Exception:  # noqa: BLE001 - fall through to managed identity / dev creds
        pass
    from azure.identity import DefaultAzureCredential
    return DefaultAzureCredential().get_token("https://purview.azure.net/.default").token


# ------------------------------------------------------------------ http client
class PurviewClient:
    def __init__(self, account: str) -> None:
        self.base = f"https://{account}.purview.azure.com"
        self.account = account
        self._token = get_token()
        self.session = requests.Session()
        retry = Retry(total=6, backoff_factor=1.5,
                      status_forcelist=(429, 500, 502, 503, 504),
                      allowed_methods=frozenset(["GET", "POST"]))
        self.session.mount("https://", HTTPAdapter(max_retries=retry))

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}",
                "Content-Type": "application/json"}

    def get(self, path: str, params: dict[str, Any] | None = None) -> requests.Response:
        params = {"api-version": ATLAS_API_VERSION, **(params or {})}
        return self.session.get(f"{self.base}{path}", headers=self._headers(),
                                params=params, timeout=TIMEOUT)

    def post(self, path: str, body: dict[str, Any],
             params: dict[str, Any] | None = None) -> requests.Response:
        params = {"api-version": ATLAS_API_VERSION, **(params or {})}
        return self.session.post(f"{self.base}{path}", headers=self._headers(),
                                 params=params, json=body, timeout=TIMEOUT)


# --------------------------------------------------------------------- pulls
def search_all_guids(client: PurviewClient, keywords: str,
                     max_assets: int | None) -> list[str]:
    """Page through the Data Map search/query API and collect every asset guid."""
    guids: list[str] = []
    seen: set[str] = set()
    continuation: str | None = None
    page = 0
    while True:
        body: dict[str, Any] = {"keywords": keywords, "limit": SEARCH_PAGE_SIZE}
        if continuation:
            body["continuationToken"] = continuation
        r = client.post("/datamap/api/search/query", body)
        if not r.ok:
            print(f"  ! search page {page} failed: {r.status_code} {r.text[:200]}")
            break
        data = r.json()
        rows = data.get("value", []) or []
        for row in rows:
            guid = row.get("id") or row.get("guid")
            if guid and guid not in seen:
                seen.add(guid)
                guids.append(guid)
        page += 1
        print(f"  page {page}: +{len(rows)} rows (total guids {len(guids)})")
        if max_assets and len(guids) >= max_assets:
            return guids[:max_assets]
        continuation = data.get("continuationToken")
        if not continuation or not rows:
            break
        time.sleep(0.2)
    return guids


def fetch_entities(client: PurviewClient, guids: list[str]) -> list[dict[str, Any]]:
    """Resolve full entity detail (attributes, classifications, labels, meanings)."""
    entities: list[dict[str, Any]] = []
    for batch in _chunks(guids, BULK_BATCH):
        params = [("guid", g) for g in batch]
        params.append(("api-version", ATLAS_API_VERSION))
        r = client.session.get(f"{client.base}/datamap/api/atlas/v2/entity/bulk",
                               headers=client._headers(), params=params, timeout=TIMEOUT)
        if not r.ok:
            print(f"  ! entity/bulk batch failed: {r.status_code} {r.text[:200]}")
            continue
        got = r.json().get("entities", []) or []
        entities.extend(got)
        print(f"  fetched {len(entities)}/{len(guids)} entities")
        time.sleep(0.1)
    return entities


def fetch_glossaries(client: PurviewClient) -> list[dict[str, Any]]:
    r = client.get("/datamap/api/atlas/v2/glossary", params={"limit": 1000})
    if not r.ok:
        print(f"  ! glossary list failed: {r.status_code} {r.text[:200]}")
        return []
    glossaries = r.json() or []
    detailed: list[dict[str, Any]] = []
    for g in glossaries:
        guid = g.get("guid")
        if not guid:
            continue
        d = client.get(f"/datamap/api/atlas/v2/glossary/{guid}/detailed")
        if d.ok:
            detailed.append(d.json())
        else:
            print(f"  ! glossary {guid} detailed failed: {d.status_code}")
            detailed.append(g)
    return detailed


def fetch_classification_defs(client: PurviewClient) -> list[dict[str, Any]]:
    r = client.get("/datamap/api/atlas/v2/types/typedefs", params={"type": "classification"})
    if not r.ok:
        print(f"  ! classification typedefs failed: {r.status_code} {r.text[:200]}")
        return []
    return r.json().get("classificationDefs", []) or []


def fetch_lineage(client: PurviewClient, guids: list[str],
                  depth: int = 3) -> dict[str, Any]:
    lineage: dict[str, Any] = {}
    for i, guid in enumerate(guids, 1):
        r = client.get(f"/datamap/api/atlas/v2/lineage/{guid}",
                       params={"direction": "BOTH", "depth": depth})
        if r.ok:
            lineage[guid] = r.json()
        if i % 50 == 0:
            print(f"  lineage {i}/{len(guids)}")
        time.sleep(0.05)
    return lineage


# --------------------------------------------------------------------- helpers
def _chunks(items: list[Any], size: int) -> Iterable[list[Any]]:
    for i in range(0, len(items), size):
        yield items[i:i + size]


# --------------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser(description="Export the classic Purview Data Map estate to JSON.")
    ap.add_argument("--account", default=None,
                    help="Purview account short name (defaults to PURVIEW_ACCOUNT env).")
    ap.add_argument("--keywords", default="*", help="Search keyword filter (default '*' = all).")
    ap.add_argument("--max-assets", type=int, default=None, help="Cap number of assets pulled.")
    ap.add_argument("--with-lineage", action="store_true", help="Also capture lineage per asset.")
    ap.add_argument("--lineage-depth", type=int, default=3)
    ap.add_argument("--out", default=str(ROOT / "out" / "purview-datamap-export.json"))
    args = ap.parse_args()

    _load_dotenv()
    account = args.account or os.environ.get("PURVIEW_ACCOUNT")
    if not account:
        sys.exit("PURVIEW_ACCOUNT not set (env or --account). See .env.example.")

    client = PurviewClient(account)
    print(f"Purview Data Map: {client.base}\n")

    print("1/4 Searching assets...")
    guids = search_all_guids(client, args.keywords, args.max_assets)
    print(f"  -> {len(guids)} asset guids\n")

    print("2/4 Fetching entity detail...")
    assets = fetch_entities(client, guids) if guids else []
    print(f"  -> {len(assets)} entities\n")

    print("3/4 Fetching glossaries + classification definitions...")
    glossaries = fetch_glossaries(client)
    classification_defs = fetch_classification_defs(client)
    print(f"  -> {len(glossaries)} glossaries, {len(classification_defs)} classification defs\n")

    lineage: dict[str, Any] = {}
    if args.with_lineage and guids:
        print("4/4 Fetching lineage...")
        lineage = fetch_lineage(client, guids, args.lineage_depth)
        print(f"  -> lineage for {len(lineage)} assets\n")
    else:
        print("4/4 Lineage skipped (use --with-lineage to include).\n")

    export = {
        "account": account,
        "endpoint": client.base,
        "exportedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "apiVersion": ATLAS_API_VERSION,
        "counts": {
            "assets": len(assets),
            "glossaries": len(glossaries),
            "classificationDefs": len(classification_defs),
            "lineage": len(lineage),
        },
        "assets": assets,
        "glossaries": glossaries,
        "classificationDefs": classification_defs,
        "lineage": lineage,
    }

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(export, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {out}  ({out.stat().st_size / 1024:.0f} KB)")
    print("\nNext: python transform_to_onelake_catalog.py "
          f"--export {out}")


if __name__ == "__main__":
    main()
