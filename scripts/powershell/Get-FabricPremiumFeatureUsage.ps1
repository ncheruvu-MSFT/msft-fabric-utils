<#
.SYNOPSIS
  Inventory Power BI / Fabric Premium-class feature usage across ALL workspaces
  in the tenant (Fabric and non-Fabric alike).

.DESCRIPTION
  Uses the Power BI *Admin* REST APIs, which see the entire tenant regardless of
  capacity type. For every workspace it reports:
    - Capacity assignment and SKU class:
        Shared/Pro | PPU (Premium-Per-User) | Premium (P-SKU) | Embedded (A-SKU)
        | Fabric (F-SKU) | Trial
    - Premium-class feature signals: paginated (RDL) reports, dataflows,
      datamarts, large-dataset storage format, XMLA/Direct Lake datasets,
      and Fabric (non-Power BI) items (lakehouse/warehouse/notebook/...).

  "Non-Fabric" coverage: classic Premium (P-SKU), PPU and Pro workspaces and
  their reports are returned by the same admin APIs and are classified here too.
  Fabric-only item types only appear on F-SKU capacities.

  Two depths:
    (default) fast pass via /admin/groups?$expand=... — capacity + item counts.
    -Deep     adds the metadata Scanner API (/admin/workspaces/getInfo) to read
              dataset storage mode, datamarts and Direct Lake details.

.PARAMETER OutputCsv
  Path to write the per-workspace CSV. Default: .\fabric-premium-usage.csv

.PARAMETER Deep
  Also run the Scanner API for dataset-level detail (slower, needs the
  "Enhance admin APIs responses with detailed metadata" tenant setting on).

.PARAMETER TopWorkspaces
  Page size for /admin/groups (max 5000). Default 5000.

.EXAMPLE
  ./Get-FabricPremiumFeatureUsage.ps1

.EXAMPLE
  ./Get-FabricPremiumFeatureUsage.ps1 -Deep -OutputCsv C:\temp\pbi-premium.csv

.NOTES
  Requires Fabric/Power BI tenant administrator rights (or a service principal
  allowed to use read-only admin APIs). Auth uses your cached Azure CLI login:
    az login
  No secrets are stored. Token is acquired for the Power BI service resource.
#>
[CmdletBinding()]
param(
    [string]$OutputCsv = (Join-Path (Get-Location) 'fabric-premium-usage.csv'),
    [switch]$Deep,
    [ValidateRange(100, 5000)][int]$TopWorkspaces = 5000
)

$ErrorActionPreference = 'Stop'
$PBI = 'https://api.powerbi.com/v1.0/myorg'

function Write-Step($m) { Write-Host "==> $m" -ForegroundColor Cyan }
function Write-Warn($m) { Write-Host "[warn] $m" -ForegroundColor Yellow }

# --- Auth: Power BI service resource via cached az login --------------------
Write-Step 'Acquiring Power BI admin token (az account get-access-token)'
$token = az account get-access-token --resource 'https://analysis.windows.net/powerbi/api' --query accessToken -o tsv
if ([string]::IsNullOrWhiteSpace($token)) {
    throw "Failed to get a Power BI token. Run 'az login' first."
}
$hdr = @{ Authorization = "Bearer $token" }

function Invoke-PBI {
    param([string]$Method = 'GET', [string]$Uri, $Body)
    $args = @{ Method = $Method; Uri = $Uri; Headers = $hdr }
    if ($Body) { $args.Body = ($Body | ConvertTo-Json -Depth 10); $args.ContentType = 'application/json' }
    Invoke-RestMethod @args
}

# --- 1. Capacity -> SKU class map -------------------------------------------
Write-Step 'Enumerating capacities (admin/capacities)'
$capMap = @{}
try {
    $caps = (Invoke-PBI -Uri "$PBI/admin/capacities").value
    foreach ($c in $caps) {
        $sku = "$($c.sku)"
        $class = switch -Regex ($sku) {
            '^F\d'        { 'Fabric (F-SKU)';   break }
            '^P\d'        { 'Premium (P-SKU)';  break }
            '^EM\d|^A\d'  { 'Embedded (A-SKU)'; break }
            '^PP'         { 'PPU';              break }
            default       { if ($sku) { "Other ($sku)" } else { 'Unknown' } }
        }
        $capMap[$c.id] = [pscustomobject]@{
            CapacityName = $c.displayName
            Sku          = $sku
            Class        = $class
            Region       = $c.region
            State        = $c.state
        }
    }
    Write-Host "    found $($caps.Count) capacities"
}
catch {
    Write-Warn "admin/capacities failed: $($_.ErrorDetails.Message ?? $_.Exception.Message)"
}

# --- 2. Enumerate ALL workspaces (paged) ------------------------------------
Write-Step 'Enumerating workspaces (admin/groups)'
$expand = 'reports,datasets,dataflows,dashboards,datamarts'
$all = New-Object System.Collections.Generic.List[object]
$skip = 0
do {
    $uri = "$PBI/admin/groups?`$top=$TopWorkspaces&`$skip=$skip&`$expand=$expand"
    $page = (Invoke-PBI -Uri $uri).value
    if ($page) { $all.AddRange($page) }
    $skip += $TopWorkspaces
} while ($page -and $page.Count -eq $TopWorkspaces)
Write-Host "    found $($all.Count) workspaces"

# --- 3. Optional deep scan (Scanner API) ------------------------------------
$scanByWs = @{}
if ($Deep) {
    Write-Step 'Deep scan via Scanner API (admin/workspaces/getInfo)'
    $ids = @($all | Where-Object { $_.type -eq 'Workspace' } | Select-Object -ExpandProperty id)
    for ($i = 0; $i -lt $ids.Count; $i += 100) {
        $batch = $ids[$i..([Math]::Min($i + 99, $ids.Count - 1))]
        $q = 'lineage=false&datasourceDetails=false&datasetSchema=false&datasetExpressions=false&getArtifactUsers=false'
        $scan = Invoke-PBI -Method POST -Uri "$PBI/admin/workspaces/getInfo?$q" -Body @{ workspaces = $batch }
        $scanId = $scan.id
        do {
            Start-Sleep -Seconds 3
            $status = Invoke-PBI -Uri "$PBI/admin/workspaces/scanStatus/$scanId"
        } while ($status.status -ne 'Succeeded' -and $status.status -ne 'Failed')
        if ($status.status -eq 'Failed') { Write-Warn "scan batch failed at offset $i"; continue }
        $result = Invoke-PBI -Uri "$PBI/admin/workspaces/scanResult/$scanId"
        foreach ($w in $result.workspaces) { $scanByWs[$w.id] = $w }
        Write-Host "    scanned $([Math]::Min($i + 100, $ids.Count))/$($ids.Count)"
    }
}

# --- 4. Classify + build rows -----------------------------------------------
Write-Step 'Classifying workspaces'
$rows = foreach ($w in $all) {
    $cap = if ($w.capacityId -and $capMap.ContainsKey($w.capacityId)) { $capMap[$w.capacityId] } else { $null }
    $class = if ($w.isOnDedicatedCapacity) {
        if ($cap) { $cap.Class } else { 'Dedicated (unknown SKU)' }
    } else { 'Shared / Pro' }

    $paginated = @($w.reports | Where-Object { $_.reportType -eq 'PaginatedReport' }).Count
    $pbiReports = @($w.reports | Where-Object { $_.reportType -ne 'PaginatedReport' }).Count
    $dataflows = @($w.dataflows).Count
    $datamarts = @($w.datamarts).Count

    # Scanner-derived premium signals
    $largeModel = 0; $directLake = 0; $fabricItems = 0
    if ($Deep -and $scanByWs.ContainsKey($w.id)) {
        $sw = $scanByWs[$w.id]
        $largeModel = @($sw.datasets | Where-Object { $_.targetStorageMode -eq 'PremiumFiles' }).Count
        $directLake = @($sw.datasets | Where-Object { "$($_.contentProviderType)" -match 'DirectLake' }).Count
        $known = 'Report','Dataset','Dashboard','Dataflow','Datamart'
        $fabricItems = @($sw.PSObject.Properties |
            Where-Object { $_.Name -notin @('id','name','type','state','reports','dashboards','datasets','dataflows','datamarts') -and $_.Value -is [System.Array] } |
            ForEach-Object { $_.Value.Count } | Measure-Object -Sum).Sum
    }

    $premiumSignals = New-Object System.Collections.Generic.List[string]
    if ($class -notin @('Shared / Pro')) { $premiumSignals.Add('DedicatedCapacity') }
    if ($paginated -gt 0)  { $premiumSignals.Add('PaginatedReports') }
    if ($dataflows -gt 0)  { $premiumSignals.Add('Dataflows') }
    if ($datamarts -gt 0)  { $premiumSignals.Add('Datamarts') }
    if ($largeModel -gt 0) { $premiumSignals.Add('LargeModelStorage') }
    if ($directLake -gt 0) { $premiumSignals.Add('DirectLake') }
    if ($fabricItems -gt 0){ $premiumSignals.Add('FabricItems') }

    [pscustomobject]@{
        WorkspaceName    = $w.name
        WorkspaceId      = $w.id
        WorkspaceState   = $w.state
        IsFabric         = ($class -eq 'Fabric (F-SKU)')
        CapacityClass    = $class
        CapacitySku      = if ($cap) { $cap.Sku } else { '' }
        CapacityName     = if ($cap) { $cap.CapacityName } else { '' }
        CapacityRegion   = if ($cap) { $cap.Region } else { '' }
        PbiReports       = $pbiReports
        PaginatedReports = $paginated
        Datasets         = @($w.datasets).Count
        Dataflows        = $dataflows
        Datamarts        = $datamarts
        Dashboards       = @($w.dashboards).Count
        LargeModelStores = $largeModel
        DirectLakeModels = $directLake
        FabricItems      = $fabricItems
        PremiumSignals   = ($premiumSignals -join ';')
    }
}

# --- 5. Output --------------------------------------------------------------
$rows | Sort-Object CapacityClass, WorkspaceName | Export-Csv -NoTypeInformation -Path $OutputCsv
Write-Step "Wrote $($rows.Count) rows -> $OutputCsv"

Write-Host ''
Write-Host 'Workspaces by capacity class:' -ForegroundColor Green
$rows | Group-Object CapacityClass | Sort-Object Count -Descending |
    Select-Object @{n='CapacityClass';e={$_.Name}}, Count | Format-Table -AutoSize

Write-Host 'Premium-class feature footprint (workspaces using each):' -ForegroundColor Green
'DedicatedCapacity','PaginatedReports','Dataflows','Datamarts','LargeModelStorage','DirectLake','FabricItems' |
    ForEach-Object {
        $sig = $_
        [pscustomobject]@{ Feature = $sig; Workspaces = @($rows | Where-Object { $_.PremiumSignals -match $sig }).Count }
    } | Format-Table -AutoSize

if (-not $Deep) {
    Write-Host "Tip: re-run with -Deep for dataset storage mode, datamarts and Direct Lake detail." -ForegroundColor DarkGray
}
