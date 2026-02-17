# Microsoft Fabric Utilities

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Fabric](https://img.shields.io/badge/Microsoft-Fabric-green.svg)](https://www.microsoft.com/en-us/microsoft-fabric)
[![Contributions Welcome](https://img.shields.io/badge/Contributions-Welcome-brightgreen.svg)](CONTRIBUTING.md)

A community-driven collection of open-source notebooks, scripts, and utilities for **Microsoft Fabric** — designed to help customers accelerate common administrative, monitoring, governance, and maintenance tasks across Fabric workspaces.

## 📦 What's Included

| Asset | Folder | Description |
|-------|--------|-------------|
| **Warehouse & Lakehouse Metrics** | `notebooks/` | Fabric notebook that discovers all Warehouses and Lakehouses in a workspace, collects table-level row counts, size on disk, and maintenance settings via SQL Endpoint DMVs and the Fabric REST API. Includes consolidated reporting, maintenance configuration management, and CSV export. |

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
   git clone https://github.com/<org>/msft-fabric-utils.git
   ```

2. **Import** the desired notebook into your Fabric workspace
3. **Attach a Lakehouse** (optional — for CSV/Delta export)
4. **Configure** `TARGET_WORKSPACE_ID` or leave `None` to scan the current workspace
5. **Run all cells**

## 📂 Repository Structure

```
msft-fabric-utils/
├── notebooks/
│   └── fabric-warehouse-lakehouse-metrics.ipynb   # Warehouse & Lakehouse metrics + maintenance
├── scripts/
│   ├── powershell/                                # PowerShell automation scripts
│   └── python/                                    # Python utility scripts
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
| **Table Metrics Collection** | Row counts, reserved size, used size via SQL Endpoint DMVs (`sys.dm_db_partition_stats`, `sys.partitions`) |
| **Maintenance Settings** | Read and configure V-Order, file compaction, and unreferenced file retention for Lakehouses |
| **Maintenance Management** | Preview and apply maintenance configuration changes with dry-run support |
| **Consolidated Reporting** | Merged view of metrics + maintenance settings with summary aggregations |
| **CSV Export** | Export full metrics report with timestamps for auditing and sharing |

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
| `sys.dm_db_partition_stats` | Row counts and page-level size metrics (primary) |
| `sys.partitions` | Row counts fallback (if `dm_db_partition_stats` unavailable) |

> **Note:** `sys.dm_pdw_nodes_db_partition_stats` is a Synapse dedicated pool DMV and does **not** exist in Fabric SQL endpoints.

### Fabric-Native Libraries Used

| Library | Purpose |
|---------|---------|
| `sempy.fabric` | Workspace context and item discovery |
| `mssparkutils.credentials` | Automatic Entra ID token acquisition |
| `spark.read.format("jdbc")` | Spark JDBC connector for SQL endpoint queries |
| `notebookutils.mssparkutils` | File system operations |

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