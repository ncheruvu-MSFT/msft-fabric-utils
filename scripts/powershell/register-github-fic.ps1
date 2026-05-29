$ErrorActionPreference = 'Stop'
$APP  = '47a48c18-47f4-4f90-a5e7-f5add3cb2ee3'
$REPO = 'ncheruvu-MSFT/msft-fabric-utils'
$creds = @(
  @{ name='gh-main';        sub='ref:refs/heads/main' }
  @{ name='gh-fabric-dev';  sub='environment:fabric-dev' }
  @{ name='gh-fabric-test'; sub='environment:fabric-test' }
  @{ name='gh-fabric-prod'; sub='environment:fabric-prod' }
)
foreach ($c in $creds) {
  $body = @{
    name      = $c.name
    issuer    = 'https://token.actions.githubusercontent.com'
    subject   = "repo:${REPO}:$($c.sub)"
    audiences = @('api://AzureADTokenExchange')
  } | ConvertTo-Json -Compress
  $tmp = [System.IO.Path]::GetTempFileName()
  [System.IO.File]::WriteAllText($tmp, $body)
  Write-Host "Creating $($c.name) -> $($c.sub)" -ForegroundColor Cyan
  az ad app federated-credential create --id $APP --parameters "@$tmp" 2>&1 | Out-String | Write-Host
  Remove-Item $tmp -Force
}
Write-Host "`n--- Current federated credentials ---" -ForegroundColor Green
az ad app federated-credential list --id $APP --query "[].{name:name,subject:subject}" -o table
