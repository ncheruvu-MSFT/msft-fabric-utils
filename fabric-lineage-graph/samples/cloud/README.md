# Cloud-tier validation (public endpoints first)

Real lineage harvest end-to-end across **Azure SQL, Postgres Flex, Cosmos DB**
(and optionally **Oracle** via BYO connection, **Synapse Serverless** via the
same MSSQL harvester pointed at the workspace endpoint).

> **MCAPS compliance** — Both SQL and Postgres are provisioned with
> **Entra-only authentication** (no SQL logins / no Postgres passwords). The
> seeder + harvesters use `DefaultAzureCredential` for everything.

## Topology

```
                +-------------------+
                |   Azure SQL       |   crm.customers + crm.orders
                |   (Entra-only)    |   --> silver.customer_360
                +---------+---------+   --> gold.customer_revenue_mart
                          |
   declared edge -------- |  ----- adf:enrich_sessions_with_customer
                          v
                +-------------------+
                |   Cosmos DB       |   web_sessions, iot_telemetry
                |   (SQL API)       |
                +---------+---------+
                          |
   declared edge -------- |  ----- spark:iot_revenue_join
                          v  (back into gold.customer_revenue_mart)

                +-------------------+
                |  Postgres Flex    |   hr.employees + hr.compensation
                |  (Entra-only)     |   --> hr.employee_compensation_v
                +---------+---------+   --> hr.payroll_summary_v
                          ^
   declared edge -------- |  ----- synapse:ship_to_hr_attribution
                          |
                +-------------------+
                |  Oracle (BYO)     |   scm.suppliers + scm.shipments
                +-------------------+   --> scm.supplier_performance_v
                                        --> scm.supplier_scorecard_v
```

In-DB views drive the per-system lineage (parsed via sqlglot from each
catalog). Cross-system edges are **declared** in
[`cross_system_edges.json`](cross_system_edges.json) — that's authentic, because
no single catalog can see lineage that lives in an ETL pipeline.

## Prerequisites (one-time)

```powershell
# Azure CLI signed in to the right tenant + subscription
az login --tenant <tenant>
az account set --subscription <sub-id>

# Python deps (adds pyodbc, psycopg, azure-cosmos, oracledb)
pip install -r requirements.txt

# Install Microsoft ODBC Driver 18 for SQL Server (Windows):
# https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server
```

## Deploy (public endpoints)

```powershell
$env:ADMIN_LOGIN     = "you@contoso.onmicrosoft.com"   # YOUR Entra UPN
$env:ADMIN_OBJECT_ID = "00000000-0000-0000-0000-000000000000"

cd samples/cloud/infra
./deploy.ps1 -ResourceGroup rg-fbrlin-dev-cac -Location canadacentral
```

The deploy script writes `.env.cloud` at the repo root with the FQDNs /
endpoints / database names produced by the bicep — the seeders and harvesters
read it automatically.

## Seed

```powershell
cd ../../..                        # back to fabric-lineage-graph/
python samples/cloud/seed/run_all.py
# Or a subset:
python samples/cloud/seed/run_all.py --only sql,pg,cosmos
```

If you have an Oracle instance, set `ORACLE_DSN`, `ORACLE_USER`, `ORACLE_PWD`
in `.env.cloud` first and the seeder + harvester will pick it up.

## Run cloud-tier validation

```powershell
python -m tests.run_cloud_validation
```

Expected output:

```
  sql        ->    2 edges       # silver.customer_360 view (2 source tables)
  pg         ->    3 edges       # employee_compensation_v + payroll_summary_v
  cosmos     ->    2 edges       # web_sessions + iot_telemetry catalog anchors
  oracle     ->    3 edges       # supplier_performance_v + supplier_scorecard_v
  declared   ->    3 edges       # 3 cross-system flows from cross_system_edges.json

Graph: ~15 nodes, ~13 edges
Violations:        0
PASS — cloud-tier lineage + label propagation validated.
```

Artifacts written to `out/cloud/`:
- `edges.json`        — full harvested edge list
- `labels.json`       — propagated MIP label per node
- `violations.json`   — DLP gate findings (should be empty on clean run)
- `graph.html`        — interactive PyVis graph — open in a browser

## Private endpoints

```powershell
# Re-run deploy with PE enabled, pointing at your existing VNet/subnet:
az deployment group create `
  -g rg-fbrlin-dev-cac `
  --template-file samples/cloud/infra/main.bicep `
  --parameters samples/cloud/infra/main.bicepparam `
  --parameters enablePrivateEndpoints=true `
               vnetId=/subscriptions/.../virtualNetworks/vnet-fab `
               peSubnetName=snet-pe
```

See [`docs/private-endpoints.md`](../../docs/private-endpoints.md) for what
breaks (DNS, harvester host reachability) and how to run the harvesters from
inside the VNet (Fabric notebook, Self-Hosted IR, ACI in the subnet).

## Teardown

```powershell
./samples/cloud/infra/teardown.ps1 -ResourceGroup rg-fbrlin-dev-cac
```

## Adding Synapse

Synapse Serverless SQL pool exposes views via the same `sys.sql_modules`
catalog. Point [`MssqlLiveHarvester`](../../harvesters/mssql_live.py) at the
`<workspace>-ondemand.sql.azuresynapse.net` FQDN with a small database name
(usually `master`) — no harvester code change needed. Add a second instance
to the runner in `tests/run_cloud_validation.py` using a fresh env var pair.
