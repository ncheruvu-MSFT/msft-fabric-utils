"""Azure Database for PostgreSQL (Flex / Single) live lineage harvester.

Reads view definitions from `pg_views` + dependency graph from
`pg_depend`/`pg_rewrite`, parses each with sqlglot (postgres dialect), and
emits one LineageEdge per (target_view, source_relation) pair.

Auth: DefaultAzureCredential issues an AAD access token used as the Postgres
password (Entra-only — MCAPS compliant). Requires the `azure_pg_admin` or an
inherited group membership.
"""
from __future__ import annotations
import os
from collections.abc import Iterable

import sqlglot
from sqlglot import exp

from common.schema import LineageEdge
from common.column_lineage import extract_column_edges
from ._schema_bootstrap import fetch_postgres_columns
from .base import Harvester


def _qname(host: str, db: str, schema: str, name: str) -> str:
    return f"postgres://{host}/{db}/{schema}/{name}"


def _parse_view(host: str, db: str, schema: str, name: str,
                ddl: str, columns_by_table: dict[str, list[str]]) -> list[LineageEdge]:
    edges: list[LineageEdge] = []
    try:
        parsed = sqlglot.parse_one(ddl, read="postgres")
    except Exception:
        return edges
    select = parsed if isinstance(parsed, exp.Select) else parsed.find(exp.Select)
    if select is None:
        return edges
    tgt = _qname(host, db, schema, name)

    col_edges, unknown_cols = extract_column_edges(
        ddl,
        dialect="postgres",
        default_schema=schema,
        schema=columns_by_table,
        qname_for=lambda s, t: _qname(host, db, s, t),
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
        src = _qname(host, db, src_schema, src_name)
        if src == tgt or src in seen_sources:
            continue
        seen_sources.add(src)
        edges.append(LineageEdge(
            source_qname=src,
            source_type="azure_postgresql_table",
            target_qname=tgt,
            target_type="azure_postgresql_view",
            process_name=f"pgsql:view:{schema}.{name}:{src_schema}.{src_name}",
            process_type="tsql_view",
            artifact_ref=f"pg_views://{host}/{db}/{schema}.{name}",
            columns=cols_by_source.get(src) or None,
            extra={"unknown_columns": unknown_cols} if unknown_cols else {},
        ))
    return edges


class PostgresLiveHarvester(Harvester):
    name = "postgres_live"

    def __init__(self, host: str | None = None, database: str | None = None,
                 user: str | None = None) -> None:
        self.host = host or os.environ.get("PG_SERVER_FQDN", "")
        self.database = database or os.environ.get("PG_DATABASE", "")
        self.user = user or os.environ.get("PG_ADMIN_LOGIN", "")

    def harvest(self) -> Iterable[LineageEdge]:
        if not (self.host and self.database and self.user):
            return
        try:
            import psycopg  # type: ignore
        except ImportError:
            print("postgres_live: psycopg not installed; skipping")
            return
        from azure.identity import DefaultAzureCredential
        token = DefaultAzureCredential().get_token(
            "https://ossrdbms-aad.database.windows.net/.default"
        ).token
        dsn = (f"host={self.host} dbname={self.database} user={self.user} "
               f"password={token} sslmode=require")
        with psycopg.connect(dsn) as cx:
            with cx.cursor() as cur:
                columns_by_table = fetch_postgres_columns(cur)
                cur.execute(
                    "SELECT schemaname, viewname, definition "
                    "FROM pg_views "
                    "WHERE schemaname NOT IN ('pg_catalog','information_schema')"
                )
                for schema, name, ddl in cur.fetchall():
                    yield from _parse_view(self.host, self.database, schema, name, ddl,
                                           columns_by_table)
