<#
.SYNOPSIS
  Tear down the cloud sample resource group.
#>
param(
  [Parameter(Mandatory)] [string] $ResourceGroup,
  [switch] $Yes
)

if (-not $Yes) {
  $confirm = Read-Host "Delete resource group '$ResourceGroup' and ALL resources in it? (type DELETE)"
  if ($confirm -ne 'DELETE') { Write-Host "Aborted."; return }
}

az group delete --name $ResourceGroup --yes --no-wait
Write-Host "Delete submitted (async). Track with: az group show -n $ResourceGroup" -ForegroundColor Yellow
