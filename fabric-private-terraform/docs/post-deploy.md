# Post-deploy steps

`terraform apply` only handles the Azure side. You must complete a small set of
**Fabric admin** actions in the portal before the private endpoint can serve
real traffic, and to wire up the F2 capacity to a workspace.

## 1. Enable tenant-level private link (one-time)

1. Sign in to https://app.fabric.microsoft.com as a Fabric admin.
2. **Settings → Admin portal → Tenant settings**.
3. Locate **Azure Private Link** and set it to **Enabled**.
4. Wait ~15 minutes for the tenant FQDN provisioning to finish.

Until this is on, the private endpoint will sit in `Pending` and DNS will return
no A records. After enabling, the PE auto-promotes to `Approved`.

## 2. Assign the F2 capacity to a workspace

```pwsh
# Workspace assignment via the Fabric REST API
$cap = terraform output -raw fabric_capacity_id     # /subscriptions/.../Microsoft.Fabric/capacities/fabpl...
$capacityName = terraform output -raw fabric_capacity_name

# 1. Find your workspace
az rest --method GET --uri "https://api.fabric.microsoft.com/v1/workspaces" `
  --resource "https://api.fabric.microsoft.com"

# 2. Assign capacity
$wsId = '<workspace-id>'
$body = @{ capacityId = $capacityName } | ConvertTo-Json
az rest --method POST `
  --uri "https://api.fabric.microsoft.com/v1/workspaces/$wsId/assignToCapacity" `
  --resource "https://api.fabric.microsoft.com" `
  --body $body
```

Or assign in the portal: **Workspace settings → License info → Capacity**.

## 3. (Optional) Block public internet access

Once you've verified private-only access works end-to-end:

1. Fabric admin portal → **Tenant settings → Advanced networking**.
2. Enable **Block Public Internet Access**.
3. Wait ~15 minutes.

This locks Fabric to private endpoints only — Power BI Desktop, browsers, and
gateways outside the VNet/on-prem network become unable to reach the tenant.

## 4. (Optional) Workspace-level private link

For per-workspace isolation (instead of, or in addition to, tenant-level):
- Workspace settings → **Network security** → **Workspace-level private link**.
- Provide the resource ID emitted by `terraform output private_link_service_id`
  (or a separate `Microsoft.PowerBI/privateLinkServicesForPowerBI` resource per
  workspace if you want granularity).

## 5. (Optional) Outbound access protection + managed PEs

To allow Fabric notebooks/Spark to reach private data sources:

1. Workspace settings → **Network security** → enable **outbound access
   protection**.
2. Add **managed private endpoints** to your private SQL MI / Storage / Cosmos.
3. Approve the pending PE on each target resource (Azure portal → Private
   endpoint connections → Approve).

This stack does not provision target data sources — extend `main.tf` with a
spoke VNet, the data source of your choice (e.g., `azurerm_mssql_server` with
`public_network_access_enabled = false`), and a managed PE definition through
the Fabric workspace API (not yet available in azurerm/azapi).
