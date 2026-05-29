"""Emit cross-source lineage into Purview via Atlas v2 (datamap data plane).

Uses **typed** Atlas entities so the Purview portal lineage tab renders the
nodes with proper source icons (Azure SQL, Azure Postgres, Cosmos DB,
Databricks, Fabric) instead of grey 'atlas_core' boxes.

Endpoint: https://{account}.purview.azure.com/datamap/api/atlas/v2/...
This Atlas v2 surface is still alive on Unified-Catalog accounts.

Lineage chain:
  azure_sql_table.dbo.customers          -+
  azure_sql_table.dbo.orders             -+
  azure_postgresql_table.public.employees-+-> Process: nb_build_silver  -> fabric_lakehouse_table (silver)
  azure_cosmosdb_sqlapi_collection.events-+                                        |
  databricks_table.products              -+                                        v
                                                Process: silver_to_gold  -> fabric_lakehouse_table (gold)

Notes
-----
* Each typed source uses the same qualifiedName format the actual scanner
  emits, so when scans run later the pre-created lineage stub will bind to the
  scanned guids automatically (Atlas upserts on qualifiedName).
* fabric_lakehouse_table enforces a regex requiring a Fabric workspace GUID
  and lakehouse GUID. Until the real capacity is provisioned we use placeholder
  GUIDs from env (FABRIC_WS_GUID / FABRIC_LH_SILVER_GUID / FABRIC_LH_GOLD_GUID).
* Bulk creation is split per-entity so a single 400 (bad regex) doesn't kill
  the whole batch.
"""
from __future__ import annotations
import os, uuid, requests, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
for env in (ROOT/".sources.env", ROOT/".env"):
    if env.exists():
        for ln in env.read_text().splitlines():
            if "=" in ln and not ln.startswith("#"):
                k,v = ln.split("=",1); os.environ.setdefault(k,v)

PURVIEW = os.environ.get("PURVIEW_ACCOUNT","ngpurview")
ATLAS   = f"https://{PURVIEW}.purview.azure.com/datamap/api/atlas/v2"
APIVER  = "2023-09-01"

def tok():
    from azure.identity import DefaultAzureCredential
    return DefaultAzureCredential().get_token("https://purview.azure.net/.default").token
def H():
    return {"Authorization": f"Bearer {tok()}", "Content-Type": "application/json"}

# ---------- helpers ----------
def entity(typ, qname, name, extra=None):
    return {
        "typeName": typ,
        "guid": f"-{uuid.uuid4().int % 10_000_000}",
        "attributes": {"qualifiedName": qname, "name": name, **(extra or {})},
    }

def upsert_one(ent):
    body = {"entities": [ent]}
    r = requests.post(f"{ATLAS}/entity/bulk?api-version={APIVER}", headers=H(), json=body)
    qn = ent["attributes"]["qualifiedName"]
    if r.ok:
        j = r.json().get("mutatedEntities", {}) or {}
        action = "CREATE" if j.get("CREATE") else ("UPDATE" if j.get("UPDATE") else "NOOP")
        print(f"  ent  {ent['typeName']:<35} {qn[:80]}  -> {action}")
        return True
    print(f"  ent  {ent['typeName']:<35} {qn[:80]}  -> FAIL {r.status_code} {r.text[:200]}")
    return False

def relate(typ, end1_type, end1_qname, end2_type, end2_qname):
    body = {
        "typeName": typ,
        "end1": {"typeName": end1_type, "uniqueAttributes": {"qualifiedName": end1_qname}},
        "end2": {"typeName": end2_type, "uniqueAttributes": {"qualifiedName": end2_qname}},
    }
    r = requests.post(f"{ATLAS}/relationship?api-version={APIVER}", headers=H(), json=body)
    short = lambda q: q.rsplit("/", 1)[-1]
    tag = f"{typ}: {short(end1_qname)} -> {short(end2_qname)}"
    if r.ok or r.status_code == 409:
        print(f"  rel  {tag}: {r.status_code}")
    else:
        print(f"  rel  {tag}: {r.status_code} {r.text[:200]}")

# ---------- main ----------
def main():
    sql    = os.environ.get("SOURCE_SQL_FQDN", "sql-fbrcdemo-dev-cac-001.database.windows.net")
    sqldb  = os.environ.get("SOURCE_SQL_DB",   "retail")
    pg     = os.environ.get("SOURCE_PG_FQDN",  "psql-fbrcdemo-dev-cac-001.postgres.database.azure.com")
    pgdb   = os.environ.get("SOURCE_PG_DB",    "hr")
    cosmos = os.environ.get("SOURCE_COSMOS_ACCT", "cosmos-fbrcdemo-dev-cac-t3dzg4vj72bsa")
    cosdb  = os.environ.get("SOURCE_COSMOS_DB", "telemetry")
    cosctn = os.environ.get("SOURCE_COSMOS_COLLECTION", "events")
    dbx_url= os.environ.get("SOURCE_DBX_URL", "adb-0000.0.azuredatabricks.net")
    ws_name= os.environ.get("FABRIC_WORKSPACE", "fabric-de-dev")

    # Auto-load real workspace + lakehouse GUIDs from the sidecar map produced
    # by scripts/fabric_workspaces_apply.py. Env vars still override.
    import json as _json
    side_path = ROOT / "contracts" / "governance" / ".workspaces.json"
    side = {}
    if side_path.exists():
        side = _json.loads(side_path.read_text())
    env_key = os.environ.get("FABRIC_ENV", "dev")
    env_entry = side.get(env_key, {})
    if env_entry.get("name"):
        ws_name = env_entry["name"]
    lhs = env_entry.get("lakehouses", {})

    fab_host  = os.environ.get("FABRIC_HOST",          "app.fabric.microsoft.com")
    fab_ws    = os.environ.get("FABRIC_WS_GUID",       env_entry.get("id", "00000000-0000-0000-0000-aaaa00000001"))
    fab_lhsil = os.environ.get("FABRIC_LH_SILVER_GUID",lhs.get("lh_silver", "00000000-0000-0000-0000-aaaa00000002"))
    fab_lhgld = os.environ.get("FABRIC_LH_GOLD_GUID",  lhs.get("lh_gold",   "00000000-0000-0000-0000-aaaa00000003"))

    qn_customers = f"mssql://{sql}/{sqldb}/dbo/customers"
    qn_orders    = f"mssql://{sql}/{sqldb}/dbo/orders"
    qn_employees = f"postgresql://{pg}/{pgdb}/public/employees"
    qn_events    = f"https://{cosmos}.documents.azure.com/dbs/{cosdb}/colls/{cosctn}"
    qn_products  = f"https://{dbx_url}/main/silver/products"

    qn_silver = f"https://{fab_host}/groups/{fab_ws}/lakehouses/{fab_lhsil}/tables/customer_orders_enriched"
    qn_gold   = f"https://{fab_host}/groups/{fab_ws}/lakehouses/{fab_lhgld}/tables/fct_orders"

    qn_proc_silver = f"fabric://workspace/{ws_name}/notebook/nb_build_silver"
    qn_proc_gold   = f"fabric://workspace/{ws_name}/pipeline/silver_to_gold"

    print("Upserting typed source entities...")
    upsert_one(entity("azure_sql_table",                  qn_customers, "customers"))
    upsert_one(entity("azure_sql_table",                  qn_orders,    "orders"))
    upsert_one(entity("azure_postgresql_table",           qn_employees, "employees"))
    upsert_one(entity("azure_cosmosdb_sqlapi_collection", qn_events,    "events"))
    upsert_one(entity("databricks_table",                 qn_products,  "products",
                      extra={"catalogName":"main","schemaName":"silver","tableType":"MANAGED"}))

    print("\nUpserting Fabric lakehouse tables (placeholder GUIDs)...")
    upsert_one(entity("fabric_lakehouse_table", qn_silver, "customer_orders_enriched"))
    upsert_one(entity("fabric_lakehouse_table", qn_gold,   "fct_orders"))

    print("\nUpserting Process entities...")
    upsert_one(entity("Process", qn_proc_silver, "nb_build_silver",
                      extra={"description":"Joins 4 mirrored sources -> silver lakehouse table"}))
    upsert_one(entity("Process", qn_proc_gold,   "silver_to_gold",
                      extra={"description":"Promotes silver lakehouse table -> gold lakehouse table"}))

    print("\nCreating dataset->process input edges...")
    relate("dataset_process_inputs", "azure_sql_table",                  qn_customers, "Process", qn_proc_silver)
    relate("dataset_process_inputs", "azure_sql_table",                  qn_orders,    "Process", qn_proc_silver)
    relate("dataset_process_inputs", "azure_postgresql_table",           qn_employees, "Process", qn_proc_silver)
    relate("dataset_process_inputs", "azure_cosmosdb_sqlapi_collection", qn_events,    "Process", qn_proc_silver)
    relate("dataset_process_inputs", "databricks_table",                 qn_products,  "Process", qn_proc_silver)

    print("\nCreating process->dataset output + downstream edges...")
    relate("process_dataset_outputs", "Process", qn_proc_silver, "fabric_lakehouse_table", qn_silver)
    relate("dataset_process_inputs",  "fabric_lakehouse_table", qn_silver, "Process", qn_proc_gold)
    relate("process_dataset_outputs", "Process", qn_proc_gold,   "fabric_lakehouse_table", qn_gold)

    print("\nDone. Open the lineage tab on any of these typed assets in the portal:")
    print(f"  https://purview.microsoft.com/{PURVIEW}/catalog -> search 'customer_orders_enriched' -> Lineage")

if __name__ == "__main__":
    main()
