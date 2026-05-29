"""Create Fabric Mirrored Databases for each source via Fabric REST API.

Docs: https://learn.microsoft.com/fabric/database/mirrored-database/

Auth: uses ADO WIF token already exchanged for AAD by the pipeline,
or falls back to DefaultAzureCredential locally.
"""
from __future__ import annotations
import os, sys, json, time, pathlib, requests
from typing import Optional

ROOT = pathlib.Path(__file__).resolve().parents[1]
for env in (ROOT/".sources.env", ROOT/".env"):
    if env.exists():
        for ln in env.read_text().splitlines():
            if "=" in ln and not ln.startswith("#"):
                k,v=ln.split("=",1); os.environ.setdefault(k,v)

FABRIC = "https://api.fabric.microsoft.com/v1"

def token() -> str:
    try:
        from azure.identity import DefaultAzureCredential
        return DefaultAzureCredential().get_token("https://api.fabric.microsoft.com/.default").token
    except Exception as e:
        sys.exit(f"Could not get Fabric token: {e}")

def hdr(): return {"Authorization": f"Bearer {token()}", "Content-Type":"application/json"}

def get_workspace_id(name: str) -> str:
    r = requests.get(f"{FABRIC}/workspaces", headers=hdr()); r.raise_for_status()
    for w in r.json().get("value", []):
        if w["displayName"].lower() == name.lower(): return w["id"]
    sys.exit(f"Workspace '{name}' not found")

def create_mirrored(ws_id: str, payload: dict) -> Optional[str]:
    name = payload["displayName"]
    # idempotent
    r = requests.get(f"{FABRIC}/workspaces/{ws_id}/mirroredDatabases", headers=hdr())
    if r.ok:
        for db in r.json().get("value", []):
            if db["displayName"]==name:
                print(f"  exists: {name} ({db['id']})"); return db["id"]
    r = requests.post(f"{FABRIC}/workspaces/{ws_id}/mirroredDatabases", headers=hdr(), json=payload)
    if r.status_code in (201,202):
        loc = r.headers.get("Location")
        # poll if LRO
        for _ in range(30):
            if not loc: break
            p = requests.get(loc, headers=hdr())
            if p.status_code==200 and p.json().get("status") in ("Succeeded","Failed"):
                break
            time.sleep(4)
        print(f"  created: {name}")
        return r.json().get("id") if r.text else None
    print(f"  FAILED {name}: {r.status_code} {r.text[:200]}"); return None

def main():
    env = sys.argv[1] if len(sys.argv)>1 else "dev"
    ws_name = os.environ.get("FABRIC_WORKSPACE", f"fabric-de-{env}")
    ws = get_workspace_id(ws_name)
    print(f"Workspace {ws_name} -> {ws}")

    sql_fqdn = os.environ.get("SOURCE_SQL_FQDN","")
    pg_fqdn  = os.environ.get("SOURCE_PG_FQDN","")
    cosmos   = os.environ.get("SOURCE_COSMOS_EP","")
    cosmos_acct = os.environ.get("SOURCE_COSMOS_ACCT","")

    mirrors = [
        {
            "displayName": "mirror_sql_retail",
            "description": "Mirror of Azure SQL retail DB (customers, orders)",
            "definition": {
                "properties": {
                    "source": {"type":"AzureSqlDatabase","typeProperties":{
                        "serverFqdn": sql_fqdn, "database": os.environ.get("SOURCE_SQL_DB","retail")}},
                    "target": {"type":"MountedRelationalDatabase","typeProperties":{"defaultSchema":"dbo","format":"Delta"}}
                }
            }
        },
        {
            "displayName": "mirror_pg_hr",
            "description": "Mirror of Azure Postgres Flex HR DB (employees)",
            "definition": {
                "properties": {
                    "source": {"type":"AzurePostgreSql","typeProperties":{
                        "serverFqdn": pg_fqdn, "database": os.environ.get("SOURCE_PG_DB","hr")}},
                    "target": {"type":"MountedRelationalDatabase","typeProperties":{"defaultSchema":"public","format":"Delta"}}
                }
            }
        },
        {
            "displayName": "mirror_cosmos_telemetry",
            "description": "Mirror of Cosmos DB telemetry container",
            "definition": {
                "properties": {
                    "source": {"type":"CosmosDb","typeProperties":{
                        "accountEndpoint": cosmos, "database":"telemetry", "container":"events"}},
                    "target": {"type":"MountedRelationalDatabase","typeProperties":{"defaultSchema":"cosmos","format":"Delta"}}
                }
            }
        },
        {
            "displayName": "mirror_databricks_retail",
            "description": "Mirror of Databricks UC contoso.retail.products",
            "definition": {
                "properties": {
                    "source": {"type":"DatabricksUnityCatalog","typeProperties":{
                        "catalogName":"contoso","workspaceUrl": os.environ.get("SOURCE_DBX_URL","")}},
                    "target": {"type":"MountedRelationalDatabase","typeProperties":{"defaultSchema":"retail","format":"Delta"}}
                }
            }
        }
    ]
    for m in mirrors:
        print(f"\n→ {m['displayName']}")
        if "<<" in json.dumps(m): print("  skipping — endpoint missing"); continue
        create_mirrored(ws, m)

    print("\nNOTE: After creation, open each Mirrored DB in Fabric portal once → click 'Start replication'")
    print("Mirroring compute is free; you only pay source DB + OneLake storage (~$0.50/mo).")

if __name__=="__main__": main()
