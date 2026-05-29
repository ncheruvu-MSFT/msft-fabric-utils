# Grant SPN Admin on Fabric workspaces (one-time).
param(
  [string]$SpnObjectId = 'b6b2a4a5-b522-4fc4-94d4-05fc9823ff66',
  [string[]]$Workspaces = @('fabric-de-dev','fabric-de-test','fabric-de-prod')
)
$ErrorActionPreference = 'Continue'
$token = az account get-access-token --resource https://api.fabric.microsoft.com --query accessToken -o tsv
$hdr = @{ Authorization = "Bearer $token"; 'Content-Type' = 'application/json' }
$ws = (Invoke-RestMethod -Uri 'https://api.fabric.microsoft.com/v1/workspaces' -Headers @{Authorization="Bearer $token"}).value
foreach ($name in $Workspaces) {
  $w = $ws | Where-Object { $_.displayName -eq $name }
  if (-not $w) { Write-Host "MISSING: $name"; continue }
  $body = @{ principal = @{ id = $SpnObjectId; type = 'ServicePrincipal' }; role = 'Admin' } | ConvertTo-Json
  try {
    Invoke-RestMethod -Method POST -Uri "https://api.fabric.microsoft.com/v1/workspaces/$($w.id)/roleAssignments" -Headers $hdr -Body $body | Out-Null
    Write-Host "OK $name -> Admin"
  } catch {
    $resp = $_.Exception.Response
    $code = if ($resp) { [int]$resp.StatusCode } else { 0 }
    $detail = $_.ErrorDetails.Message
    if (-not $detail -and $resp) {
      try { $sr = New-Object IO.StreamReader($resp.GetResponseStream()); $detail = $sr.ReadToEnd() } catch {}
    }
    if ($detail -match 'PrincipalAlreadyHasAccess|already') { Write-Host "OK $name (already had access)" }
    else { Write-Host "WARN $name [$code] : $detail" }
  }
}
