"""Azure SQL / SQL Server / Synapse-Serverless live lineage harvester.

Reads view + procedure definitions from `sys.sql_modules`, parses each with
sqlglot, and emits LineageEdges with column-level lineage when sqlglot can
resolve it.

Auth: pyodbc with an AAD access token via SQL_COPT_SS_ACCESS_TOKEN — works
on ODBC Driver 17 and 18 (Entra-only, MCAPS compliant).
"""
from __future__ import annotations
import os
from collections.abc import Iterable

import sqlglot
from sqlglot import exp

from common.schema import LineageEdge
from common.column_lineage import extract_column_edges
from ._schema_bootstrap import fetch_mssql_columns
from .base import Harvester


def _pick_driver(pyodbc_mod) -> str:
    drivers = pyodbc_mod.drivers()
    for d in ("ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server"):
        if d in drivers:
            return d
    raise RuntimeError(f"No supported SQL Server ODBC driver. Installed: {drivers}")


def _conn_str(driver: str, server_fqdn: str, database: str) -> str:
    trust = "yes" if "17" in driver else "no"
    return (
        f"Driver={{{driver}}};"
        f"Server=tcp:{server_fqdn},1433;Database={database};"
        f"Encrypt=yes;TrustServerCertificate={trust};Connection Timeout=30;"
    )


SQL_COPT_SS_ACCESS_TOKEN = 1256


def _aad_token_struct() -> bytes:
    import struct
    from azure.identity import DefaultAzureCredential
    tok = DefaultAzureCredential().get_token("https://database.windows.net/.default").token
    b = tok.encode("utf-16-le")
    return struct.pack(f"=i{len(b)}s", len(b), b)


def _qname(server: str, db: str, schema: str, name: str) -> str:
    return f"mssql://{server}/{db}/{schema}/{name}"


def _parse_view(server: str, db: str, schema: str, name: str,
                ddl: str, columns_by_table: dict[str, list[str]],
                view_type: str = "azure_sql_view") -> list[LineageEdge]:
    edges: list[LineageEdge] = []
    try:
        parsed = sqlglot.parse_one(ddl, read="tsql")
    except Exception:
        return edges
    select = parsed.find(exp.Select)
    if select is None:
        return edges
    tgt = _qname(server, db, schema, name)

    # Column-level pass: group sqlglot lineage results by source table so each
    # (source -> target) edge carries the list of (src_col, tgt_col) pairs.
    col_edges, unknown_cols = extract_column_edges(
        ddl,
        dialect="tsql",
        default_schema=schema,
        schema=columns_by_table,
        qname_for=lambda s, t: _qname(server, db, s, t),
    )
    cols_by_source: dict[str, list[tuple[str, str]]] = {}
    for src_qname, src_col, tgt_col in col_edges:
        cols_by_source.setdefault(src_qname, []).append((src_col, tgt_col))

    seen_sources = set()
    for src_tbl in select.find_all(exp.Table):
        src_schema = src_tbl.db or schema
        src_name = src_tbl.name
        if not src_name:
            continue
        src = _qname(server, db, src_schema, src_name)
        if src == tgt or src in seen_sources:
            continue
        seen_sources.add(src)
        edges.append(LineageEdge(
            source_qname=src,
            source_type="azure_sql_table",
            target_qname=tgt,
            target_type=view_type,
            process_name=f"tsql:view:{schema}.{name}:{src_schema}.{src_name}",
            process_type="tsql_view",
            artifact_ref=f"sys.sql_modules://{server}/{db}/{schema}.{name}",
            columns=cols_by_source.get(src) or None,
            extra={"unknown_columns": unknown_cols} if unknown_cols else {},
        ))
    return edges


class MssqlLiveHarvester(Harvester):
    name = "mssql_live"

    def __init__(self, server_fqdn: str | None = None, database: str | None = None) -> None:
        self.server = server_fqdn or os.environ.get("SQL_SERVER_FQDN", "")
        self.database = database or os.environ.get("SQL_DATABASE", "")

    def harvest(self) -> Iterable[LineageEdge]:
        if not (self.server and self.database):
            return
        try:
            import pyodbc  # type: ignore
        except ImportError:
            print("mssql_live: pyodbc not installed; skipping")
            return
        driver = _pick_driver(pyodbc)
        with pyodbc.connect(
            _conn_str(driver, self.server, self.database),
            autocommit=True,
            attrs_before={SQL_COPT_SS_ACCESS_TOKEN: _aad_token_struct()},
        ) as cx:
            cur = cx.cursor()
            columns_by_table = fetch_mssql_columns(cur)
            cur.execute(
                "SELECT s.name AS schema_name, o.name AS object_name, "
                "       m.definition, o.type_desc "
                "FROM sys.sql_modules m "
                "JOIN sys.objects o ON o.object_id = m.object_id "
                "JOIN sys.schemas s ON s.schema_id = o.schema_id "
                "WHERE o.type IN ('V','P','TF','IF') "
                "  AND s.name NOT IN ('sys','INFORMATION_SCHEMA')"
            )
            for row in cur.fetchall():
                schema, name, ddl, type_desc = row
                view_type = "azure_sql_view" if type_desc == "VIEW" else "azure_sql_procedure"
                yield from _parse_view(self.server, self.database, schema, name, ddl,
                                       columns_by_table, view_type)
