"""Push edges from the OneLake `lineage.edges` table to Purview Atlas v2.

This is a thin wrapper over `common.purview_client.upsert_edges` that loads
the latest edges Delta snapshot. Designed to be called from the scheduled
`02_publish_to_purview.ipynb` notebook.
"""
from __future__ import annotations

from common.schema import LineageEdge
from common.purview_client import upsert_edges


def push_edges(edges: list[LineageEdge]) -> dict[str, int]:
    return upsert_edges(edges)
