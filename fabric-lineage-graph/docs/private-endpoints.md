# Private endpoints — running the cloud-tier validation in a locked-down VNet

The cloud-tier infra has a `enablePrivateEndpoints=true` switch (see
[`samples/cloud/infra/main.bicep`](../samples/cloud/infra/main.bicep)). When
enabled, the SQL Server, Postgres Flex, and Cosmos account all set
`publicNetworkAccess=Disabled` and a private endpoint is created in the
caller's VNet/subnet.

## What breaks the moment public access is off

| Symptom | Cause | Fix |
|---|---|---|
| `pyodbc.OperationalError: ... Could not open a connection to SQL Server` | Caller machine has no route to the PE NIC | Run the harvester from inside the VNet (see below) |
| `azure.cosmos.exceptions.CosmosHttpResponseError 403 Forbidden` | Public IP path blocked; PE in place but DNS still resolves to the public FQDN | Wire up the private DNS zone `privatelink.documents.azure.com` |
| `psycopg.OperationalError ... no route to host` | Same DNS / firewall situation as SQL | Private DNS zone `privatelink.postgres.database.azure.com` |
| Deployment fails: `Cannot enable AAD-only auth ...` | Bicep parameter order — the AAD admin block must be set in the SAME PUT as the publicNetworkAccess flip | The provided bicep does this in one module, so this only bites on manual portal flips |

## Private DNS zones you must link to the VNet

| Service | Zone |
|---|---|
| Azure SQL  | `privatelink.database.windows.net` |
| Postgres   | `privatelink.postgres.database.azure.com` |
| Cosmos SQL | `privatelink.documents.azure.com` |

`az network private-dns zone create` + `az network private-dns link vnet create` per zone. The AVM modules in the bicep DON'T create the zones (intentional — most enterprises centralise zones in a hub VNet).

## Where to run the harvesters when public is off

In order of operational cost, lowest first:

1. **Fabric notebook in the same VNet** — Fabric workspace bound to a managed VNet, gateway peered to the data VNet. Run `01_harvest_all.ipynb`; the live harvesters work unchanged because pyodbc / psycopg / azure-cosmos all reach the PEs via the workspace network. **Recommended.**
2. **Self-Hosted Integration Runtime** — Windows VM in the data VNet, `tests/run_cloud_validation.py` scheduled there. Useful if you also want SHIR for ADF pipelines.
3. **ACI in the PE subnet** — short-lived, build a container with the harvester deps + ODBC driver, run on schedule. Cheaper than #2 but more moving parts.
4. **Azure VPN / ExpressRoute** — only if dev laptops need direct access. Almost never the right answer for a service-account-driven harvester.

## Auth caveats with private endpoints

`AzureCliCredential` / `DefaultAzureCredential` are control-plane only — the
private endpoint affects the data plane. So as long as the harvester host has
ANY route to login.microsoftonline.com (it does, that's a public endpoint) the
AAD token acquisition still works. Only the data-plane connect needs the
private endpoint route.

This matches my memory note: SPN tokens from a local machine often 403 on
data plane (tenant-wide Conditional Access on SP principals). Inside a Fabric
notebook the workload identity sidesteps that — `DefaultAzureCredential` picks
the runtime token, not an SP, and the call succeeds.

## Validating PE-mode in 60 seconds

```powershell
# From inside the VNet host:
nslookup sql-fbrlin-dev-cac-001.database.windows.net
# Must return a 10.x.x.x (private) IP, NOT a 20.x.x.x (public Azure) IP.

python -m tests.run_cloud_validation --only sql
# Should match the public-endpoint run output exactly. If you get
# DNS errors, the private DNS zone link to your VNet is missing.
```

## What we explicitly do NOT cover here

- Cross-tenant PE (Privatelink Service / approval workflow) — out of scope for the demo.
- Customer-managed key on SQL / Cosmos — orthogonal; turn on per-service after PE is working.
- Synapse Managed VNet — uses Managed Private Endpoints (no end-user subnet). Different bicep — add a separate module when the user actually needs Synapse.
