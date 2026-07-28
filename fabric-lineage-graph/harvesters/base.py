"""Base contract for all lineage harvesters.

Each harvester implements `harvest()` returning an iterable of `LineageEdge`.
The runner (notebooks/01_harvest_all.ipynb) collects edges from every
harvester and persists them in a single write to `lineage.edges`.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from collections.abc import Iterable

from common.schema import LineageEdge


class Harvester(ABC):
    name: str = "base"

    @abstractmethod
    def harvest(self) -> Iterable[LineageEdge]:
        ...
