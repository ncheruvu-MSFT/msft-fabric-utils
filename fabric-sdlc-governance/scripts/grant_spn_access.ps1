<#
.SYNOPSIS
One-time grants for the Purview-SIT-Migration app (Entra app used by ADO WIF service connection)
to operate Fabric capacity, deploy workspaces, and publish to Purview.

USAGE
  pwsh ./grant_spn_access.ps1
#>
$spnAppId = "47a48c18-47f4-4f90-a5e7-f5add3cb2ee3"
$spnObjId = (az ad sp show --id $spnAppId --query id -o tsv)
$sub      = "31613fe0-1e9b-4a97-b771-dc48fbaa0fbb"
$rg       = "ng-fabric-capacity"
$capacity = "ngfabricf2westus3001"

Write-Host "SPN object id: $spnObjId"

# --- Azure RBAC ---
Write-Host "`n1. Granting Contributor on Fabric capacity (start/stop) ..."
az role assignment create `
  --assignee-object-id $spnObjId `
  --assignee-principal-type ServicePrincipal `
  --role "Contributor" `
  --scope "/subscriptions/$sub/resourceGroups/$rg/providers/Microsoft.Fabric/capacities/$capacity"

# --- Purview RBAC (Data Source Admin + Data Curator on root collection) ---
Write-Host "`n2. Granting Purview Data Source Admin + Data Curator (root collection) ..."
$purview = "ngpurview"
# Purview RBAC is set via /policystore/metadataPolicies — the simplest pattern is portal,
# but az cli supports it via the data-plane:
$pvToken = (az account get-access-token --resource https://purview.azure.net --query accessToken -o tsv)
$pol = Invoke-RestMethod -Uri "https://$purview.purview.azure.com/policystore/metadataRoles?api-version=2021-07-01-preview" -Headers @{Authorization="Bearer $pvToken"}
Write-Host "  Purview roles available: $($pol.values.Count)"
Write-Host "  Apply 'Data Source Administrator' and 'Data Curator' to SPN $spnAppId in Purview portal →"
Write-Host "  https://web.purview.azure.com/resource/$purview/main/collections → Role assignments"

# --- Fabric tenant admin (already done earlier via security group sg-fabric-purview-admin-ui) ---
Write-Host "`n3. Ensure SPN is a member of group 'sg-fabric-purview-admin-ui' (already enabled in Fabric admin)"
$groupId = "d7de487f-a25f-46b4-9709-4774785c9f06"
az ad group member add --group $groupId --member-id $spnObjId 2>$null
$inGroup = (az ad group member list --group $groupId --query "[?id=='$spnObjId'] | length(@)" -o tsv)
Write-Host "  In group: $($inGroup -eq '1')"

# --- Fabric workspace admin (per env) ---
Write-Host "`n4. Add SPN as Workspace Admin to fabric-de-dev, fabric-de-test, fabric-de-prod"
Write-Host "   Run in portal: app.fabric.microsoft.com → workspace → Manage access → Add admin → search '$spnAppId'"
Write-Host "   (Programmatic: POST /v1/workspaces/{wsId}/roleAssignments — needs Fabric Admin token, easier in portal once)"

Write-Host "`nDone. Re-run the DE pipeline after these steps complete."
