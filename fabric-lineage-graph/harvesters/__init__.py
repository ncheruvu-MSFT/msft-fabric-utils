"""Harvester registry.

Import all concrete harvesters here so the notebook runner can iterate over
`HARVESTERS` without knowing each module name.
"""
from .base import Harvester
from .tsql import TsqlHarvester
from .notebook import NotebookHarvester
from .adf import AdfHarvester
from .powerbi import PowerBiHarvester
from .fabric_pipeline import FabricPipelineHarvester
from .dataflow_gen2 import DataflowGen2Harvester
from .mssql_live import MssqlLiveHarvester
from .postgres_live import PostgresLiveHarvester
from .cosmos_live import CosmosLiveHarvester
from .oracle_live import OracleLiveHarvester
from .databricks_live import DatabricksLiveHarvester
from .declared import DeclaredEdgesHarvester

HARVESTERS: list[type[Harvester]] = [
    TsqlHarvester,
    NotebookHarvester,
    AdfHarvester,
    PowerBiHarvester,
    FabricPipelineHarvester,
    DataflowGen2Harvester,
]

# Live harvesters that require external DB connections. The cloud-tier
# validation runner (tests/run_cloud_validation.py) wires these up explicitly
# instead of running them on every scheduled harvest.
LIVE_HARVESTERS: list[type[Harvester]] = [
    MssqlLiveHarvester,
    PostgresLiveHarvester,
    CosmosLiveHarvester,
    OracleLiveHarvester,
    DatabricksLiveHarvester,
    DeclaredEdgesHarvester,
]

__all__ = ["Harvester", "HARVESTERS"] + [h.__name__ for h in HARVESTERS]
