"""Seed an end-to-end Fabric data estate with lineage in Purview classic catalog.

Estate (Bronze -> Silver -> Gold -> BI):
  azure_sql_db_table   : contoso.sql.dbo.Customers, contoso.sql.dbo.Orders   (Bronze sources)
  demo_fabric_lakehouse: ngfabric.lh_bronze (mirrored), ngfabric.lh_silver   (Silver)
  demo_fabric_warehouse: ngfabric.wh_gold                                    (Gold)
  powerbi_dataset      : ngfabric.semantic.sales_pipeline                    (BI)

Lineage processes:
  ingest_customers : sql Customers -> lh_bronze
  ingest_orders    : sql Orders    -> lh_bronze
  curate_silver    : lh_bronze     -> lh_silver
  load_gold        : lh_silver     -> wh_gold
  refresh_dataset  : wh_gold       -> sales_pipeline

Host: ngpurview.purview.azure.com (Atlas v2)
"""
from __future__ import annotations
import os, sys, pathlib, subprocess, requests
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

ACCOUNT = os.environ.get("PURVIEW_ACCOUNT", "ngpurview")
TENANT  = os.environ["TENANT_ID"]
SUB     = os.environ.get("AZ_SUBSCRIPTION_ID", "31613fe0-1e9b-4a97-b771-dc48fbaa0fbb")
BASE    = f"https://{ACCOUNT}.purview.azure.com"
ATLAS   = f"{BASE}/catalog/api/atlas/v2"

S = requests.Session()
S.mount("https://", HTTPAdapter(max_retries=Retry(
    total=6, backoff_factor=1.5, status_forcelist=(429,500,502,503,504),
    allowed_methods=frozenset(["GET","POST","PUT","DELETE"]))))

_TOKEN = subprocess.check_output(
    f"az account get-access-token --subscription {SUB} --resource https://purview.azure.net --query accessToken -o tsv",
    shell=True, text=True).strip()

def H():
    return {"Authorization": f"Bearer {_TOKEN}", "Content-Type": "application/json"}

# (typeName, qualifiedName, name, extraAttrs)
ENTITIES = [
    ("DataSet",    "mssql://contoso.sql/dbo/Customers",
     "Customers", {"description": "Source CRM customer table (Bronze)."}),
    ("DataSet",    "mssql://contoso.sql/dbo/Orders",
     "Orders",    {"description": "Source CRM orders table (Bronze)."}),
    ("demo_fabric_lakehouse", "fabric://ngfabric/lh_bronze",
     "lh_bronze", {"description": "Bronze lakehouse - mirrored landing zone.",
                   "workspaceId": "11111111-1111-1111-1111-111111111111",
                   "capacityId":  "22222222-2222-2222-2222-222222222222",
                   "region": "westus2"}),
    ("demo_fabric_lakehouse", "fabric://ngfabric/lh_silver",
     "lh_silver", {"description": "Silver lakehouse - cleansed and conformed.",
                   "workspaceId": "11111111-1111-1111-1111-111111111111",
                   "capacityId":  "22222222-2222-2222-2222-222222222222",
                   "region": "westus2"}),
    ("demo_fabric_warehouse", "fabric://ngfabric/wh_gold",
     "wh_gold",   {"description": "Gold warehouse - business-ready marts.",
                   "workspaceId": "11111111-1111-1111-1111-111111111111",
                   "sku": "F64"}),
    ("powerbi_dataset",       "powerbi://ngfabric/semantic/sales_pipeline",
     "sales_pipeline", {"description": "Power BI semantic model serving the Sales Pipeline report."}),
]

# (qn, name, [(typeName,qn) inputs], [(typeName,qn) outputs])
PROCESSES = [
    ("fabric://process/ingest_customers", "ingest_customers",
     [("DataSet", "mssql://contoso.sql/dbo/Customers")],
     [("demo_fabric_lakehouse", "fabric://ngfabric/lh_bronze")]),
    ("fabric://process/ingest_orders", "ingest_orders",
     [("DataSet", "mssql://contoso.sql/dbo/Orders")],
     [("demo_fabric_lakehouse", "fabric://ngfabric/lh_bronze")]),
    ("fabric://process/curate_silver", "curate_silver",
     [("demo_fabric_lakehouse", "fabric://ngfabric/lh_bronze")],
     [("demo_fabric_lakehouse", "fabric://ngfabric/lh_silver")]),
    ("fabric://process/load_gold", "load_gold",
     [("demo_fabric_lakehouse", "fabric://ngfabric/lh_silver")],
     [("demo_fabric_warehouse", "fabric://ngfabric/wh_gold")]),
    ("fabric://process/refresh_sales_pipeline", "refresh_sales_pipeline",
     [("demo_fabric_warehouse", "fabric://ngfabric/wh_gold")],
     [("powerbi_dataset",       "powerbi://ngfabric/semantic/sales_pipeline")]),
]

def upsert_entity(type_name, qn, name, extra):
    body = {"entity": {"typeName": type_name,
                       "attributes": {"qualifiedName": qn, "name": name, **extra}}}
    r = S.post(f"{ATLAS}/entity", headers=H(), json=body, timeout=60)
    tag = "+" if r.ok else "!"
    print(f"  {tag} {type_name}: {name}  -> {r.status_code} {r.text[:200] if not r.ok else ''}")

def ref(type_name, qn):
    return {"typeName": type_name, "uniqueAttributes": {"qualifiedName": qn}}

def upsert_process(qn, name, inputs, outputs):
    body = {"entity": {"typeName": "Process",
                       "attributes": {"qualifiedName": qn, "name": name,
                                      "inputs":  [ref(t,q) for t,q in inputs],
                                      "outputs": [ref(t,q) for t,q in outputs]}}}
    r = S.post(f"{ATLAS}/entity", headers=H(), json=body, timeout=60)
    tag = "+" if r.ok else "!"
    print(f"  {tag} process: {name}  -> {r.status_code} {r.text[:200] if not r.ok else ''}")

def main():
    print(f"Atlas: {ATLAS}\n")
    print("Entities (data estate):")
    for tn, qn, nm, ex in ENTITIES:
        upsert_entity(tn, qn, nm, ex)
    print("\nLineage processes:")
    for qn, nm, ins, outs in PROCESSES:
        upsert_process(qn, nm, ins, outs)
    print("\nView lineage in classic Data Map:")
    print(f"  https://web.purview.azure.com/resource/{ACCOUNT}/main/catalog/search")
    print("Open any entity above and click the Lineage tab.")

if __name__ == "__main__":
    main()
