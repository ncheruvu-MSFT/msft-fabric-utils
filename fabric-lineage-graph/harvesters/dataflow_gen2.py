"""Dataflow Gen2 harvester — parses M (Power Query) expressions.

Dataflow Gen2 definitions are exposed via the Fabric REST
`/workspaces/{id}/dataflows/{id}/getDefinition` endpoint. The payload contains
a `mashup.pq` part (M expressions) and a `mashup.metadata.json` part with the
table list.

Strategy: extract the M source step per entity and apply the same parser used
by `powerbi.py` so the M-step types are unified.

Status: STUB. List wired; M parser shared with PowerBiHarvester (also TODO).
"""
from __future__ import annotations
import os
from collections.abc import Iterable

from common.schema import LineageEdge
from common import fabric_client
from .base import Harvester


class DataflowGen2Harvester(Harvester):
    name = "dataflow_gen2"

    def __init__(self, workspace_id: str | None = None) -> None:
        self.workspace_id = workspace_id or os.environ.get("FABRIC_WORKSPACE_ID", "")

    def harvest(self) -> Iterable[LineageEdge]:
        if not self.workspace_id:
            return
        items = fabric_client.list_items(self.workspace_id, item_type="Dataflow")
        for it in items:
            yield from self._edges_for_dataflow(it)

    def _edges_for_dataflow(self, item: dict) -> Iterable[LineageEdge]:
        # TODO: fetch definition via fabric_client and parse the mashup.pq part.
        return ()
