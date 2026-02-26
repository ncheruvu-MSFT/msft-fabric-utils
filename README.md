# Microsoft Fabric Utilities

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Fabric](https://img.shields.io/badge/Microsoft-Fabric-green.svg)](https://www.microsoft.com/en-us/microsoft-fabric)
[![Contributions Welcome](https://img.shields.io/badge/Contributions-Welcome-brightgreen.svg)](CONTRIBUTING.md)

A community-driven collection of open-source notebooks, scripts, and utilities for **Microsoft Fabric** — designed to help customers accelerate common administrative, monitoring, governance, and maintenance tasks across Fabric workspaces.

## 📦 What's Included

| Asset | Folder | Description |
|-------|--------|-------------|
| **Warehouse & Lakehouse Metrics** | `notebooks/` | Fabric notebook that discovers all Warehouses and Lakehouses in a workspace, collects table-level row counts and maintenance settings via SQL Endpoint DMVs and the Fabric REST API. Includes consolidated reporting, maintenance configuration management, and CSV export. |
| **Notebook & Pipeline Efficiency** | `notebooks/` | Fabric notebook that analyzes execution efficiency for all Notebooks and Data Pipelines in a workspace. Collects run history, calculates success rates, duration trends (avg/P50/P95), failure analysis, health dashboard, and scheduling patterns via the Fabric REST API. |
| **Warehouse Performance & Soft Delete** | `notebooks/` | Fabric notebook combining warehouse performance diagnostics (cold cache, long-running queries, statistics freshness, schema optimization, lock monitoring, compaction health, V-Order) with OneLake soft-deleted file scanning and recovery guidance. |
| **Capacity Migration Inventory** | `fabric-region-migration/` | Fabric notebook that auto-discovers all capacities, workspaces, and items tenant-wide via Admin APIs. Classifies each item as movable vs non-movable for cross-region capacity migration, calculates workspace complexity, assigns migration waves, and exports CSV inventory. |
| **Migration Tracker Generator** | `fabric-region-migration/` | Python script that generates a multi-sheet Excel workbook for tracking a Fabric capacity migration (phases, risk register, RACI matrix, issue tracker, validation checklist). |
| **OneLake Table Sizes** *(Coming Soon)* | `scripts/powershell/` | PowerShell script that lists tables and their actual OneLake storage sizes for a given Lakehouse or Warehouse. Uses Azure Storage commands against OneLake. |

## 🚀 Getting Started

### Prerequisites

| Requirement | Details |
|-------------|---------|
| **Microsoft Fabric** | Trial, Premium, or Fabric capacity |
| **Workspace Role** | Admin or Member |
| **Runtime** | Fabric notebook runtime (PySpark) |
| **Built-in Libraries** | `sempy`, `mssparkutils`, `pandas`, `requests`, `pyspark` (pre-installed) |

### Quick Start

1. **Clone** this repository

   ```bash
   git clone https://github.com/ncheruvu-MSFT/msft-fabric-utils.git
   ```

2. **Import** the desired notebook into your Fabric workspace
3. **Attach a Lakehouse** (optional — for CSV/Delta export)
4. **Configure** `TARGET_WORKSPACE_ID` or leave `None` to scan the current workspace
5. **Run all cells**

## 📂 Repository Structure

```
msft-fabric-utils/
├── notebooks/
│   ├── fabric-warehouse-lakehouse-metrics.ipynb        # Warehouse & Lakehouse metrics + maintenance
│   ├── fabric-notebook-pipeline-efficiency.ipynb       # Notebook & Pipeline execution efficiency
│   └── fabric-warehouse-performance-softdelete.ipynb   # Warehouse perf & OneLake soft delete
├── fabric-region-migration/
│   ├── fabric-capacity-migration-inventory.ipynb       # Cross-region migration inventory & planning
│   └── generate_migration_tracker_excel.py             # Excel migration tracker generator
├── scripts/
│   ├── powershell/                                     # PowerShell automation scripts
│   └── python/                                         # Python utility scripts
├── docs/
│   └── getting-started.md                         # Additional documentation
├── .gitignore
├── LICENSE                                        # MIT License
├── CONTRIBUTING.md                                # Contribution guidelines
├── CODE_OF_CONDUCT.md                             # Microsoft Open Source Code of Conduct
├── SECURITY.md                                    # Security policy
└── README.md                                      # This file
```

## 🔧 Covered Scenarios

### Warehouse & Lakehouse Metrics Notebook

| Capability | Description |
|------------|-------------|
| **Item Discovery** | Enumerate all Warehouses and Lakehouses in a workspace via Fabric REST API |
| **Table Row Counts** | Row counts via SQL Endpoint DMVs (`sys.dm_db_partition_stats`, `sys.partitions`) |
| **Maintenance Settings** | Read and configure V-Order, file compaction, and unreferenced file retention for Lakehouses |
| **Maintenance Management** | Preview and apply maintenance configuration changes with dry-run support |
| **Consolidated Reporting** | Merged view of row counts + maintenance settings with summary aggregations |
| **CSV Export** | Export full metrics report with timestamps for auditing and sharing |

### Notebook & Pipeline Efficiency Notebook

| Capability | Description |
|------------|-------------|
| **Item Discovery** | Enumerate all Notebooks and Data Pipelines in a workspace via Fabric REST API |
| **Run History** | Fetch job instances (executions) with start/end times, status, and failure reasons |
| **Success Rate Analysis** | Per-item success/failure counts and success rate percentage |
| **Duration Statistics** | Average, median (P50), 95th percentile (P95), min/max execution times |
| **Health Dashboard** | Color-coded health status (Healthy / Warning / Critical) based on success rate |
| **Failure Analysis** | Top failing items, most common failure reasons, recent failure timeline |
| **Duration Trends** | Weekly aggregation showing performance trends (improving / degrading / stable) |
| **Scheduling Analysis** | Invocation method distribution (manual / scheduled) and execution frequency |
| **Spark Resource Efficiency** | Per-notebook Spark efficiency % — tries Spark Applications API, falls back to compute efficiency proxy |
| **Recommendations** | Automated suggestions for items that need attention |
| **CSV Export** | Export efficiency summary, run history, and Spark efficiency with timestamps |

### Warehouse Performance & OneLake Soft Delete Notebook

| Capability | Description |
|------------|-------------|
| **Warehouse Discovery** | Enumerate all Warehouses and Lakehouses in a workspace via Fabric REST API |
| **Cold Cache Detection** | Identify queries hitting remote storage instead of cache via `queryinsights.exec_requests_history` |
| **Long-Running Queries** | Surface slow query patterns from `queryinsights.long_running_queries` |
| **Frequently Run Queries** | Find most-executed queries (optimization candidates) from `queryinsights.frequently_run_queries` |
| **Statistics Freshness** | Detect stale statistics that may degrade query plan quality (`sys.stats` + `dm_db_stats_properties`) |
| **Schema & Data Type Audit** | Flag oversized `varchar` columns, inefficient `decimal(18,0)`, excessive nullable columns |
| **Lock & Transaction Monitoring** | Active locks and blocking detection via `sys.dm_tran_locks` |
| **Table Compaction Health** | Small/fragmented row groups per table via `sys.dm_db_partition_stats` |
| **V-Order & Maintenance Status** | V-Order and compaction configuration per Warehouse/Lakehouse |
| **OneLake Soft-Deleted Files** | Scan for soft-deleted files using Azure Data Lake Storage SDK |
| **Soft Delete Recovery Guide** | Recovery instructions via Storage Explorer, PowerShell, and REST API |
| **Consolidated Summary** | Prioritized recommendations covering performance and data protection |
| **CSV Export** | Export all reports with timestamps for auditing |

> **References:** [Warehouse Performance Guidelines](https://learn.microsoft.com/en-us/fabric/data-warehouse/guidelines-warehouse-performance) · [OneLake Soft Delete](https://learn.microsoft.com/en-us/fabric/onelake/onelake-disaster-recovery#soft-delete-for-onelake-files)

### Capacity Migration Inventory Notebook

| Capability | Description |
|------------|-------------|
| **Capacity Discovery** | Enumerate all Fabric capacities with region, SKU, and state via `GET /v1/capacities` |
| **Workspace Discovery** | List all workspaces per capacity via Admin API `GET /v1/admin/workspaces` |
| **Item Enumeration** | List all items tenant-wide via Admin API `GET /v1/admin/items` with pagination |
| **Movability Classification** | Classify each item as ✅ Movable or ❌ Non-Movable per [MS Learn capacity reassignment restrictions](https://learn.microsoft.com/en-us/fabric/admin/portal-workspace-capacity-reassignment) |
| **Migration Complexity** | Assess Low / Medium / High complexity per workspace based on item composition |
| **Wave Assignment** | Auto-assign migration waves (Wave 1 = movable-only, Wave 2 = data copy, Wave 3 = recreate) |
| **Phased Plan** | Auto-generated 6-phase migration plan (Discovery → Setup → Wave 1–3 → Cutover) |
| **Constraints Reminder** | Surface key constraints: jobs cancelled, staging items, Private Link, large-storage models |
| **CSV Export** | Export capacities, workspace summary, and item detail CSVs for the Excel tracker |
| **Retry / Backoff** | Built-in `fabric_api_get()` helper with exponential backoff for HTTP 429 rate limits |

> **References:** [Capacity Reassignment Restrictions](https://learn.microsoft.com/en-us/fabric/admin/portal-workspace-capacity-reassignment) · [Multi-Geo Support](https://learn.microsoft.com/en-us/fabric/admin/service-admin-premium-multi-geo) · [Admin Items API](https://learn.microsoft.com/en-us/rest/api/fabric/admin/items/list-items) · [Find Your Fabric Home Region](https://learn.microsoft.com/en-us/fabric/admin/find-fabric-home-region)

### Migration Tracker Excel Generator

| Sheet | Description |
|-------|-------------|
| **Migration Inventory** | Template for capacity/workspace/item data (populate from notebook CSV exports) |
| **Migration Phases** | 6-phase plan with milestones, owners, planned/actual dates, status, % complete |
| **Risk Register** | 10 pre-populated migration risks with likelihood, impact, and mitigation strategies |
| **RACI Matrix** | Responsibility assignment for 17 migration tasks across 7 roles (color-coded) |
| **Issue Tracker** | Log for tracking migration issues with severity, status, and resolution |
| **Validation Checklist** | Post-migration validation steps per wave (data integrity, connectivity, performance) |

```bash
# Generate the Excel tracker
pip install openpyxl
python fabric-region-migration/generate_migration_tracker_excel.py
```

### OneLake Table Sizes – PowerShell *(Coming Soon)*

| Capability | Description |
|------------|-------------|
| **Table Discovery** | List all tables under a Lakehouse or Warehouse in OneLake |
| **Actual File Sizes** | Recursively calculate real Delta/Parquet file sizes per table |
| **CSV Export** | Export table size report with file counts |
| **Prerequisites** | Auto-installs `Az.Accounts` and `Az.Storage` modules; prompts for Azure login |

> **Reference:** [Get the size of OneLake items](https://learn.microsoft.com/en-us/fabric/onelake/how-to-get-item-size)

### Table Maintenance in Microsoft Fabric

| Feature | Warehouse | Lakehouse |
|---------|-----------|-----------|
| **Auto-Statistics** | Always ON (built-in) | N/A (Delta-based) |
| **V-Order Optimization** | Always ON (auto) | Configurable (ON/OFF) |
| **File Compaction** | Always ON (auto) | Configurable (ON/OFF) |
| **Unreferenced File Removal** | Auto-managed | Configurable (1–90 days retention) |
| **Maintenance Schedule** | Automatic | User-configurable |

### SQL Endpoint DMVs Used

| DMV | Purpose |
|-----|---------|
| `sys.tables` | Table metadata (name, create/modify dates) |
| `sys.schemas` | Schema names |
| `sys.dm_db_partition_stats` | Row counts (primary) |
| `sys.partitions` | Row counts fallback (if `dm_db_partition_stats` unavailable) |

> **Note:** `sys.dm_pdw_nodes_db_partition_stats` is a Synapse dedicated pool DMV and does **not** exist in Fabric SQL endpoints. Data sizes from DMVs do not reflect actual OneLake file sizes — use the PowerShell script for accurate storage measurement.

### Fabric-Native Libraries Used

| Library | Purpose |
|---------|---------|
| `sempy.fabric` | Workspace context and item discovery |
| `mssparkutils.credentials` | Automatic Entra ID token acquisition |
| `spark.read.format("jdbc")` | Spark JDBC connector for SQL endpoint queries |

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting a pull request.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/). For more information, see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any questions or comments.

## 🔒 Security

If you discover a security vulnerability, please follow the instructions in [SECURITY.md](SECURITY.md). **Do not** report security vulnerabilities through public GitHub issues.

## 📄 License

This project is licensed under the [MIT License](LICENSE).

## ⚠️ Disclaimer

This repository is **not an official Microsoft product**. It is a community-driven collection of utilities provided **as-is**, without warranty or support. Always test in a non-production environment before applying changes to production workspaces. Use at your own risk.

## 📚 Resources

- [Microsoft Fabric Documentation](https://learn.microsoft.com/en-us/fabric/)
- [Fabric REST API Reference](https://learn.microsoft.com/en-us/rest/api/fabric/)
- [Lakehouse Table Maintenance](https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-table-maintenance)
- [Fabric Warehouse Overview](https://learn.microsoft.com/en-us/fabric/data-warehouse/data-warehousing)
- [Warehouse Performance Guidelines](https://learn.microsoft.com/en-us/fabric/data-warehouse/guidelines-warehouse-performance)
- [OneLake Disaster Recovery & Soft Delete](https://learn.microsoft.com/en-us/fabric/onelake/onelake-disaster-recovery)
- [Recover Soft-Deleted Files](https://learn.microsoft.com/en-us/fabric/onelake/soft-delete)
- [Capacity Reassignment Restrictions](https://learn.microsoft.com/en-us/fabric/admin/portal-workspace-capacity-reassignment)
- [Multi-Geo Support for Fabric](https://learn.microsoft.com/en-us/fabric/admin/service-admin-premium-multi-geo)
- [Find Your Fabric Home Region](https://learn.microsoft.com/en-us/fabric/admin/find-fabric-home-region)
- [Admin Items API](https://learn.microsoft.com/en-us/rest/api/fabric/admin/items/list-items)
- [Admin Workspaces API](https://learn.microsoft.com/en-us/rest/api/fabric/admin/workspaces/list-workspaces)