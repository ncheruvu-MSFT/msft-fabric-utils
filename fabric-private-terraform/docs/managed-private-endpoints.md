# Managed Private Endpoints (MPEs) for Microsoft Fabric

> Companion to the tenant-level Private Link sample in this repo. Read this
> after you've deployed the hub and enabled tenant Azure Private Link, when
> you need Fabric workloads (Spark notebooks, lakehouses, eventstreams, Spark
> job definitions) to reach **your own private Azure data sources**.

References:
- [Overview of managed private endpoints for Microsoft Fabric](https://learn.microsoft.com/fabric/security/security-managed-private-endpoints-overview)
- [REST API: Create workspace managed private endpoint](https://learn.microsoft.com/rest/api/fabric/core/managed-private-endpoints/create-workspace-managed-private-endpoint)

---

## How tenant Private Link and MPEs differ

| Direction | Sample artifact | What it does |
|---|---|---|
| **Inbound to Fabric** (your network → Fabric) | `azurerm_private_endpoint` + `Microsoft.PowerBI/privateLinkServicesForPowerBI` | Creates a private IP in **your** VNet for the Fabric tenant FQDNs. Used by users on-prem / in spokes hitting `app.powerbi.com`, OneLake, the Warehouse SQL endpoint, etc. |
| **Outbound from Fabric** (Fabric → your data) | **Managed Private Endpoint (this doc)** | Created **inside the Fabric workspace**. Lets a Spark notebook / lakehouse / eventstream reach a private-only Storage / SQL DB / Cosmos / Key Vault that has `publicNetworkAccess=Disabled`. |

You almost always need both for a fully private deployment.

## What you can target

| Target | `targetSubresourceType` |
|---|---|
| Azure SQL Database / Synapse | `sqlServer` |
| ADLS Gen2 storage | `dfs` |
| Blob storage | `blob` |
| Cosmos DB (SQL API) | `Sql` |
| Key Vault | `vault` |
| Event Hubs / Service Bus | `namespace` |

FQDN-based MPEs (e.g. a third-party SaaS behind Private Link Service) are also supported but only via the REST API by passing `targetFQDNs`.

## Prerequisites

1. Fabric workspace assigned to a paid F SKU (or Trial) — handled by this Terraform sample.
2. **Workspace admin** role for the caller (not just capacity admin).
3. Target resource has Private Link enabled and `publicNetworkAccess=Disabled`.
4. The caller must have **owner / network contributor** equivalent on the target so they can approve the connection on the target side later.

## Workflow

```
Fabric admin / workspace admin                Target resource owner
─────────────────────────────                 ──────────────────────
1. POST /workspaces/{id}/managedPrivateEndpoints
   ↓
   provisioningState = Provisioning
   connectionState   = Pending     ─────▶  2. Sees connection in:
                                              <target>.Networking →
                                              "Private endpoint connections"
                                           3. Clicks Approve
   ↓                                           (or via az/PowerShell)
4. GET /managedPrivateEndpoints/{id}   ◀──
   provisioningState = Succeeded
   connectionState   = Approved
   ↓
5. Use the private name from a Spark
   notebook / lakehouse shortcut /
   eventstream connector.
```

The REST contract:

```http
POST https://api.fabric.microsoft.com/v1/workspaces/{workspaceId}/managedPrivateEndpoints
Content-Type: application/json
Authorization: Bearer <Fabric access token>

{
  "name": "mpe-sql-shared",
  "targetPrivateLinkResourceId": "/subscriptions/.../Microsoft.Sql/servers/sqlsrv01",
  "targetSubresourceType": "sqlServer",
  "requestMessage": "prod-analytics workspace needs sqlsrv01"
}
```

## Helper script

This repo ships [`scripts/fabric/Create-FabricMpe.ps1`](../scripts/fabric/Create-FabricMpe.ps1) and [`scripts/fabric/Get-FabricMpe.ps1`](../scripts/fabric/Get-FabricMpe.ps1).

```powershell
Connect-AzAccount -Tenant $tenantId

./scripts/fabric/Create-FabricMpe.ps1 `
  -WorkspaceId 47482db6-4583-4672-86dd-999d0f8f4d7a `
  -Name        'mpe-sql-shared' `
  -TargetResourceId '/subscriptions/sub/resourceGroups/data/providers/Microsoft.Sql/servers/sqlsrv01' `
  -TargetSubresource sqlServer `
  -RequestMessage   'prod-analytics needs sqlsrv01' `
  -WaitForActivated
```

The script POSTs the create request, prints the MPE ID, and (with `-WaitForActivated`) polls until provisioning succeeds AND the target owner approves. Approval still happens **out-of-band** in the Azure portal on the target resource.

## Approving on the target

After the POST succeeds, an entry shows up under:

> Target resource → **Networking** → **Private endpoint connections**

with status **Pending** and a description that includes your `requestMessage`. The owner approves it there; the MPE flips to `Approved` within ~1 minute.

CLI alternative for approval:

```powershell
# Example: SQL server
az network private-endpoint-connection approve `
  --resource-group   data `
  --name             $connectionName `
  --resource-name    sqlsrv01 `
  --type             Microsoft.Sql/servers `
  --description      'Approved for fabric workspace'
```

## Things to know

- **Owner approval on target is mandatory.** No portal click = MPE stays Pending forever.
- **15-minute cool-down** between deleting an MPE and recreating one with the same name on the same target.
- **One MPE per target sub-resource per workspace.** A workspace pointing at the same SQL server twice for the same sub-resource is rejected.
- **Workspace identity vs MPE.** The MPE itself is the network path; the *credential* used by your notebook still needs to be a valid identity that the data source authorizes (managed identity, service principal, OneLake shortcut credentials, etc.).
- **Outbound access protection.** If you turn on workspace-level outbound access protection, MPEs become the only outbound channel — every external host the workspace touches must be reachable via an MPE.
- **MPE counts.** Default is 200 MPEs per workspace, 200 across the tenant — request a service quota increase via support if you need more.

## Putting it together with this Terraform sample

1. `terraform apply` (this repo) — creates capacity, network, DNS resolver, firewall, simulated on-prem.
2. Manually enable tenant Azure Private Link in the Fabric admin portal.
3. Create a private-only target in Azure (e.g. an Azure SQL DB with `public_network_access_enabled = false` — see [`docs/post-deploy.md`](./post-deploy.md)).
4. Assign your Fabric workspace to the capacity (`assignToCapacity` REST API).
5. Run `Create-FabricMpe.ps1` from the lab DC (or your laptop) pointing at the workspace + target.
6. Approve the connection on the target resource.
7. From a Fabric notebook in that workspace, connect to the target by its private FQDN. Confirm with `nslookup` inside the notebook (`%pip install nslookup`) or by reading a row from a private-only table.
