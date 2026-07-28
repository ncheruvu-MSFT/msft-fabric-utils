"""Unified lineage edge schema — every harvester emits records of this shape.

The schema is intentionally narrow so it round-trips cleanly to:

* a OneLake Delta table (`lineage.edges`) for the graph backing store
* Atlas v2 entities + Process in Purview (`process_name` -> Process.qualifiedName)
* a NetworkX MultiDiGraph for the in-app PyVis renderer
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any


# Canonical type names — must match the Purview Atlas typeDefs the lineage
# scripts in fabric-sdlc-governance already register.
KNOWN_SOURCE_TYPES = {
    "azure_sql_table",
    "azure_sql_view",
    "azure_sql_procedure",
    "azure_postgresql_table",
    "azure_postgresql_view",
    "azure_cosmosdb_sqlapi_collection",
    "oracle_table",
    "oracle_view",
    "databricks_table",
    "fabric_lakehouse_table",
    "fabric_warehouse_table",
    "fabric_kql_table",
    "powerbi_dataset",
    "powerbi_report",
    "powerbi_dataflow",
    "adf_pipeline",
    "adf_dataset",
    "fabric_data_pipeline",
    "fabric_notebook",
    "fabric_dataflow_gen2",
    "file",  # generic fallback for ADLS/OneLake paths
}

KNOWN_PROCESS_TYPES = {
    "adf_copy",
    "adf_dataflow",
    "tsql_select",
    "tsql_insert",
    "tsql_merge",
    "tsql_ctas",
    "tsql_view",
    "pbi_m_step",
    "pbi_dax_measure",
    "spark_read",
    "spark_write",
    "spark_save_as_table",
    "spark_sql",
    "fabric_pipeline_activity",
    "dataflow_gen2_step",
    "databricks_view",
    "catalog_anchor",  # used by cosmos_live to register containers as nodes
}


@dataclass
class LineageEdge:
    source_qname: str
    source_type: str
    target_qname: str
    target_type: str
    process_name: str
    process_type: str
    artifact_ref: str
    harvested_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    columns: list[tuple[str, str]] | None = None  # [(src_col, tgt_col), ...]
    extra: dict[str, Any] = field(default_factory=dict)

    def to_row(self) -> dict[str, Any]:
        d = asdict(self)
        if d["columns"] is not None:
            d["columns"] = [{"src": s, "tgt": t} for s, t in d["columns"]]
        return d


# Delta table schema (Spark-compatible). Used by common.onelake_io.write_edges
# when running inside a Fabric notebook.
EDGES_DELTA_SCHEMA = """
    source_qname STRING NOT NULL,
    source_type  STRING NOT NULL,
    target_qname STRING NOT NULL,
    target_type  STRING NOT NULL,
    process_name STRING NOT NULL,
    process_type STRING NOT NULL,
    artifact_ref STRING NOT NULL,
    harvested_at TIMESTAMP NOT NULL,
    columns ARRAY<STRUCT<src: STRING, tgt: STRING>>,
    extra MAP<STRING, STRING>
"""
