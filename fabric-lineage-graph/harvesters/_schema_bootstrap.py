"""Catalog-introspection helpers used by the live harvesters to build
column-level lineage.

Each helper returns:

    {
      "<src_schema>.<src_table>": ["col1", "col2", ...],
    }

Cheap enough to call on every harvest — these catalog views are tiny.
"""
from __future__ import annotations


def fetch_mssql_columns(cursor, schemas_to_include: list[str] | None = None) -> dict[str, list[str]]:
    """sys.columns / sys.tables / sys.views / sys.schemas."""
    sql = (
        "SELECT s.name AS schema_name, o.name AS object_name, c.name AS column_name "
        "FROM sys.columns c "
        "JOIN sys.objects o ON o.object_id = c.object_id "
        "JOIN sys.schemas s ON s.schema_id = o.schema_id "
        "WHERE o.type IN ('U','V') "
        "  AND s.name NOT IN ('sys','INFORMATION_SCHEMA') "
        "ORDER BY s.name, o.name, c.column_id"
    )
    cursor.execute(sql)
    out: dict[str, list[str]] = {}
    for schema, obj, col in cursor.fetchall():
        if schemas_to_include and schema not in schemas_to_include:
            continue
        out.setdefault(f"{schema}.{obj}", []).append(col)
    return out


def fetch_postgres_columns(cursor) -> dict[str, list[str]]:
    sql = (
        "SELECT table_schema, table_name, column_name "
        "FROM information_schema.columns "
        "WHERE table_schema NOT IN ('pg_catalog','information_schema') "
        "ORDER BY table_schema, table_name, ordinal_position"
    )
    cursor.execute(sql)
    out: dict[str, list[str]] = {}
    for schema, obj, col in cursor.fetchall():
        out.setdefault(f"{schema}.{obj}", []).append(col)
    return out


def fetch_databricks_columns(
    exec_sql,  # (statement: str) -> list[list[str]]
    catalog: str,
    schema: str,
) -> dict[str, list[str]]:
    """Reads `<catalog>.information_schema.columns` filtered by schema.

    `exec_sql` is the DatabricksLiveHarvester._exec callable so we don't
    re-implement the Statement Execution API plumbing.
    """
    rows = exec_sql(
        f"SELECT table_name, column_name FROM {catalog}.information_schema.columns "
        f"WHERE table_schema = '{schema}' "
        f"ORDER BY table_name, ordinal_position"
    )
    out: dict[str, list[str]] = {}
    for row in rows:
        if len(row) < 2:
            continue
        table_name, column_name = row[0], row[1]
        key = f"{schema}.{table_name}"
        out.setdefault(key, []).append(column_name)
    return out
