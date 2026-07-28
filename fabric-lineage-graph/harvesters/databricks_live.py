"""Live harvester for Azure Databricks (Unity Catalog OR hive_metastore).

Queries the SQL Warehouse for view definitions via the Statement Execution API
(Entra OAuth, no PAT), parses each with sqlglot (databricks dialect), and emits
one LineageEdge per (upstream_table -> view).

Requires .env.cloud to contain:
  DATABRICKS_HOST              e.g. adb-xxxxx.azuredatabricks.net
  DATABRICKS_WAREHOUSE_ID      from seed_databricks.py
  DATABRICKS_CATALOG           default: hive_metastore
  DATABRICKS_SCHEMA            default: iot
"""
from __future__ import annotations
import os
import time
import json
from collections.abc import Iterable

import requests
import sqlglot
from sqlglot import exp
from azure.identity import DefaultAzureCredential

from common.schema import LineageEdge
from common.column_lineage import extract_column_edges
from ._schema_bootstrap import fetch_databricks_columns
from .base import Harvester

AAD_DATABRICKS_RESOURCE_ID = "2ff814a6-3304-4ab8-85cb-cd0e6f879c1d"


def _qname(host: str, catalog: str, schema: str, name: str) -> str:
    return f"databricks://{host}/{catalog}/{schema}/{name}"


class DatabricksLiveHarvester(Harvester):
    name = "databricks_live"

    def __init__(
        self,
        host: str | None = None,
        warehouse_id: str | None = None,
        catalog: str | None = None,
        schema: str | None = None,
    ) -> None:
        self.host = (host or os.environ.get("DATABRICKS_HOST", "")).rstrip("/")
        self.warehouse_id = warehouse_id or os.environ.get("DATABRICKS_WAREHOUSE_ID", "")
        self.catalog = catalog or os.environ.get("DATABRICKS_CATALOG", "hive_metastore")
        self.schema = schema or os.environ.get("DATABRICKS_SCHEMA", "iot")
        self._token: str | None = None

    def _base(self) -> str:
        return self.host if self.host.startswith("http") else f"https://{self.host}"

    def _ensure_token(self) -> str:
        if self._token is None:
            cred = DefaultAzureCredential(exclude_interactive_browser_credential=False)
            self._token = cred.get_token(f"{AAD_DATABRICKS_RESOURCE_ID}/.default").token
        return self._token

    def _exec(self, statement: str) -> list[list[str]]:
        headers = {"Authorization": f"Bearer {self._ensure_token()}"}
        body = {
            "warehouse_id": self.warehouse_id,
            "statement": statement,
            "wait_timeout": "30s",
            "format": "JSON_ARRAY",
            "disposition": "INLINE",
        }
        r = requests.post(
            f"{self._base()}/api/2.0/sql/statements", headers=headers, json=body, timeout=60
        )
        r.raise_for_status()
        res = r.json()
        sid = res.get("statement_id")
        state = res.get("status", {}).get("state")
        while state in ("PENDING", "RUNNING"):
            time.sleep(1.5)
            g = requests.get(
                f"{self._base()}/api/2.0/sql/statements/{sid}",
                headers=headers, timeout=30,
            )
            g.raise_for_status()
            res = g.json()
            state = res.get("status", {}).get("state")
        if state != "SUCCEEDED":
            raise RuntimeError(f"databricks_live SQL {state}: {json.dumps(res)[:300]}")
        return ((res.get("result") or {}).get("data_array")) or []

    def harvest(self) -> Iterable[LineageEdge]:
        if not (self.host and self.warehouse_id):
            return
        columns_by_table = fetch_databricks_columns(self._exec, self.catalog, self.schema)
        rows = self._exec(f"SHOW VIEWS IN {self.catalog}.{self.schema}")
        # SHOW VIEWS returns columns [namespace, viewName, isTemporary].
        for row in rows:
            view_name = row[1] if len(row) > 1 else None
            if not view_name:
                continue
            qualified = f"{self.catalog}.{self.schema}.{view_name}"
            ddl_rows = self._exec(f"SHOW CREATE TABLE {qualified}")
            if not ddl_rows or not ddl_rows[0]:
                continue
            ddl = ddl_rows[0][0]
            yield from self._parse(view_name, ddl, columns_by_table)

    def _parse(self, view_name: str, ddl: str,
               columns_by_table: dict[str, list[str]]) -> Iterable[LineageEdge]:
        try:
            parsed = sqlglot.parse_one(ddl, dialect="databricks")
        except Exception as exc:
            print(f"  [warn] databricks_live sqlglot failed for {view_name}: {exc}")
            return
        select = parsed.find(exp.Select)
        if select is None:
            return
        tgt = _qname(self.host, self.catalog, self.schema, view_name)

        col_edges, unknown_cols = extract_column_edges(
            ddl,
            dialect="databricks",
            default_schema=self.schema,
            schema=columns_by_table,
            qname_for=lambda s, t: _qname(self.host, self.catalog, s, t),
        )
        cols_by_source: dict[str, list[tuple[str, str]]] = {}
        for src_qname, src_col, tgt_col in col_edges:
            cols_by_source.setdefault(src_qname, []).append((src_col, tgt_col))

        seen_sources = set()
        for src_tbl in select.find_all(exp.Table):
            src_catalog = (
                src_tbl.args["catalog"].name if src_tbl.args.get("catalog") else self.catalog
            )
            src_schema = src_tbl.args["db"].name if src_tbl.args.get("db") else self.schema
            src_name = src_tbl.name
            if not src_name:
                continue
            src = _qname(self.host, src_catalog, src_schema, src_name)
            if src == tgt or src in seen_sources:
                continue
            seen_sources.add(src)
            yield LineageEdge(
                source_qname=src,
                source_type="databricks_table",
                target_qname=tgt,
                target_type="databricks_view",
                process_name=f"databricks:view:{self.catalog}.{self.schema}.{view_name}:{src_catalog}.{src_schema}.{src_name}",
                process_type="databricks_view",
                artifact_ref=f"databricks://{self.host}/{self.catalog}/{self.schema}/{view_name}",
                columns=cols_by_source.get(src) or None,
                extra={
                    "warehouse_id": self.warehouse_id,
                    **({"unknown_columns": unknown_cols} if unknown_cols else {}),
                },
            )
