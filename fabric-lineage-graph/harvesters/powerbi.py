"""Power BI harvester.

Strategy:
1. Call Power BI Scanner API (`getInfo` + `scanResult`) for the target
   workspaces — returns dataset tables, columns, measures, **M expression**
   and source string for each partition.
2. Parse the `source` string of each M step:
     * Sql.Database(server, db)       -> azure_sql_table
     * Fabric.Warehouse / Fabric.Lakehouse -> fabric_* types
     * AzureStorage.Blobs / Web.Contents -> file
3. Emit dataset -> source edges (one per M step) and report -> dataset edges
   for thick reports.

Status: STUB. Scanner call wired; M parsing is the remaining work. A future
extension can add DAX measure-level lineage via `DEFINE MEASURE` rewriting.
"""
from __future__ import annotations
import os
from collections.abc import Iterable

from common.schema import LineageEdge
from common import fabric_client
from .base import Harvester


class PowerBiHarvester(Harvester):
    name = "powerbi"

    def __init__(self, workspace_ids: list[str] | None = None) -> None:
        self.workspace_ids = workspace_ids or [
            w.strip() for w in os.environ.get("PBI_WORKSPACE_IDS", "").split(",")
            if w.strip()
        ]

    def harvest(self) -> Iterable[LineageEdge]:
        if not self.workspace_ids:
            return
        scan = fabric_client.pbi_scanner_workspaces(self.workspace_ids)
        for ws in scan.get("workspaces", []):
            for ds in ws.get("datasets", []):
                yield from self._edges_for_dataset(ws, ds)

    def _edges_for_dataset(self, ws: dict, ds: dict) -> Iterable[LineageEdge]:
        # TODO: parse ds["expressions"] / ds["tables"][*]["source"][0]["expression"]
        # to identify Sql.Database / Fabric.Warehouse / etc., emit edges.
        return ()
