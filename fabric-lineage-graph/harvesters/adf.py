"""Azure Data Factory harvester.

Strategy:
1. List all pipelines via ADF REST (`adf_list_pipelines`).
2. For each pipeline, walk activities. Emit edges per activity type:
     * Copy           : source.dataset -> sink.dataset
     * DataFlow       : referenced datasets (inputs -> outputs from mapping)
     * Lookup/Script  : best-effort SQL handed to the T-SQL parser

Status: STUB. The activity walker is sketched; dataset->qname resolution and
the per-activity-type emit blocks are TODO. Wired into the harvester registry
so the runner notebook will skip cleanly until implemented.
"""
from __future__ import annotations
import os
from collections.abc import Iterable

from common.schema import LineageEdge
from common import fabric_client
from .base import Harvester


class AdfHarvester(Harvester):
    name = "adf"

    def __init__(self, sub_id: str | None = None, rg: str | None = None,
                 factory: str | None = None) -> None:
        self.sub_id = sub_id or os.environ.get("ADF_SUBSCRIPTION_ID", "")
        self.rg = rg or os.environ.get("ADF_RESOURCE_GROUP", "")
        self.factory = factory or os.environ.get("ADF_FACTORY_NAME", "")

    def harvest(self) -> Iterable[LineageEdge]:
        if not (self.sub_id and self.rg and self.factory):
            return
        pipelines = fabric_client.adf_list_pipelines(self.sub_id, self.rg, self.factory)
        for pl in pipelines:
            yield from self._edges_for_pipeline(pl)

    def _edges_for_pipeline(self, pl: dict) -> Iterable[LineageEdge]:
        # TODO: walk pl["properties"]["activities"], resolve datasets via
        # fabric_client.adf_get_dataset, emit edges per activity type.
        # Return nothing for now so the harvester is a no-op rather than crash.
        return ()
