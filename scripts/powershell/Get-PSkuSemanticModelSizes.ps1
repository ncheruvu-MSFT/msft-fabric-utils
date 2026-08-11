<#
.SYNOPSIS
  Get the in-memory size of every semantic model on Premium (P-SKU) and/or
  Fabric (F-SKU) capacities in the tenant, using XMLA DMV queries.

.DESCRIPTION
  1. Authenticates via cached `az login` session.
  2. Enumerates capacities and filters by -CapacityFilter (P, F, or All).
  3. Gets all workspaces assigned to those capacities.
  4. Queries each dataset's XMLA endpoint using DISCOVER_STORAGE_TABLE_COLUMNS
     to compute compressed in-memory size.
  5. Exports results to CSV.

  Prerequisites:
    - `az login` completed (uses cached Azure CLI token)
    - SqlServer PowerShell module installed (Install-Module SqlServer)
    - XMLA Read endpoint enabled in the capacity admin settings
    - Caller has at least dataset Read + Build permissions (or is workspace Admin)

.PARAMETER CapacityFilter
  Which capacity SKUs to scan:
        P   - Premium P-SKU only (P1, P2, P3, P4, P5)
        F   - Fabric F-SKU only (F2, F4, F8, F16, F32, F64, F128, ...)
        All - Both P-SKU and F-SKU (default)

.PARAMETER OutputCsv
  Path to write the results CSV. Default: .\semantic-model-sizes.csv

.PARAMETER IncludeTableDetail
  If set, also outputs a per-table breakdown CSV alongside the summary.

.EXAMPLE
  .\Get-PSkuSemanticModelSizes.ps1

.EXAMPLE
  .\Get-PSkuSemanticModelSizes.ps1 -CapacityFilter P

.EXAMPLE
  .\Get-PSkuSemanticModelSizes.ps1 -CapacityFilter F -IncludeTableDetail

.EXAMPLE
  .\Get-PSkuSemanticModelSizes.ps1 -CapacityFilter All -OutputCsv C:\temp\model-sizes.csv
#>
[CmdletBinding()]
param(
    [ValidateSet('P','F','All')]
    [string]$CapacityFilter = 'All',
    [string]$OutputCsv = (Join-Path (Get-Location) 'semantic-model-sizes.csv'),
    [switch]$IncludeTableDetail
)

$ErrorActionPreference = 'Stop'
$PBI = 'https://api.powerbi.com/v1.0/myorg'

function Write-Step($m) { Write-Host "==> $m" -ForegroundColor Cyan }
function Write-Warn($m) { Write-Host "[warn] $m" -ForegroundColor Yellow }

# -----------------------------------------------------------------------------
# 1. Auth via az login
# -----------------------------------------------------------------------------
Write-Step 'Acquiring Power BI token via az login'
$token = az account get-access-token --resource 'https://analysis.windows.net/powerbi/api' --query accessToken -o tsv
if ([string]::IsNullOrWhiteSpace($token)) {
    throw "Failed to get a Power BI token. Run 'az login' first."
}
$hdr = @{ Authorization = "Bearer $token" }
Write-Host '    Token acquired.'

# -----------------------------------------------------------------------------
# 2. Load SqlServer module (for Invoke-ASCmd / XMLA queries)
# -----------------------------------------------------------------------------
Write-Step 'Loading SqlServer module'
if (-not (Get-Module -ListAvailable -Name SqlServer)) {
    Write-Host '    Installing SqlServer module...'
    Install-Module -Name SqlServer -Scope CurrentUser -Force -AllowClobber
}
Import-Module SqlServer -ErrorAction Stop
Write-Host '    SqlServer module loaded.'

# -----------------------------------------------------------------------------
# 3. Enumerate capacities -> filter by CapacityFilter
# -----------------------------------------------------------------------------
Write-Step "Enumerating capacities (filter: $CapacityFilter)"
$caps = (Invoke-RestMethod -Uri "$PBI/admin/capacities" -Headers $hdr).value

$skuPattern = switch ($CapacityFilter) {
    'P'   { '^P\d' }
    'F'   { '^F\d' }
    'All' { '^(P|F)\d' }
}
$filteredCaps = $caps | Where-Object { $_.sku -match $skuPattern }

if (-not $filteredCaps) {
    $label = switch ($CapacityFilter) { 'P' { 'P-SKU (Premium)' }; 'F' { 'F-SKU (Fabric)' }; 'All' { 'P-SKU or F-SKU' } }
    Write-Host "No $label capacities found in this tenant." -ForegroundColor Yellow
    Write-Host ''
    Write-Host 'Available capacities in tenant:' -ForegroundColor DarkGray
    $caps | ForEach-Object { Write-Host "    $($_.displayName) - SKU: $($_.sku) - State: $($_.state)" -ForegroundColor DarkGray }
    return
}

$targetCapIds = @($filteredCaps | Where-Object { $_.state -eq 'Active' } | Select-Object -ExpandProperty id)
$pausedCaps = @($filteredCaps | Where-Object { $_.state -ne 'Active' })
Write-Host "    Found $($filteredCaps.Count) matching capacities:"
$filteredCaps | ForEach-Object { 
    $stateColor = if ($_.state -eq 'Active') { 'Green' } else { 'Yellow' }
    Write-Host "      $($_.displayName) - $($_.sku) - $($_.region) - $($_.state)" -ForegroundColor $stateColor
}
if ($pausedCaps.Count -gt 0) {
    Write-Warn "$($pausedCaps.Count) capacity/capacities are not Active (paused/deallocated) - their workspaces will be skipped."
}
if ($targetCapIds.Count -eq 0) {
    Write-Host 'No ACTIVE capacities matching the filter. Start/resume a capacity and re-run.' -ForegroundColor Yellow
    return
}

# -----------------------------------------------------------------------------
# 4. Get workspaces on matching capacities
# -----------------------------------------------------------------------------
Write-Step "Enumerating workspaces on $CapacityFilter capacities"
$allWs = New-Object System.Collections.Generic.List[object]
$skip = 0
do {
    $uri = "$PBI/admin/groups?`$top=5000&`$skip=$skip&`$expand=datasets"
    $page = (Invoke-RestMethod -Uri $uri -Headers $hdr).value
    if ($page) { $allWs.AddRange($page) }
    $skip += 5000
} while ($page -and $page.Count -eq 5000)

$pSkuWorkspaces = @($allWs | Where-Object { $_.capacityId -in $targetCapIds -and $_.state -eq 'Active' })
$totalDatasets = ($pSkuWorkspaces | ForEach-Object { @($_.datasets).Count } | Measure-Object -Sum).Sum
Write-Host "    Found $($pSkuWorkspaces.Count) workspaces with $totalDatasets datasets on P-SKU capacities"

# -----------------------------------------------------------------------------
# 5. Query each dataset via XMLA DMV
# -----------------------------------------------------------------------------
Write-Step 'Querying semantic model sizes via XMLA (this may take a while)'

$summaryRows = New-Object System.Collections.Generic.List[object]
$tableRows   = New-Object System.Collections.Generic.List[object]
$errors      = New-Object System.Collections.Generic.List[object]

$counter = 0
foreach ($ws in $pSkuWorkspaces) {
    $wsName = $ws.name
    $server = "powerbi://api.powerbi.com/v1.0/myorg/$wsName"

    foreach ($ds in $ws.datasets) {
        $counter++
        $dsName = $ds.name
        $dsId   = $ds.id
        Write-Progress -Activity 'Querying XMLA' -Status "$counter / $totalDatasets - $wsName / $dsName" -PercentComplete (($counter / [Math]::Max($totalDatasets,1)) * 100)

        try {
            # XMLA connection via OAuth token in Password field (standard PBI XMLA auth)
            $connStr = "Provider=MSOLAP;Data Source=${server};Initial Catalog=$dsName;Password=$token"

            # Query column-level storage DMV
            $xmlaQuery = @"
<Statement xmlns="urn:schemas-microsoft-com:xml-analysis">
SELECT
    [TABLE_ID],
    [COLUMN_ID],
    [DICTIONARY_SIZE],
    [COLUMN_ENCODING_SIZE]
FROM `$SYSTEM.DISCOVER_STORAGE_TABLE_COLUMNS
</Statement>
"@
            $raw = Invoke-ASCmd -ConnectionString $connStr -Query $xmlaQuery

            # Parse the XML response
            [xml]$x = $raw
            $ns = New-Object Xml.XmlNamespaceManager($x.NameTable)
            $ns.AddNamespace('r', 'urn:schemas-microsoft-com:xml-analysis:rowset')

            $rows = $x.SelectNodes('//r:row', $ns)

            $tableSizes = @{}
            $grandTotal = [long]0

            foreach ($row in $rows) {
                $tableId   = $row.SelectSingleNode('r:TABLE_ID', $ns).'#text'
                $dictNode  = $row.SelectSingleNode('r:DICTIONARY_SIZE', $ns)
                $encNode   = $row.SelectSingleNode('r:COLUMN_ENCODING_SIZE', $ns)
                $dictSize  = if ($null -ne $dictNode -and $dictNode.InnerText) { [long]$dictNode.InnerText } else { [long]0 }
                $encSize   = if ($null -ne $encNode -and $encNode.InnerText) { [long]$encNode.InnerText } else { [long]0 }
                $colBytes  = $dictSize + $encSize
                $grandTotal += $colBytes

                if ($tableId) {
                    if (-not $tableSizes.ContainsKey($tableId)) { $tableSizes[$tableId] = [long]0 }
                    $tableSizes[$tableId] += $colBytes
                }
            }

            # Summary row
            $summaryRows.Add([PSCustomObject]@{
                Workspace   = $wsName
                WorkspaceId = $ws.id
                Dataset     = $dsName
                DatasetId   = $dsId
                SizeBytes   = $grandTotal
                SizeMB      = [math]::Round($grandTotal / 1MB, 2)
                SizeGB      = [math]::Round($grandTotal / 1GB, 3)
                Tables      = $tableSizes.Count
                Status      = 'OK'
            })

            # Per-table detail
            if ($IncludeTableDetail) {
                foreach ($kv in $tableSizes.GetEnumerator()) {
                    $tableRows.Add([PSCustomObject]@{
                        Workspace = $wsName
                        Dataset   = $dsName
                        DatasetId = $dsId
                        TableName = $kv.Key
                        SizeBytes = $kv.Value
                        SizeMB    = [math]::Round($kv.Value / 1MB, 2)
                    })
                }
            }

        } catch {
            $errMsg = $_.Exception.Message
            # Common: model is in Direct Lake mode or not accessible
            $summaryRows.Add([PSCustomObject]@{
                Workspace   = $wsName
                WorkspaceId = $ws.id
                Dataset     = $dsName
                DatasetId   = $dsId
                SizeBytes   = $null
                SizeMB      = $null
                SizeGB      = $null
                Tables      = $null
                Status      = "ERROR: $errMsg"
            })
            $errors.Add([PSCustomObject]@{
                Workspace = $wsName
                Dataset   = $dsName
                Error     = $errMsg
            })
        }
    }
}
Write-Progress -Activity 'Querying XMLA' -Completed

# -----------------------------------------------------------------------------
# 6. Output
# -----------------------------------------------------------------------------
Write-Step 'Writing results'

# Summary CSV
$summaryRows | Sort-Object SizeBytes -Descending | Export-Csv -NoTypeInformation -Path $OutputCsv
Write-Host "    Summary: $OutputCsv ($($summaryRows.Count) models)"

# Table detail CSV
if ($IncludeTableDetail -and $tableRows.Count -gt 0) {
    $detailPath = $OutputCsv -replace '\.csv$', '-table-detail.csv'
    $tableRows | Sort-Object Dataset, SizeBytes -Descending | Export-Csv -NoTypeInformation -Path $detailPath
    Write-Host "    Table detail: $detailPath ($($tableRows.Count) rows)"
}

# Console summary
Write-Host ''
Write-Host '--- P-SKU Semantic Model Size Summary ---' -ForegroundColor Green
$ok = @($summaryRows | Where-Object { $_.Status -eq 'OK' })
if ($ok.Count -gt 0) {
    $totalGB = ($ok | Measure-Object -Property SizeBytes -Sum).Sum / 1GB
    Write-Host "    Models scanned successfully: $($ok.Count)"
    Write-Host "    Total in-memory size: $([math]::Round($totalGB, 2)) GB"
    Write-Host ''
    Write-Host '    Top 20 largest models:' -ForegroundColor Green
    $ok | Sort-Object SizeBytes -Descending | Select-Object -First 20 Workspace, Dataset, SizeMB, SizeGB, Tables |
        Format-Table -AutoSize
}

if ($errors.Count -gt 0) {
    Write-Host "    Models with errors: $($errors.Count)" -ForegroundColor Yellow
    $errors | Select-Object -First 10 Workspace, Dataset, Error | Format-Table -AutoSize
}
