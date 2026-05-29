"""Register data sources in Purview, kick off scans, link Fabric workspace.

Sources registered:
  - Azure SQL retail DB
  - Azure Postgres HR DB
  - Cosmos DB telemetry
  - Azure Databricks workspace
  - Fabric (tenant-level, already auto-registered if Purview hub enabled)
"""
from __future__ import annotations
import os, sys, json, requests, pathlib, time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Shared retry session — Purview UC plane occasionally drops SSL handshakes
# under burst, returning SSLEOFError. Retrying handles transient TLS resets.
_S = requests.Session()
_S.mount("https://", HTTPAdapter(max_retries=Retry(
    total=6, backoff_factor=1.5,
    status_forcelist=[429,500,502,503,504],
    allowed_methods=["GET","PUT","POST","DELETE"])))
requests = _S  # shadow module name with session

ROOT = pathlib.Path(__file__).resolve().parents[1]
for env in (ROOT/".sources.env", ROOT/".env"):
    if env.exists():
        for ln in env.read_text().splitlines():
            if "=" in ln and not ln.startswith("#"):
                k,v=ln.split("=",1); os.environ.setdefault(k,v)

PURVIEW=os.environ.get("PURVIEW_ACCOUNT","ngpurview")
SCAN=f"https://{PURVIEW}.purview.azure.com/scan"
SUB=os.environ.get("AZURE_SUBSCRIPTION","31613fe0-1e9b-4a97-b771-dc48fbaa0fbb")
RG=os.environ.get("SOURCES_RG","ng-fabric-sources-cc")

def tok():
    from azure.identity import DefaultAzureCredential
    return DefaultAzureCredential().get_token("https://purview.azure.net/.default").token
def H(): return {"Authorization":f"Bearer {tok()}","Content-Type":"application/json"}

def put_ds(name, kind, props):
    body={"kind":kind,"name":name,"properties":props}
    r=requests.put(f"{SCAN}/datasources/{name}?api-version=2023-09-01",headers=H(),json=body)
    print(f"  DS {name}: {r.status_code} {r.text[:200] if not r.ok else ''}")

def main():
    sql=os.environ.get("SOURCE_SQL_FQDN",""); sqldb=os.environ.get("SOURCE_SQL_DB","retail")
    pg=os.environ.get("SOURCE_PG_FQDN","");   pgdb=os.environ.get("SOURCE_PG_DB","hr")
    cosmos=os.environ.get("SOURCE_COSMOS_ACCT","")
    dbx=os.environ.get("SOURCE_DBX_ID","")
    loc=os.environ.get("SOURCES_LOCATION","canadacentral")
    coll={"referenceName":PURVIEW,"type":"CollectionReference"}

    if sql:
        put_ds("ds_sql_retail","AzureSqlDatabase",{
            "serverEndpoint": sql,"subscriptionId":SUB,"resourceGroup":RG,
            "resourceName": sql.split('.')[0], "location":loc, "collection":coll})
    if pg:
        put_ds("ds_pg_hr","AzurePostgreSql",{
            "serverEndpoint": pg, "subscriptionId":SUB,"resourceGroup":RG,
            "resourceName": pg.split('.')[0], "location":loc, "collection":coll})
    if cosmos:
        put_ds("ds_cosmos_telemetry","AzureCosmosDb",{
            "accountUri": f"https://{cosmos}.documents.azure.com:443/",
            "subscriptionId":SUB,"resourceGroup":RG,"resourceName":cosmos,
            "location":loc, "collection":coll})
    # Azure Databricks Unity Catalog source -> kind 'Databricks' (requires metastoreId)
    dbx_metastore = os.environ.get("SOURCE_DBX_METASTORE_ID","")
    dbx_url       = os.environ.get("SOURCE_DBX_URL","")
    if dbx and dbx_metastore:
        put_ds("ds_databricks","Databricks",{
            "metastoreId":   dbx_metastore,
            "endpoint":      dbx_url,
            "subscriptionId":SUB,"resourceGroup":RG,
            "resourceName":  dbx.split('/')[-1],
            "location":loc, "collection":coll})
    elif dbx:
        print("  SKIP ds_databricks: set SOURCE_DBX_METASTORE_ID (Unity Catalog metastore GUID) in .sources.env")

    # Fabric tenant
    put_ds("ds_fabric","Fabric",{"tenant":os.environ.get("AZURE_TENANT","62c0cb46-1fcc-4c79-ba1b-d7d9fdfbaa68"),
        "collection":coll})

    print("\nRunning scans (Managed-Identity auth — make sure Purview MI has SQL/PG db_datareader):")
    for ds in ["ds_sql_retail","ds_pg_hr","ds_cosmos_telemetry","ds_databricks"]:
        # Note: Azure Database for PostgreSQL only supports Basic-auth scans
        # (no MSI). Skip until a Key Vault credential is wired in.
        if ds == "ds_pg_hr":
            print(f"  SKIP scan {ds}: Azure Postgres requires Basic auth via Key Vault credential (no MSI support).")
            continue
        if ds == "ds_databricks":
            print(f"  SKIP scan {ds}: Azure Databricks UC scan requires PAT/SP credential via Key Vault (no MSI support).")
            continue
        kindmap={"ds_sql_retail":"AzureSqlDatabaseMsi",
                 "ds_cosmos_telemetry":"AzureCosmosDbMsi","ds_databricks":"DatabricksMsi"}
        rulesetmap={"ds_sql_retail":"AzureSqlDatabase",
                    "ds_cosmos_telemetry":"AzureCosmosDb","ds_databricks":"Databricks"}
        props = {"scanRulesetName":rulesetmap[ds],"scanRulesetType":"System"}
        if ds == "ds_sql_retail":
            props.update({"serverEndpoint": sql, "databaseName": sqldb})
        elif ds == "ds_databricks":
            if not (dbx and dbx_metastore):
                print(f"  SKIP scan {ds}: no metastore id"); continue
        sb={"kind":kindmap[ds],"properties":props}
        r=requests.put(f"{SCAN}/datasources/{ds}/scans/scan-once?api-version=2023-09-01",headers=H(),json=sb)
        print(f"  scan {ds}: {r.status_code} {r.text[:300] if not r.ok else ''}")
        if r.ok:
            # Trigger an immediate run (no runId in path).
            r2=requests.post(f"{SCAN}/datasources/{ds}/scans/scan-once/run?api-version=2023-09-01",headers=H(),json={})
            print(f"    run trigger: {r2.status_code} {r2.text[:200] if not r2.ok else ''}")

if __name__=="__main__": main()
