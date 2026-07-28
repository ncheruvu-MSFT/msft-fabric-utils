"""T-SQL harvester — column-level lineage via sqlglot.

Parses INSERT/MERGE/CTAS/CREATE VIEW statements and emits one LineageEdge per
target-table per source-table pair, with per-column mapping where derivable.

Sources covered:
  * Fabric Warehouse / SQL endpoint stored procedures and views
  * Azure SQL DB / MI .sql files in a repo path
  * Any .sql file passed on the CLI

Status: implemented for INSERT ... SELECT, SELECT INTO, CREATE [OR ALTER] VIEW.
MERGE and dynamic SQL are best-effort (sqlglot extracts source/target tables
but column mapping may be partial).
"""
from __future__ import annotations
import argparse
import pathlib
from collections.abc import Iterable

import sqlglot
from sqlglot import exp

from common.schema import LineageEdge
from .base import Harvester


def _qname(server: str, db: str, table: exp.Table) -> str:
    parts = [p for p in (table.catalog, table.db, table.name) if p]
    return f"mssql://{server}/{db}/" + "/".join(parts)


def _column_pairs(select: exp.Select) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for proj in select.expressions:
        alias = proj.alias_or_name
        col = proj.find(exp.Column)
        if col is not None and alias:
            pairs.append((col.name, alias))
    return pairs


def _edges_from_statement(stmt: exp.Expression, server: str, db: str,
                          artifact: str) -> Iterable[LineageEdge]:
    # INSERT INTO tgt SELECT ... FROM src
    if isinstance(stmt, exp.Insert) and isinstance(stmt.expression, exp.Select):
        tgt = stmt.this
        if isinstance(tgt, exp.Schema):
            tgt = tgt.this
        if not isinstance(tgt, exp.Table):
            return
        select = stmt.expression
        cols = _column_pairs(select)
        for src in select.find_all(exp.Table):
            if src is tgt:
                continue
            yield LineageEdge(
                source_qname=_qname(server, db, src),
                source_type="azure_sql_table",
                target_qname=_qname(server, db, tgt),
                target_type="azure_sql_table",
                process_name=f"tsql:insert:{tgt.name}:{src.name}",
                process_type="tsql_insert",
                artifact_ref=artifact,
                columns=cols or None,
                extra={"statement": "INSERT_SELECT"},
            )
        return

    # SELECT ... INTO tgt FROM src   (CTAS)
    if isinstance(stmt, exp.Select) and stmt.args.get("into"):
        tgt = stmt.args["into"].this
        if not isinstance(tgt, exp.Table):
            return
        cols = _column_pairs(stmt)
        for src in stmt.find_all(exp.Table):
            if src is tgt:
                continue
            yield LineageEdge(
                source_qname=_qname(server, db, src),
                source_type="azure_sql_table",
                target_qname=_qname(server, db, tgt),
                target_type="azure_sql_table",
                process_name=f"tsql:ctas:{tgt.name}:{src.name}",
                process_type="tsql_ctas",
                artifact_ref=artifact,
                columns=cols or None,
            )
        return

    # CREATE [OR ALTER] VIEW v AS SELECT ... FROM src
    if isinstance(stmt, exp.Create) and stmt.kind == "VIEW":
        tgt = stmt.this
        if isinstance(tgt, exp.Schema):
            tgt = tgt.this
        if not isinstance(tgt, exp.Table):
            return
        select = stmt.expression
        if not isinstance(select, exp.Select):
            return
        cols = _column_pairs(select)
        for src in select.find_all(exp.Table):
            if src is tgt:
                continue
            yield LineageEdge(
                source_qname=_qname(server, db, src),
                source_type="azure_sql_table",
                target_qname=_qname(server, db, tgt),
                target_type="azure_sql_table",
                process_name=f"tsql:view:{tgt.name}:{src.name}",
                process_type="tsql_view",
                artifact_ref=artifact,
                columns=cols or None,
            )
        return

    # MERGE INTO tgt USING src ...
    if isinstance(stmt, exp.Merge):
        tgt = stmt.this
        src = stmt.args.get("using")
        if isinstance(tgt, exp.Table) and isinstance(src, exp.Table):
            yield LineageEdge(
                source_qname=_qname(server, db, src),
                source_type="azure_sql_table",
                target_qname=_qname(server, db, tgt),
                target_type="azure_sql_table",
                process_name=f"tsql:merge:{tgt.name}:{src.name}",
                process_type="tsql_merge",
                artifact_ref=artifact,
                columns=None,
                extra={"statement": "MERGE"},
            )


def parse_sql_file(path: pathlib.Path, server: str = "unknown",
                   db: str = "unknown") -> list[LineageEdge]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    edges: list[LineageEdge] = []
    try:
        parsed = sqlglot.parse(text, read="tsql")
    except Exception:
        return edges
    for stmt in parsed:
        if stmt is None:
            continue
        edges.extend(_edges_from_statement(stmt, server, db, str(path)))
    return edges


class TsqlHarvester(Harvester):
    name = "tsql"

    def __init__(self, sql_root: str | pathlib.Path,
                 server: str = "unknown", database: str = "unknown") -> None:
        self.sql_root = pathlib.Path(sql_root)
        self.server = server
        self.database = database

    def harvest(self) -> Iterable[LineageEdge]:
        for sql_file in self.sql_root.rglob("*.sql"):
            yield from parse_sql_file(sql_file, self.server, self.database)


def _cli() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True, help="Directory containing .sql files")
    p.add_argument("--server", default="unknown")
    p.add_argument("--database", default="unknown")
    args = p.parse_args()
    h = TsqlHarvester(args.root, args.server, args.database)
    edges = list(h.harvest())
    print(f"Parsed {len(edges)} lineage edges from {args.root}")
    for e in edges[:10]:
        print(f"  {e.process_type:14} {e.source_qname} -> {e.target_qname}")


if __name__ == "__main__":
    _cli()
