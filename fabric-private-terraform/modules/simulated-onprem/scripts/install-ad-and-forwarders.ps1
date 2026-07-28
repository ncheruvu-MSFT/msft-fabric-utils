<#
.SYNOPSIS
  Bootstraps a Windows Server VM as a self-contained "simulated on-prem" lab DC:
    - Promotes to a new AD DS forest
    - Installs AD-integrated DNS
    - Configures conditional forwarders for Microsoft Fabric private DNS zones,
      pointing them to the Azure Private DNS Resolver inbound endpoint IP

.DESCRIPTION
  Designed to run from an Azure Custom Script Extension. After AD DS promotion
  the VM auto-reboots; a one-shot scheduled task created by Phase 1 finishes
  the DNS forwarder configuration after Phase 2 boot.

.PARAMETER DomainName
  FQDN of the new forest (e.g. lab.contoso.local).

.PARAMETER NetBiosName
  NetBIOS name (e.g. LAB).

.PARAMETER SafeModePassword
  Plain text DSRM/safe-mode admin password.

.PARAMETER ResolverIp
  Private DNS Resolver inbound endpoint IP in the hub VNet.

.PARAMETER FabricTenantId
  Fabric/Entra tenant ID — embedded in a test script saved to C:\Tools.
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory)] [string] $DomainName,
  [Parameter(Mandatory)] [string] $NetBiosName,
  [Parameter(Mandatory)] [string] $SafeModePassword,
  [Parameter(Mandatory)] [string] $ResolverIp,
  [Parameter(Mandatory)] [string] $FabricTenantId
)

$ErrorActionPreference = 'Stop'
Start-Transcript -Path 'C:\bootstrap\install-ad.log' -Append -Force

New-Item -ItemType Directory -Path 'C:\bootstrap' -Force | Out-Null
New-Item -ItemType Directory -Path 'C:\Tools'     -Force | Out-Null

# ----------------------------------------------------------------------------
# Phase 2 script: runs once at next boot, configures Fabric DNS forwarders
# and self-deletes its scheduled task.
# ----------------------------------------------------------------------------
$phase2 = @'
param([string]$ResolverIp)

$ErrorActionPreference = 'Continue'
Start-Transcript -Path 'C:\bootstrap\phase2.log' -Append -Force

$zones = @(
  'privatelink.analysis.windows.net',
  'privatelink.pbidedicated.windows.net',
  'privatelink.prod.powerquery.microsoft.com',
  'analysis.windows.net',
  'pbidedicated.windows.net',
  'powerquery.microsoft.com',
  'fabric.microsoft.com',
  'powerbi.com'
)

# Wait for the DNS service to be ready post-promo
$ready = $false
for ($i = 0; $i -lt 30 -and -not $ready; $i++) {
  try {
    Get-DnsServer -ErrorAction Stop | Out-Null
    $ready = $true
  } catch {
    Start-Sleep -Seconds 10
  }
}

foreach ($z in $zones) {
  $existing = Get-DnsServerZone -Name $z -ErrorAction SilentlyContinue
  if ($null -eq $existing) {
    Add-DnsServerConditionalForwarderZone `
      -Name $z `
      -MasterServers @($ResolverIp) `
      -ReplicationScope Forest `
      -ErrorAction Continue
    Write-Output "Added conditional forwarder for $z -> $ResolverIp"
  } else {
    Set-DnsServerConditionalForwarderZone `
      -Name $z `
      -MasterServers @($ResolverIp) `
      -ErrorAction Continue
    Write-Output "Updated conditional forwarder for $z -> $ResolverIp"
  }
}

# Self-delete
Unregister-ScheduledTask -TaskName 'ConfigureFabricForwarders' -Confirm:$false -ErrorAction SilentlyContinue
Stop-Transcript
'@

Set-Content -Path 'C:\bootstrap\phase2.ps1' -Value $phase2 -Encoding UTF8 -Force

# ----------------------------------------------------------------------------
# Test script saved for the demo operator (lives in C:\Tools, not auto-run).
# ----------------------------------------------------------------------------
$testScript = @"
# Run this on the lab DC after Phase 2 completes to verify private resolution.
`$tenantNoDash = '$FabricTenantId'.Replace('-', '')
`$names = @(
  'app.fabric.microsoft.com',
  'api.powerbi.com',
  "`$tenantNoDash-api.privatelink.analysis.windows.net",
  "`$tenantNoDash-onelake.privatelink.analysis.windows.net",
  "`$tenantNoDash-warehouse.privatelink.analysis.windows.net"
)
foreach (`$n in `$names) {
  Write-Host "==> `$n" -ForegroundColor Cyan
  Resolve-DnsName -Name `$n -Server 127.0.0.1 -ErrorAction Continue |
    Select-Object Name, Type, IPAddress, NameHost | Format-Table -AutoSize
}
"@

Set-Content -Path 'C:\Tools\Test-FabricResolution.ps1' -Value $testScript -Encoding UTF8 -Force

# ----------------------------------------------------------------------------
# Schedule Phase 2 to run once at next boot (after AD DS promo reboot).
# ----------------------------------------------------------------------------
$action  = New-ScheduledTaskAction -Execute 'powershell.exe' `
  -Argument "-ExecutionPolicy Bypass -NoProfile -File C:\bootstrap\phase2.ps1 -ResolverIp $ResolverIp"
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -RunLevel Highest

Register-ScheduledTask -TaskName 'ConfigureFabricForwarders' `
  -Action $action -Trigger $trigger -Principal $principal `
  -Description 'One-shot — configure Fabric private DNS forwarders after AD DS promotion.' `
  -Force | Out-Null

Write-Output 'Phase 2 scheduled task registered.'

# ----------------------------------------------------------------------------
# Install AD DS + DNS roles and promote to a new forest.
# ----------------------------------------------------------------------------
Install-WindowsFeature -Name AD-Domain-Services, DNS, RSAT-AD-Tools, RSAT-DNS-Server `
  -IncludeManagementTools

$securePwd = ConvertTo-SecureString $SafeModePassword -AsPlainText -Force

Install-ADDSForest `
  -DomainName $DomainName `
  -DomainNetbiosName $NetBiosName `
  -SafeModeAdministratorPassword $securePwd `
  -InstallDns `
  -CreateDnsDelegation:$false `
  -DatabasePath 'C:\Windows\NTDS' `
  -LogPath     'C:\Windows\NTDS' `
  -SysvolPath  'C:\Windows\SYSVOL' `
  -NoRebootOnCompletion:$true `
  -Force

Write-Output 'AD DS forest promotion complete; rebooting in 60s.'
Stop-Transcript

# Reboot now — Custom Script Extension reports success after exit, scheduled
# task picks up after the DC comes back online.
shutdown.exe /r /t 60 /c 'AD DS promotion complete — rebooting'
