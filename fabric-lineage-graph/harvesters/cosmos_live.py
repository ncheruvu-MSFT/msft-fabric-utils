"""Cosmos DB (SQL API) live lineage harvester.

Cosmos has no relational catalog → no intra-DB lineage. This harvester just
enumerates containers and registers them as nodes so the graph has anchors
for cross-system edges declared in samples/cloud/cross_system_edges.json.

Auth: DefaultAzureCredential against the Cosmos data plane. Requires the
`Cosmos DB Built-in Data Reader` role (control-plane RBAC).
"""
from __future__ import annotations
import os
from collections.abc import Iterable

from common.schema import LineageEdge
from .base import Harvester


class CosmosLiveHarvester(Harvester):
    name = "cosmos_live"

    def __init__(self, endpoint: str | None = None, database: str | None = None) -> None:
        self.endpoint = endpoint or os.environ.get("COSMOS_ENDPOINT", "")
        self.database = database or os.environ.get("COSMOS_DATABASE", "")

    def harvest(self) -> Iterable[LineageEdge]:
        if not (self.endpoint and self.database):
            return
        try:
            from azure.cosmos import CosmosClient  # type: ignore
            from azure.identity import DefaultAzureCredential
        except ImportError:
            print("cosmos_live: azure-cosmos or azure-identity not installed; skipping")
            return
        client = CosmosClient(self.endpoint, credential=DefaultAzureCredential())
        db = client.get_database_client(self.database)
        # Self-loop edges keep the container in the graph as a node with the
        # correct kind. build_graph dedups; render skips self-loops in PyVis.
        for cont in db.list_containers():
            qname = f"cosmos://{self.endpoint}/{self.database}/{cont['id']}"
            yield LineageEdge(
                source_qname=qname,
                source_type="azure_cosmosdb_sqlapi_collection",
                target_qname=qname,
                target_type="azure_cosmosdb_sqlapi_collection",
                process_name=f"cosmos:catalog:{cont['id']}",
                process_type="catalog_anchor",
                artifact_ref=f"cosmos://{self.endpoint}/{self.database}",
                extra={"partitionKey": str(cont.get("partitionKey", ""))},
            )
