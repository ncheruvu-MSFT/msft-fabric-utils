"""Read/write the `lineage.edges` Delta table.

Inside a Fabric notebook this uses the runtime spark session. Locally it falls
back to `deltalake` against OneLake via the abfss path + AAD token.
"""
from __future__ import annotations
import os
from typing import Iterable

from .schema import LineageEdge, EDGES_DELTA_SCHEMA


def _onelake_table_path() -> str:
    ws = os.environ["FABRIC_WORKSPACE_ID"]
    lh = os.environ["LAKEHOUSE_ID"]
    table = os.environ.get("EDGES_TABLE", "lineage_edges")
    return f"abfss://{ws}@onelake.dfs.fabric.microsoft.com/{lh}/Tables/{table}"


def write_edges_spark(edges: Iterable[LineageEdge]) -> int:
    """Append edges via the notebook-bound Spark session."""
    from pyspark.sql import SparkSession  # type: ignore

    spark = SparkSession.builder.getOrCreate()
    rows = [e.to_row() for e in edges]
    if not rows:
        return 0
    df = spark.createDataFrame(rows)
    df.write.format("delta").mode("append").saveAsTable(
        os.environ.get("EDGES_TABLE", "lineage_edges")
    )
    return df.count()


def write_edges_local(edges: Iterable[LineageEdge]) -> int:
    """Local/dev write using deltalake + an AAD token for OneLake."""
    from deltalake import write_deltalake  # type: ignore
    import pandas as pd
    from azure.identity import DefaultAzureCredential

    rows = [e.to_row() for e in edges]
    if not rows:
        return 0
    df = pd.DataFrame(rows)
    token = DefaultAzureCredential().get_token("https://storage.azure.com/.default").token
    write_deltalake(
        _onelake_table_path(),
        df,
        mode="append",
        storage_options={"bearer_token": token, "use_fabric_endpoint": "true"},
    )
    return len(rows)


def write_edges(edges: Iterable[LineageEdge]) -> int:
    """Auto-detects runtime — spark inside Fabric, deltalake locally."""
    try:
        import pyspark  # noqa: F401
        return write_edges_spark(edges)
    except ImportError:
        return write_edges_local(edges)
