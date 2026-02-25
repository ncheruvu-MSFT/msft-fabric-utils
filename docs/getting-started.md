# Getting Started with Microsoft Fabric Utilities

## Importing Notebooks into Fabric

1. Open your **Microsoft Fabric** workspace in the browser
2. Click **New** → **Import notebook**
3. Upload the `.ipynb` file from the `notebooks/` folder
4. Once imported, click on the notebook to open it
5. **Attach a Lakehouse** from the left panel (optional — required for CSV/Delta export)

## Configuration

Each notebook has a **Configuration** cell near the top. Common settings:

| Setting | Description |
|---------|-------------|
| `TARGET_WORKSPACE_ID` | Set to a specific workspace ID, or `None` to use the current workspace |
| `DRY_RUN` | Set to `True` to preview changes without applying (default) |

## Authentication

All notebooks use **Fabric-native authentication** via `mssparkutils.credentials.getToken()`. No manual credential setup is required when running inside a Fabric workspace.

## Data Sizes

The notebook collects **row counts only** via SQL Endpoint DMVs. For actual **OneLake storage sizes** (data on disk), use the PowerShell script:

```
scripts/powershell/Get-FabricTableSizes.ps1
```

> **Status:** Coming Soon — the PowerShell script is under testing.

See [Get the size of OneLake items](https://learn.microsoft.com/en-us/fabric/onelake/how-to-get-item-size) for details on the underlying Azure Storage commands.

## Notebook & Pipeline Efficiency Monitor

The `fabric-notebook-pipeline-efficiency.ipynb` notebook analyzes execution performance for all Notebooks and Data Pipelines in your workspace.

### Additional Settings

| Setting | Description |
|---------|-------------|
| `LOOKBACK_DAYS` | Number of days of run history to analyze (default: 30) |
| `INCLUDE_NOTEBOOKS` | Set to `True` to include Notebooks in the analysis |
| `INCLUDE_PIPELINES` | Set to `True` to include Data Pipelines in the analysis |

### What It Reports

- **Health Dashboard** – color-coded status (🟢 Healthy / 🟡 Warning / 🔴 Critical)
- **Success rates** and **failure analysis** per item
- **Duration trends** (avg, P50, P95) with improving/degrading indicators
- **Spark Resource Efficiency %** per notebook (compute efficiency, consistency, wasted compute)
- **Scheduling patterns** and invocation frequency
- **Automated recommendations** for items needing attention

### Spark Resource Efficiency

The notebook tracks Spark resource efficiency for each notebook — the same metric shown in the
Fabric portal under **Resources** → **Spark resource usage**. It tries the Fabric Spark Applications
API first, and falls back to a Compute Efficiency proxy calculated from job instance data:

| Metric | Formula |
|--------|---------|
| Compute % | Successful compute time / Total compute time × 100 |
| Consistency % | Duration P50 / Mean × 100 |
| Efficiency % | 70% Compute + 30% Consistency |

## Warehouse Performance & OneLake Soft Delete Monitor

The `fabric-warehouse-performance-softdelete.ipynb` notebook combines warehouse performance diagnostics with OneLake soft-deleted file scanning.

### Additional Settings

| Setting | Description |
|---------|-------------|
| `RUN_PERFORMANCE_DIAGNOSTICS` | Enable/disable Part A – warehouse performance checks (default: `True`) |
| `RUN_SOFT_DELETE_SCAN` | Enable/disable Part B – OneLake soft delete scanning (default: `True`) |
| `COLD_CACHE_THRESHOLD_MB` | Flag queries reading more than N MB from remote storage (default: 100) |
| `LONG_QUERY_THRESHOLD_SEC` | Flag queries running longer than N seconds (default: 300) |
| `VARCHAR_OVERSIZED_THRESHOLD` | Flag `varchar(n)` columns where n exceeds this value (default: 4000) |
| `TOP_N_QUERIES` | Number of top queries to show in reports (default: 20) |
| `SCAN_ITEM_TYPES` | Item types to scan for soft deletes – `Lakehouse`, `Warehouse` (default: both) |

### What It Reports

**Part A – Warehouse Performance:**
- **Cold cache detection** – queries fetching data from remote storage instead of cache
- **Long-running & frequently run queries** – via `queryinsights` views
- **Statistics freshness** – stale statistics that degrade query plan quality
- **Schema & data type audit** – oversized strings, inefficient decimals, nullable columns
- **Lock & transaction monitoring** – active locks and blocking detection
- **Table compaction health** – fragmented row groups needing optimization
- **V-Order & maintenance status** – configuration per Warehouse/Lakehouse

**Part B – OneLake Soft Delete:**
- **Soft-deleted file inventory** – files recoverable within the 7-day retention window
- **Storage cost impact** – soft-deleted data billed at the same rate as active data
- **Urgency alerts** – files expiring within 2 days
- **Recovery guidance** – step-by-step instructions for Storage Explorer, PowerShell, and REST API

### Dependencies

Requires `azure-storage-file-datalake` for soft delete scanning (auto-installed by the notebook).

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: sempy` | Ensure you're running inside a Fabric notebook, not a local Jupyter environment |
| `403 Forbidden` on REST API calls | Verify you have Admin or Member role on the target workspace |
| `dm_db_partition_stats not available` | The notebook will automatically fall back to `sys.partitions` (row counts only) |
| SQL endpoint connection timeout | Ensure the Warehouse/Lakehouse SQL endpoint is active and accessible |
