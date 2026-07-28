"""Declared-edges harvester.

Some lineage cannot be inferred from any single system catalog — it lives in
ETL definitions (ADF copy activity, Synapse pipeline, Spark write). Until the
ADF/Fabric-pipeline harvesters cover everything, declare those edges manually
in a JSON file and feed them through this harvester so they share the same
schema, propagation, and DLP gate.

The JSON path defaults to samples/cloud/cross_system_edges.json. Each edge may
embed ${ENV_VAR} placeholders which are substituted from os.environ at read
time.
"""
from __future__ import annotations
import json
import os
import pathlib
import re
from collections.abc import Iterable

from common.schema import LineageEdge
from .base import Harvester


_VAR = re.compile(r"\$\{([A-Z0-9_]+)\}")


def _expand(value: str) -> str:
    return _VAR.sub(lambda m: os.environ.get(m.group(1), m.group(0)), value)


class DeclaredEdgesHarvester(Harvester):
    name = "declared"

    def __init__(self, path: str | pathlib.Path) -> None:
        self.path = pathlib.Path(path)

    def harvest(self) -> Iterable[LineageEdge]:
        if not self.path.exists():
            return
        doc = json.loads(self.path.read_text(encoding="utf-8"))
        for raw in doc.get("edges", []):
            column_map = raw.get("column_map") or {}
            columns: list[tuple[str, str]] | None = (
                [(src, tgt) for src, tgt in column_map.items()] if column_map else None
            )
            yield LineageEdge(
                source_qname=_expand(raw["source_qname"]),
                source_type=raw["source_type"],
                target_qname=_expand(raw["target_qname"]),
                target_type=raw["target_type"],
                process_name=_expand(raw["process_name"]),
                process_type=raw["process_type"],
                artifact_ref=raw.get("artifact_ref", str(self.path)),
                columns=columns,
                extra=raw.get("extra", {}),
            )
