"""Create Fabric workspaces per environment from contracts/governance/domains.yml.

For each `environments[*].fabric_workspace` value in domains.yml this script:
  1. Lists existing workspaces (GET /v1/workspaces).
  2. Creates the workspace if missing (POST /v1/workspaces) and assigns the
     Fabric capacity given by env var FABRIC_CAPACITY_ID.
  3. Optionally adds role assignments (admin) for principals listed via env
     FABRIC_WS_ADMINS (comma-separated AAD object IDs).
  4. Tags the workspace by writing the workspace GUID back to a sidecar file
     `contracts/governance/.workspaces.json` so other scripts (lineage_demo.py,
     fabric_deploy.py) can resolve names → GUIDs.

Env vars
--------
  TENANT_ID            - AAD tenant for token (read from .env)
  FABRIC_CAPACITY_ID   - GUID of an F-SKU / Trial capacity (required to create)
                         If missing, the script will list-only and warn.
  FABRIC_WS_ADMINS     - Optional comma-separated AAD object IDs to add as
                         workspace admins.

Idempotent: safe to re-run.
"""
from __future__ import annotations
import os, sys, json, pathlib, time, requests, yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
GOV  = ROOT / "contracts" / "governance"
SIDE = GOV / ".workspaces.json"

# load .env
for env in (ROOT/".env",):
    if env.exists():
        for ln in env.read_text().splitlines():
            if "=" in ln and not ln.startswith("#"):
                k, v = ln.split("=", 1); os.environ.setdefault(k, v)

CAPACITY = os.environ.get("FABRIC_CAPACITY_ID", "").strip()
ADMINS   = [a.strip() for a in os.environ.get("FABRIC_WS_ADMINS", "").split(",") if a.strip()]

API = "https://api.fabric.microsoft.com/v1"

# ---- Auth (cached) ---------------------------------------------------------
_TOKEN = {"t": None, "exp": 0}
def token():
    now = int(time.time())
    if _TOKEN["t"] and _TOKEN["exp"] - 120 > now:
        return _TOKEN["t"]
    from azure.identity import DefaultAzureCredential
    tk = DefaultAzureCredential().get_token("https://api.fabric.microsoft.com/.default")
    _TOKEN["t"] = tk.token; _TOKEN["exp"] = tk.expires_on
    return tk.token

def H():
    return {"Authorization": f"Bearer {token()}", "Content-Type": "application/json"}

from requests.adapters import HTTPAdapter
try: from urllib3.util.retry import Retry
except ImportError: from requests.packages.urllib3.util.retry import Retry  # type: ignore
S = requests.Session()
S.mount("https://", HTTPAdapter(max_retries=Retry(
    total=6, backoff_factor=1.5,
    status_forcelist=(429, 500, 502, 503, 504),
    allowed_methods=frozenset(["GET", "POST", "PUT", "DELETE"]),
)))

# ---- Workspace helpers -----------------------------------------------------
def list_workspaces() -> list[dict]:
    r = S.get(f"{API}/workspaces", headers=H(), timeout=60)
    r.raise_for_status()
    return r.json().get("value", [])

def create_workspace(name: str) -> str | None:
    body = {"displayName": name, "description": f"Fabric SDLC env workspace ({name})"}
    if CAPACITY: body["capacityId"] = CAPACITY
    r = S.post(f"{API}/workspaces", headers=H(), json=body, timeout=60)
    if r.status_code in (200, 201):
        return r.json().get("id")
    print(f"  ! create {name} failed {r.status_code}: {r.text[:240]}")
    return None

def assign_capacity(ws_id: str):
    if not CAPACITY: return
    r = S.post(f"{API}/workspaces/{ws_id}/assignToCapacity",
               headers=H(), json={"capacityId": CAPACITY}, timeout=60)
    if r.status_code not in (200, 202):
        print(f"  ! assign capacity {ws_id} {r.status_code}: {r.text[:200]}")

def add_admin(ws_id: str, oid: str):
    body = {"principal": {"id": oid, "type": "User"}, "role": "Admin"}
    r = S.post(f"{API}/workspaces/{ws_id}/roleAssignments", headers=H(), json=body, timeout=60)
    if r.status_code not in (200, 201) and r.status_code != 409:
        print(f"    ! add admin {oid} {r.status_code}: {r.text[:160]}")

def list_lakehouses(ws_id: str) -> list[dict]:
    r = S.get(f"{API}/workspaces/{ws_id}/lakehouses", headers=H(), timeout=60)
    if not r.ok: return []
    return r.json().get("value", [])

def create_lakehouse(ws_id: str, name: str) -> str | None:
    r = S.post(f"{API}/workspaces/{ws_id}/lakehouses", headers=H(),
               json={"displayName": name, "description": f"{name} medallion lakehouse"}, timeout=60)
    if r.status_code in (200, 201):
        return r.json().get("id")
    if r.status_code == 202:
        # async LRO — extract id from Location header eventually; simplest: list
        for lh in list_lakehouses(ws_id):
            if lh.get("displayName") == name: return lh.get("id")
    print(f"    ! lakehouse {name} {r.status_code}: {r.text[:160]}")
    return None

def main():
    cfg = yaml.safe_load((GOV / "domains.yml").read_text(encoding="utf-8"))
    envs = cfg["environments"]
    print(f"Fabric API: {API}")
    print(f"Capacity:   {CAPACITY or '(none — list/skip-create mode)'}")
    print(f"Admins:     {ADMINS or '(none)'}\n")

    existing = {w["displayName"]: w["id"] for w in list_workspaces()}
    side = json.loads(SIDE.read_text()) if SIDE.exists() else {}

    for env in envs:
        name = env["fabric_workspace"]
        if name in existing:
            wid = existing[name]
            print(f"= exists: {name}  ({wid})")
        else:
            if not CAPACITY:
                print(f"- skip create (no capacity): {name}")
                continue
            wid = create_workspace(name)
            if not wid: continue
            print(f"+ created: {name}  ({wid})")
            assign_capacity(wid)
        for oid in ADMINS:
            add_admin(wid, oid)

        # Provision silver + gold lakehouses
        existing_lh = {lh["displayName"]: lh["id"] for lh in list_lakehouses(wid)}
        lh_map = {}
        for lh_name in ("lh_silver", "lh_gold"):
            if lh_name in existing_lh:
                lh_map[lh_name] = existing_lh[lh_name]
                print(f"    = lakehouse exists: {lh_name}  ({existing_lh[lh_name]})")
            else:
                lid = create_lakehouse(wid, lh_name)
                if lid:
                    lh_map[lh_name] = lid
                    print(f"    + lakehouse: {lh_name}  ({lid})")
        side[env["key"]] = {"name": name, "id": wid, "lakehouses": lh_map}

    SIDE.write_text(json.dumps(side, indent=2))
    print(f"\nWorkspace map written: {SIDE}")
    print(json.dumps(side, indent=2))

if __name__ == "__main__":
    main()
