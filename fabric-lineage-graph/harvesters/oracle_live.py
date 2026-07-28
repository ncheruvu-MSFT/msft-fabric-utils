"""Oracle live lineage harvester (BYO instance).

Reads view DDL from `ALL_VIEWS` and parses with sqlglot (oracle dialect).

Auth: Basic Oracle credentials via ORACLE_USER / ORACLE_PWD env vars (Oracle
on Azure VM / OCI / on-prem). For Oracle Database@Azure with Entra,
substitute with the token-based connection per Oracle's wallet config.
"""
from __future__ import annotations
import os
from collections.abc import Iterable

import sqlglot
from sqlglot import exp

from common.schema import LineageEdge
from .base import Harvester


def _qname(dsn: str, schema: str, name: str) -> str:
    return f"oracle://{dsn}/{schema}/{name}"


def _parse_view(dsn: str, schema: str, name: str, ddl: str) -> list[LineageEdge]:
    edges: list[LineageEdge] = []
    try:
        parsed = sqlglot.parse_one(ddl, read="oracle")
    except Exception:
        return edges
    select = parsed if isinstance(parsed, exp.Select) else parsed.find(exp.Select)
    if select is None:
        return edges
    tgt = _qname(dsn, schema, name)
    for src_tbl in select.find_all(exp.Table):
        src_schema = (src_tbl.db or schema).upper()
        src_name = (src_tbl.name or "").upper()
        if not src_name:
            continue
        src = _qname(dsn, src_schema, src_name)
        if src == tgt:
            continue
        edges.append(LineageEdge(
            source_qname=src,
            source_type="oracle_table",
            target_qname=tgt,
            target_type="oracle_view",
            process_name=f"oracle:view:{schema}.{name}:{src_schema}.{src_name}",
            process_type="tsql_view",
            artifact_ref=f"all_views://{dsn}/{schema}.{name}",
        ))
    return edges


class OracleLiveHarvester(Harvester):
    name = "oracle_live"

    def __init__(self, dsn: str | None = None, user: str | None = None,
                 password: str | None = None,
                 schemas: list[str] | None = None) -> None:
        self.dsn = dsn or os.environ.get("ORACLE_DSN", "")
        self.user = user or os.environ.get("ORACLE_USER", "system")
        self.password = password or os.environ.get("ORACLE_PWD", "")
        # Restrict to the sample schemas by default; otherwise the harvester
        # would walk every system view.
        env_schemas = os.environ.get("ORACLE_SCHEMAS", "SCM")
        self.schemas = schemas or [s.strip().upper() for s in env_schemas.split(",") if s.strip()]

    def harvest(self) -> Iterable[LineageEdge]:
        if not self.dsn:
            return
        try:
            import oracledb  # type: ignore
        except ImportError:
            print("oracle_live: oracledb not installed; skipping")
            return
        placeholders = ",".join(f":s{i}" for i, _ in enumerate(self.schemas))
        binds = {f"s{i}": s for i, s in enumerate(self.schemas)}
        with oracledb.connect(user=self.user, password=self.password, dsn=self.dsn) as cx:
            with cx.cursor() as cur:
                cur.execute(
                    f"SELECT owner, view_name, text "
                    f"FROM all_views WHERE owner IN ({placeholders})",
                    binds,
                )
                for schema, name, ddl in cur.fetchall():
                    if hasattr(ddl, "read"):
                        ddl = ddl.read()
                    full_ddl = f"CREATE VIEW {schema}.{name} AS {ddl}"
                    yield from _parse_view(self.dsn, schema, name, full_ddl)
