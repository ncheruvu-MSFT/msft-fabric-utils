# Fabric Lineage Graph + Governance App

End-to-end **data lineage harvester + governance app** that runs **entirely inside Microsoft Fabric**:

- Crawls **ADF pipelines, Power BI (DAX/M), T-SQL, Fabric notebooks, Fabric Data Pipelines, Dataflows Gen2**.
- Emits a unified `LineageEdge` schema into a OneLake **Delta table** (`lineage.edges`).
- Pushes the same edges to **Microsoft Purview** as Atlas v2 typed entities + processes.
- Renders an **interactive graph** in a Fabric Data App (Streamlit).
- Exposes a **REST API** via Fabric User Data Functions for the UI and external callers.
- Provides **glossary editor**, **catalog bulk-update**, **Entra-group → Purview-role self-approval** workflows.
- Reuses the existing workflows already defined in [`../fabric-sdlc-governance/scripts/purview_apply_workflows.py`](../fabric-sdlc-governance/scripts/purview_apply_workflows.py).

> **Scope boundary** — this package builds the *lineage graph + governance UI*. The
> Purview domain/glossary/workflow bootstrap, classification rules, DLP, and ADO
> SDLC pipelines live in [`../fabric-sdlc-governance`](../fabric-sdlc-governance/) and
> are reused here, not re-implemented.

## Why Streamlit and not Blazor?

Fabric Data Apps and User Data Functions are **Python-only** as of 2026. Blazor cannot run
natively inside Fabric. If a .NET Blazor UI is required, see
[`docs/blazor-alternative.md`](docs/blazor-alternative.md) — host Blazor in Azure
Container Apps with managed identity to OneLake and call the same UDF REST API
defined here. The harvest + graph + Purview layers are unchanged.

## Architecture

```
                       +-----------------------------------------------+
                       |              Microsoft Fabric Workspace        |
                       |                                                |
   +---------------+   |  +--------------+      +------------------+    |
   | ADF / ARM     |---+->|  Harvest     |----->|  Lakehouse:      |    |
   | Power BI      |---+->|  Notebooks   |      |  lineage.edges   |    |
   | Fabric SQL    |---+->|  (scheduled  |      |  (Delta)         |    |
   | Notebooks     |---+->|  Data        |      +-------+----------+    |
   | Data Pipeline |---+->|  Pipeline)   |              |               |
   | Dataflow Gen2 |---+->|              |              v               |
   +---------------+   |  +--------------+      +------------------+    |
                       |                        |  Publish-to-     |    |
                       |  +--------------+      |  Purview         |---+--> Purview
                       |  | User Data    |<-----+  Notebook        |    |   Atlas v2
                       |  | Functions    |      +------------------+    |
                       |  | (REST API)   |                              |
                       |  +------+-------+      +------------------+    |
                       |         |              |  Entra Group     |---+--> MS Graph
                       |         v              |  Sync Notebook   |    |
                       |  +--------------+      +------------------+    |
                       |  | Streamlit    |                              |
                       |  | Data App     |                              |
                       |  +--------------+                              |
                       +-----------------------------------------------+
```

## Folder layout

| Path | Purpose |
|---|---|
| [`common/`](common/) | Shared `LineageEdge` schema, Purview/Fabric clients, OneLake IO |
| [`harvesters/`](harvesters/) | One module per source type — all return `LineageEdge` records |
| [`graph/`](graph/) | NetworkX build + PyVis render + Purview push |
| [`app/`](app/) | Streamlit Fabric Data App — graph viewer, glossary editor, access requests |
| [`api/`](api/) | Fabric User Data Functions — REST endpoints for the app and external callers |
| [`notebooks/`](notebooks/) | Scheduled harvest, Purview publish, workflow trigger, Entra sync |
| [`pipelines/`](pipelines/) | Fabric Data Pipeline JSON that schedules the notebooks |
| [`infra/`](infra/) | Bicep (KV + identity) + Python deployer for the Fabric items |
| [`docs/`](docs/) | Architecture, Blazor alternative |

## Quickstart

```powershell
# 1. Install local deps (the Fabric notebooks pick these up from %pip install)
pip install -r requirements.txt

# 2. Copy env template
Copy-Item .env.example .env
# edit .env — TENANT_ID, FABRIC_WORKSPACE_ID, PURVIEW_ACCOUNT, LAKEHOUSE_ID, etc.

# 3. Deploy the Fabric items (lakehouse, app, UDFs, scheduled pipeline)
python infra/deploy_fabric_items.py

# 4. Trigger the first harvest from local (or wait for the scheduled run)
python -m harvesters.tsql --workspace-id $env:FABRIC_WORKSPACE_ID
```

## Common edge schema

Every harvester emits records that match [`common/schema.py`](common/schema.py):

```python
@dataclass
class LineageEdge:
    source_qname: str        # e.g. "mssql://srv/db/dbo/Customers"
    source_type:  str        # "azure_sql_table" | "powerbi_dataset" | "fabric_lakehouse_table" | ...
    target_qname: str
    target_type:  str
    process_name: str        # "adf:CopyCustomers" | "tsql:proc_load_silver" | "pbi:m:Source"
    process_type: str        # "adf_copy" | "tsql_select" | "pbi_m_step" | "spark_write" | ...
    columns:      list[tuple[str, str]] | None  # column-level when available
    artifact_ref: str        # path/URI of the artifact the edge was parsed from
    harvested_at: str        # ISO-8601 UTC
    extra:        dict       # harvester-specific extras (file line, DAX expr, etc.)
```

## What's deferred / TODO

The skeleton scaffolds each harvester and ships a working **T-SQL harvester** (most reusable, exercises the full edge schema). The other harvesters are stubs with the parser entry-point sketched and the REST endpoints they'll call documented. See each module's docstring for status.
