$ErrorActionPreference = 'Stop'
$REPO   = 'ncheruvu-MSFT/msft-fabric-utils'
$CLIENT = '47a48c18-47f4-4f90-a5e7-f5add3cb2ee3'
$TENANT = '62c0cb46-1fcc-4c79-ba1b-d7d9fdfbaa68'
$SUB    = '31613fe0-1e9b-4a97-b771-dc48fbaa0fbb'

# Get current GitHub user as reviewer for gated environments
$me = (gh api user --jq .login).Trim()
$myId = (gh api user --jq .id)
Write-Host "Reviewer for gated envs: $me (id=$myId)" -ForegroundColor Cyan

# ── 1. Repo secrets ──────────────────────────────────────────
Write-Host "`nSetting repo secrets..." -ForegroundColor Cyan
$CLIENT | gh secret set AZURE_CLIENT_ID       --repo $REPO --body -
$TENANT | gh secret set AZURE_TENANT_ID       --repo $REPO --body -
$SUB    | gh secret set AZURE_SUBSCRIPTION_ID --repo $REPO --body -
gh secret list --repo $REPO

# ── 2. Environments ──────────────────────────────────────────
$envs = @(
  @{ name='fabric-dev';  gated=$false }
  @{ name='fabric-test'; gated=$true  }
  @{ name='fabric-prod'; gated=$true  }
)
foreach ($e in $envs) {
  Write-Host "`nCreating environment '$($e.name)' (gated=$($e.gated))..." -ForegroundColor Cyan
  if ($e.gated) {
    $body = @{
      reviewers = @( @{ type='User'; id=[int]$myId } )
      deployment_branch_policy = $null
    } | ConvertTo-Json -Depth 5 -Compress
  } else {
    $body = '{}'
  }
  $tmp = [System.IO.Path]::GetTempFileName()
  [System.IO.File]::WriteAllText($tmp, $body)
  gh api -X PUT "repos/$REPO/environments/$($e.name)" --input $tmp | Out-Null
  Remove-Item $tmp -Force
  Write-Host "  OK: $($e.name)" -ForegroundColor Green
}

Write-Host "`n--- Environments ---" -ForegroundColor Green
gh api "repos/$REPO/environments" --jq '.environments[] | {name, protection: (.protection_rules // [])}'
