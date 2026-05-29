<#
.SYNOPSIS
Create Microsoft Purview Information Protection (MIP) sensitivity labels
from contracts/labels/sensitivity-labels.yml and publish them in a label policy.

REQUIREMENTS
- ExchangeOnlineManagement module (for Connect-IPPSSession)
  Install-Module -Name ExchangeOnlineManagement -Force
- powershell-yaml module
  Install-Module -Name powershell-yaml -Force
- A Compliance Administrator (or Security Administrator) account in the tenant.

USAGE
  pwsh ./create_mip_labels.ps1 -Tenant '00000000-0000-0000-0000-000000000000'
#>
param(
  [Parameter(Mandatory=$true)][string]$Tenant,
  [string]$YamlPath = "contracts/labels/sensitivity-labels.yml",
  [string]$PolicyName = "Contoso-Fabric-AutoLabel",
  [string]$PolicyTargetGroup = "data-stewards@contoso.com"
)

Import-Module ExchangeOnlineManagement -ErrorAction Stop
Import-Module powershell-yaml             -ErrorAction Stop

Write-Host "Connecting to Security & Compliance for tenant $Tenant ..."
Connect-IPPSSession -UseRPSSession:$false

$cfg = (Get-Content $YamlPath -Raw) | ConvertFrom-Yaml
foreach ($l in $cfg.labels) {
  $name = $l.name
  $existing = Get-Label -Identity $name -ErrorAction SilentlyContinue
  if ($null -ne $existing) {
    Write-Host "  label '$name' already exists, updating tooltip + color"
    Set-Label -Identity $name -Tooltip $l.tooltip -DisplayName $name
  } else {
    Write-Host "  creating label '$name'"
    $params = @{ Name = $name; DisplayName = $name; Tooltip = $l.tooltip }
    if ($l.enforce_encryption) {
      $params.EncryptionEnabled = $true
      $params.EncryptionProtectionType = "Template"
      $params.EncryptionRightsDefinitions = "$($l.rights_users -join ';'):$($l.rights_permissions -join ',')"
    }
    if ($l.enforce_watermark) {
      $params.ApplyContentMarkingHeaderEnabled = $true
      $params.ApplyContentMarkingHeaderText = $l.content_marking_header
      $params.ApplyWaterMarkingEnabled = $true
      $params.ApplyWaterMarkingText = $l.content_marking_header
    }
    New-Label @params
  }
}

# Publish a label policy so labels show up in Fabric/Office clients
$labels = ($cfg.labels | ForEach-Object { $_.name }) -join ","
$existingPolicy = Get-LabelPolicy -Identity $PolicyName -ErrorAction SilentlyContinue
if ($null -eq $existingPolicy) {
  Write-Host "Publishing label policy '$PolicyName' to $PolicyTargetGroup"
  New-LabelPolicy -Name $PolicyName -Labels $labels -ExchangeLocation $PolicyTargetGroup
} else {
  Write-Host "Updating label policy '$PolicyName'"
  Set-LabelPolicy -Identity $PolicyName -AddLabels $labels
}

Write-Host "Done."
