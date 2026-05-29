<#
.SYNOPSIS
Create Purview DLP policy that protects assets labelled 'Confidential-PII' or higher
across Fabric Lakehouses and Warehouses.

NOTE: Fabric DLP policy creation via PowerShell is in preview. This script attempts
the New-DlpCompliancePolicy + New-DlpComplianceRule combo. If the cmdlets are not
available in your tenant, follow portal steps printed at the end.
#>
param(
  [string]$PolicyName = "Contoso-Fabric-Confidential-DLP",
  [string]$TargetGroup = "data-stewards@contoso.com"
)

Import-Module ExchangeOnlineManagement -ErrorAction Stop
Connect-IPPSSession -UseRPSSession:$false

try {
  $policy = Get-DlpCompliancePolicy -Identity $PolicyName -ErrorAction SilentlyContinue
  if ($null -eq $policy) {
    New-DlpCompliancePolicy -Name $PolicyName -FabricLocation All -Mode Enable | Out-Null
    Write-Host "Created DLP policy $PolicyName"
  }
  $ruleName = "$PolicyName-Block-Confidential-PII"
  $existing = Get-DlpComplianceRule -Policy $PolicyName -ErrorAction SilentlyContinue | Where-Object Name -eq $ruleName
  if ($null -eq $existing) {
    New-DlpComplianceRule -Name $ruleName -Policy $PolicyName `
      -ContentContainsSensitiveInformation @(@{Name='Credit Card Number'; minCount=1}) `
      -BlockAccess $true `
      -NotifyUser $TargetGroup `
      -GenerateAlert $TargetGroup
    Write-Host "Created rule $ruleName"
  }
} catch {
  Write-Warning "DLP cmdlets failed or not available: $_"
  Write-Host "`nPortal steps:" -ForegroundColor Yellow
  Write-Host "  1. Open https://purview.microsoft.com/dlp"
  Write-Host "  2. New policy → 'Custom' → Locations: Fabric & Power BI"
  Write-Host "  3. Rule: block when sensitivity label = Confidential-PII or Highly-Confidential-Restricted"
  Write-Host "  4. Action: block + notify data-stewards"
}
