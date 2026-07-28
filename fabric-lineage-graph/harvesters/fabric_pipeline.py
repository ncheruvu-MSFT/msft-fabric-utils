"""Fabric Data Pipeline harvester.

Fabric Data Pipelines are stored as JSON with a similar activity shape to ADF.
The Fabric REST endpoint `/workspaces/{id}/dataPipelines/{id}/getDefinition`
returns a base64 inline payload with the pipeline JSON.

Strategy: list pipelines in the workspace, fetch each definition, walk
activities (Copy/Notebook/Lookup), emit edges. Notebook activities are
cross-referenced to the NotebookHarvester output via `notebookId`.

Status: STUB. List+fetch wired; activity walker is the remaining work.
"""
from __future__ import annotations
import os
from collections.abc import Iterable

from common.schema import LineageEdge
from common import fabric_client
from .base import Harvester


class FabricPipelineHarvester(Harvester):
    name = "fabric_pipeline"

    def __init__(self, workspace_id: str | None = None) -> None:
        self.workspace_id = workspace_id or os.environ.get("FABRIC_WORKSPACE_ID", "")

    def harvest(self) -> Iterable[LineageEdge]:
        if not self.workspace_id:
            return
        items = fabric_client.list_items(self.workspace_id, item_type="DataPipeline")
        for it in items:
            pipeline = fabric_client.get_pipeline_definition(self.workspace_id, it["id"])
            yield from self._edges_for_pipeline(it, pipeline)

    def _edges_for_pipeline(self, item: dict, definition: dict) -> Iterable[LineageEdge]:
        # TODO: base64-decode definition["definition"]["parts"][*]["payload"]
        # and walk activities.
        return ()
