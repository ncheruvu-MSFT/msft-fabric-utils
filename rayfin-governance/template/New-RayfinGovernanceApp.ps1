<#
.SYNOPSIS
  Scaffold a new Rayfin governance app from a proven template in this repo.

.DESCRIPTION
  Copies one of the existing, working rayfin-governance apps into a new folder,
  rewrites its name across package.json / rayfin.yml / index.html, resets any
  recorded Fabric deployment, and (optionally) runs `npm install`.

  The copied app already includes the premium Fluent theme and the "Rayfin app"
  badge from the branding kit, so the new app is customer-ready out of the box.

.PARAMETER Name
  New app name in kebab-case, e.g. "contoso-glossary-app". Used as the folder
  name, package name and Rayfin item id.

.PARAMETER From
  Which existing app to clone. Defaults to glossary-app (richest example).

.PARAMETER Destination
  Parent folder for the new app. Defaults to the current directory.

.PARAMETER Install
  Run `npm install` in the new app after copying.

.EXAMPLE
  ./New-RayfinGovernanceApp.ps1 -Name contoso-glossary-app -Install

.EXAMPLE
  ./New-RayfinGovernanceApp.ps1 -Name acme-lineage-app -From lineage-app
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidatePattern('^[a-z][a-z0-9-]*[a-z0-9]$')]
    [string]$Name,

    [ValidateSet('glossary-app', 'lineage-app', 'sdlc-governance-app',
        'data-agent-governance-app', 'infra-request-app')]
    [string]$From = 'glossary-app',

    [string]$Destination = (Get-Location).Path,

    [switch]$Install
)

$ErrorActionPreference = 'Stop'

# The rayfin-governance root is the parent of this template folder.
$repoGovRoot = Split-Path -Parent $PSScriptRoot
$source = Join-Path $repoGovRoot $From
if (-not (Test-Path $source)) {
    throw "Source app '$From' not found at $source"
}

$target = Join-Path $Destination $Name
if (Test-Path $target) {
    throw "Destination '$target' already exists. Choose another -Name or remove it."
}

Write-Host "==> Cloning $From -> $Name" -ForegroundColor Cyan

# Copy the source app, skipping build artifacts and secrets.
$exclude = @('node_modules', 'dist', '.env.local', 'build.log', 'deploy.log',
    'deploy2.log', 'dbapply.log', 'genconfig.log', 'npminstall.log',
    'dryrun.log', 'loginstatus.log', 'capstate.txt')

New-Item -ItemType Directory -Path $target | Out-Null
Get-ChildItem -Path $source -Force | Where-Object { $exclude -notcontains $_.Name } |
    ForEach-Object {
        Copy-Item -Path $_.FullName -Destination $target -Recurse -Force -Exclude $exclude
    }

# Remove any recorded Fabric deployment so the new app provisions fresh.
$deployments = Join-Path $target 'rayfin/.deployments.json'
if (Test-Path $deployments) { Remove-Item $deployments -Force }
$dotenv = Join-Path $target 'rayfin/.env'
if (Test-Path $dotenv) { Remove-Item $dotenv -Force }

# Rewrite the app identity in place.
$oldId = $From
$titleCase = (Get-Culture).TextInfo.ToTitleCase(($Name -replace '-', ' '))

function Set-Content-Replace($path, $find, $replace) {
    if (Test-Path $path) {
        (Get-Content $path -Raw).Replace($find, $replace) |
            Set-Content -Path $path -NoNewline
    }
}

Set-Content-Replace (Join-Path $target 'package.json') "`"name`": `"$oldId`"" "`"name`": `"$Name`""
Set-Content-Replace (Join-Path $target 'rayfin/rayfin.yml') "id: $oldId" "id: $Name"

# Friendly display name in rayfin.yml (best-effort; leaves value if pattern differs).
$yml = Join-Path $target 'rayfin/rayfin.yml'
if (Test-Path $yml) {
    (Get-Content $yml -Raw) -replace '(?m)^name:.*$', "name: $titleCase" |
        Set-Content -Path $yml -NoNewline
}

Write-Host "==> Created $target" -ForegroundColor Green

if ($Install) {
    Write-Host "==> Running npm install" -ForegroundColor Cyan
    Push-Location $target
    npm install
    Pop-Location
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  cd $Name"
if (-not $Install) { Write-Host "  npm install" }
Write-Host "  npm run dev                 # local preview at http://localhost:5173"
Write-Host "  `$env:FABRIC_WORKSPACE_ID = '<workspace-guid>'"
Write-Host "  `$env:FABRIC_CAPACITY_ID  = '<capacity-guid>'"
Write-Host "  rayfin login --tenant <tenant-guid>"
Write-Host "  rayfin up --yes --workspace-id <workspace-guid>"
