<#
.SYNOPSIS
    Lists tables and their OneLake storage sizes for a Fabric Lakehouse or Warehouse.

.DESCRIPTION
    Connects to OneLake via Azure Storage PowerShell commands and enumerates all
    tables under the specified item (Lakehouse or Warehouse). For each table it
    calculates the total file size by recursively listing all child objects.

    Reference: https://learn.microsoft.com/en-us/fabric/onelake/how-to-get-item-size

.PARAMETER WorkspaceId
    The GUID of the Fabric workspace that contains the item.

.PARAMETER ItemId
    The GUID of the Lakehouse or Warehouse whose tables you want to measure.

.PARAMETER Unit
    Display unit for sizes: Auto, Bytes, KB, MB, GB, TB. Default is Auto.

.PARAMETER ExportCsv
    Optional path to export results as a CSV file.

.EXAMPLE
    # List tables for a lakehouse
    .\Get-FabricTableSizes.ps1 -WorkspaceId "<your-workspace-id>" -ItemId "<your-item-id>"

.EXAMPLE
    # Export to CSV in GB
    .\Get-FabricTableSizes.ps1 -WorkspaceId "<your-workspace-id>" -ItemId "<your-item-id>" -Unit GB -ExportCsv "./table_sizes.csv"

.NOTES
    Prerequisites:
      - Az.Storage module   : Install-Module Az.Storage -Repository PSGallery -Force
      - Azure sign-in       : Connect-AzAccount
      - Read access to the target workspace/item in OneLake
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, HelpMessage = "Fabric workspace GUID")]
    [ValidatePattern('^[0-9a-fA-F]{8}-([0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}$')]
    [string]$WorkspaceId,

    [Parameter(Mandatory = $true, HelpMessage = "Lakehouse or Warehouse GUID")]
    [ValidatePattern('^[0-9a-fA-F]{8}-([0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}$')]
    [string]$ItemId,

    [Parameter(HelpMessage = "Display unit: Auto, Bytes, KB, MB, GB, TB")]
    [ValidateSet("Auto", "Bytes", "KB", "MB", "GB", "TB")]
    [string]$Unit = "Auto",

    [Parameter(HelpMessage = "Optional CSV export path")]
    [string]$ExportCsv
)

#region ── Helper Functions ───────────────────────────────────────────────────

function Format-FileSize {
    <# Converts bytes to a human-readable string #>
    param(
        [Parameter(Mandatory)] [double]$Bytes,
        [string]$DisplayUnit = "Auto"
    )

    switch ($DisplayUnit) {
        "Bytes" { return "{0:N0} B" -f $Bytes }
        "KB"    { return "{0:N2} KB" -f ($Bytes / 1KB) }
        "MB"    { return "{0:N2} MB" -f ($Bytes / 1MB) }
        "GB"    { return "{0:N4} GB" -f ($Bytes / 1GB) }
        "TB"    { return "{0:N6} TB" -f ($Bytes / 1TB) }
        default {
            # Auto
            if ($Bytes -ge 1TB) { return "{0:N4} TB" -f ($Bytes / 1TB) }
            if ($Bytes -ge 1GB) { return "{0:N4} GB" -f ($Bytes / 1GB) }
            if ($Bytes -ge 1MB) { return "{0:N2} MB" -f ($Bytes / 1MB) }
            if ($Bytes -ge 1KB) { return "{0:N2} KB" -f ($Bytes / 1KB) }
            return "{0:N0} B" -f $Bytes
        }
    }
}

function Get-RawBytes {
    <# Returns the numeric value in the requested unit (for CSV export) #>
    param(
        [Parameter(Mandatory)] [double]$Bytes,
        [string]$DisplayUnit = "Auto"
    )

    switch ($DisplayUnit) {
        "Bytes" { return $Bytes }
        "KB"    { return [math]::Round($Bytes / 1KB, 2) }
        "MB"    { return [math]::Round($Bytes / 1MB, 2) }
        "GB"    { return [math]::Round($Bytes / 1GB, 4) }
        "TB"    { return [math]::Round($Bytes / 1TB, 6) }
        default { return $Bytes }   # raw bytes for Auto
    }
}

#endregion

#region ── Pre-flight Checks & Install ────────────────────────────────────────

# 1. Ensure Az.Accounts module is available (needed for Connect-AzAccount)
if (-not (Get-Module -ListAvailable -Name Az.Accounts)) {
    Write-Host "Az.Accounts module not found. Installing..." -ForegroundColor Yellow
    try {
        Install-Module Az.Accounts -Repository PSGallery -Force -Scope CurrentUser -AllowClobber
        Write-Host "  Az.Accounts installed successfully." -ForegroundColor Green
    }
    catch {
        Write-Error "Failed to install Az.Accounts: $($_.Exception.Message)"
        exit 1
    }
}

# 2. Ensure Az.Storage module is available
if (-not (Get-Module -ListAvailable -Name Az.Storage)) {
    Write-Host "Az.Storage module not found. Installing..." -ForegroundColor Yellow
    try {
        Install-Module Az.Storage -Repository PSGallery -Force -Scope CurrentUser -AllowClobber
        Write-Host "  Az.Storage installed successfully." -ForegroundColor Green
    }
    catch {
        Write-Error "Failed to install Az.Storage: $($_.Exception.Message)"
        exit 1
    }
}

Import-Module Az.Accounts -ErrorAction Stop
Import-Module Az.Storage  -ErrorAction Stop

# 3. Check Azure sign-in; prompt to login if not authenticated
$azContext = Get-AzContext -ErrorAction SilentlyContinue
if (-not $azContext -or -not $azContext.Account) {
    Write-Host "Not signed in to Azure. Launching interactive login..." -ForegroundColor Yellow
    try {
        Connect-AzAccount -ErrorAction Stop | Out-Null
        $azContext = Get-AzContext -ErrorAction Stop
    }
    catch {
        Write-Error "Azure login failed: $($_.Exception.Message)"
        exit 1
    }
}

Write-Host "Signed in as: $($azContext.Account.Id)" -ForegroundColor Cyan

#endregion

#region ── Main Logic ─────────────────────────────────────────────────────────

Write-Host "`n=== Fabric OneLake Table Size Report ===" -ForegroundColor Green
Write-Host "Workspace : $WorkspaceId"
Write-Host "Item      : $ItemId"
Write-Host "Unit      : $Unit"
Write-Host ""

# 1. Create OneLake storage context
Write-Host "Creating OneLake storage context..." -ForegroundColor Yellow
$ctx = New-AzStorageContext -StorageAccountName 'onelake' -UseConnectedAccount -Endpoint 'fabric.microsoft.com'

# 2. Discover tables – list immediate children of <ItemId>/Tables
$tablesPath = "$ItemId/Tables"
Write-Host "Listing tables under: $tablesPath" -ForegroundColor Yellow

try {
    $tableItems = Get-AzDataLakeGen2ChildItem -Context $ctx -FileSystem $WorkspaceId -Path $tablesPath -ErrorAction Stop
}
catch {
    Write-Error "Failed to list tables. Verify the Workspace ID, Item ID, and your permissions.`n$($_.Exception.Message)"
    exit 1
}

# Filter to directories only (each directory = one table)
$tables = $tableItems | Where-Object { $_.IsDirectory -eq $true }

if (-not $tables -or $tables.Count -eq 0) {
    Write-Warning "No tables found under $tablesPath"
    exit 0
}

Write-Host "Found $($tables.Count) table(s). Calculating sizes...`n" -ForegroundColor Yellow

# 3. For each table, recursively calculate size
$results = [System.Collections.Generic.List[PSCustomObject]]::new()
$totalBytes = 0
$tableIndex = 0

foreach ($table in $tables) {
    $tableIndex++
    $tableName = $table.Path -replace "^.*Tables/", ""
    $tablePath = "$tablesPath/$tableName"

    Write-Progress -Activity "Calculating table sizes" -Status "$tableName ($tableIndex of $($tables.Count))" -PercentComplete (($tableIndex / $tables.Count) * 100)

    try {
        $measurement = Get-AzDataLakeGen2ChildItem -Context $ctx -FileSystem $WorkspaceId -Path $tablePath -Recurse -FetchProperty -ErrorAction Stop |
            Measure-Object -Property Length -Sum

        $sizeBytes = if ($measurement.Sum) { $measurement.Sum } else { 0 }
        $fileCount = if ($measurement.Count) { $measurement.Count } else { 0 }
    }
    catch {
        Write-Warning "  Could not measure table '$tableName': $($_.Exception.Message)"
        $sizeBytes = 0
        $fileCount = 0
    }

    $totalBytes += $sizeBytes

    $results.Add([PSCustomObject]@{
        TableName       = $tableName
        SizeBytes       = $sizeBytes
        SizeFormatted   = Format-FileSize -Bytes $sizeBytes -DisplayUnit $Unit
        FileCount       = $fileCount
    })
}

Write-Progress -Activity "Calculating table sizes" -Completed

#endregion

#region ── Output ─────────────────────────────────────────────────────────────

# Sort by size descending
$results = $results | Sort-Object -Property SizeBytes -Descending

# Console table
$results | Format-Table -AutoSize @(
    @{ Label = "#";              Expression = { $script:rowNum++; $script:rowNum }; Alignment = "Right" }
    @{ Label = "Table Name";     Expression = { $_.TableName } }
    @{ Label = "Files";          Expression = { $_.FileCount }; Alignment = "Right" }
    @{ Label = "Size";           Expression = { $_.SizeFormatted }; Alignment = "Right" }
)
$script:rowNum = 0   # reset after Format-Table enumerates

# Summary
Write-Host "─────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host ("Total tables : {0}" -f $results.Count)
Write-Host ("Total size   : {0}" -f (Format-FileSize -Bytes $totalBytes -DisplayUnit $Unit))
Write-Host ("Total files  : {0}" -f ($results | Measure-Object -Property FileCount -Sum).Sum)
Write-Host ""

# Optional CSV export
if ($ExportCsv) {
    $csvData = $results | Select-Object TableName, FileCount, SizeBytes,
        @{ Name = "Size_$Unit"; Expression = { Get-RawBytes -Bytes $_.SizeBytes -DisplayUnit $Unit } }

    $csvData | Export-Csv -Path $ExportCsv -NoTypeInformation -Encoding UTF8
    Write-Host "Results exported to: $ExportCsv" -ForegroundColor Green
}

#endregion
