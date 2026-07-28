"""Column-level lineage extraction via sqlglot.lineage.

Returns a list of (source_table_qname, source_col, target_col) tuples for one
SELECT/CREATE VIEW DDL, given a schema dict shaped as:

    {
      "<src_schema>.<src_table>": ["col1", "col2", ...],
      "another_table": ["x", "y"],
    }

Used by mssql_live, postgres_live, databricks_live so column tracking logic
lives in one place.
"""
from __future__ import annotations
from typing import Callable

import sqlglot
from sqlglot import exp
from sqlglot.lineage import lineage as sqlglot_lineage


ColumnEdge = tuple[str, str, str]  # (source_table_qname, source_col, target_col)


def _output_columns(parsed: exp.Expression) -> list[str]:
    """Return the projected output column names from a SELECT / CREATE VIEW."""
    select = parsed.find(exp.Select)
    if select is None:
        return []
    cols: list[str] = []
    for proj in select.expressions or []:
        # SELECT * — sqlglot represents this as exp.Star; we can't track it
        # column-by-column without expanding, so skip and the caller falls
        # back to table-level edges.
        if isinstance(proj, exp.Star):
            return ["*"]
        # `alias` if present, else last token of the column reference
        name = proj.alias_or_name
        if name:
            cols.append(name)
    return cols


def _nest_schema(flat: dict[str, list[str]]) -> dict:
    """Convert `{"schema.table": [cols]}` into the nested form sqlglot wants:
    `{"schema": {"table": {"col": "UNKNOWN", ...}}}`.

    Unqualified keys (no dot) become top-level table entries.
    """
    nested: dict = {}
    for key, cols in flat.items():
        col_map = {c: "UNKNOWN" for c in cols}
        if "." in key:
            schema_name, table_name = key.split(".", 1)
            nested.setdefault(schema_name, {})[table_name] = col_map
        else:
            nested[key] = col_map
    return nested


def extract_column_edges(
    ddl: str,
    *,
    dialect: str,
    default_schema: str,
    schema: dict[str, list[str]],
    qname_for: Callable[[str, str], str],
) -> tuple[list[ColumnEdge], list[str]]:
    """Parse `ddl` and return (column_edges, unknown_output_cols).

    `qname_for(src_schema, src_table) -> source_table_qname` produces the
    fully-qualified source-table identifier the caller expects to see in the
    resulting edges.

    Returns ([], ["*"]) when the view uses SELECT *  — caller should fall back
    to a table-level edge.
    """
    try:
        parsed = sqlglot.parse_one(ddl, read=dialect)
    except Exception:
        return [], []
    out_cols = _output_columns(parsed)
    if out_cols == ["*"]:
        return [], ["*"]

    nested_schema = _nest_schema(schema)

    # Strip the CREATE wrapper — sqlglot.lineage wants a bare SELECT.
    select_expr = parsed.find(exp.Select)
    if select_expr is None:
        return [], []
    sql_only = select_expr.sql(dialect=dialect)

    column_edges: list[ColumnEdge] = []
    unknown: list[str] = []

    for out_col in out_cols:
        try:
            node = sqlglot_lineage(
                out_col, sql=sql_only, schema=nested_schema, dialect=dialect
            )
        except Exception:
            unknown.append(out_col)
            continue
        for leaf in _walk_leaves(node):
            tbl = _leaf_table(leaf)
            col = _leaf_column(leaf)
            if not tbl or not col:
                continue
            parts = tbl.split(".")
            if len(parts) >= 2:
                src_schema, src_table = parts[-2], parts[-1]
            else:
                src_schema, src_table = default_schema, parts[-1]
            src_qname = qname_for(src_schema, src_table)
            column_edges.append((src_qname, col, out_col))
    return column_edges, unknown


def _walk_leaves(node):
    """Yield only the leaf nodes of a sqlglot lineage Node tree."""
    if not node.downstream:
        yield node
        return
    for child in node.downstream:
        yield from _walk_leaves(child)


def _leaf_table(leaf) -> str | None:
    """Return 'schema.table' for a lineage leaf, if it resolves to a Table."""
    src = getattr(leaf, "source", None)
    if isinstance(src, exp.Table):
        # Build "[db.]name" directly — don't use sql() because it includes the
        # alias and quoting that we don't want in the qname key.
        parts = [p for p in (src.db, src.name) if p]
        if parts:
            return ".".join(parts)
    expr = getattr(leaf, "expression", None)
    if isinstance(expr, exp.Column) and expr.table:
        if expr.db:
            return f"{expr.db}.{expr.table}"
        return expr.table
    return None


def _leaf_column(leaf) -> str | None:
    expr = getattr(leaf, "expression", None)
    if isinstance(expr, exp.Column):
        return expr.name
    name = getattr(leaf, "name", None)
    if name and "." in name:
        return name.split(".")[-1]
    return name
