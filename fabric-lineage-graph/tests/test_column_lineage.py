"""Column-level lineage extractor tests (no live DBs).

Each test feeds a synthetic DDL + schema dict into common.column_lineage and
verifies the extracted (src_table, src_col, tgt_col) triples.
"""
from __future__ import annotations

import pytest

from common.column_lineage import extract_column_edges


def _q(schema: str, table: str) -> str:
    return f"{schema}.{table}"


SCHEMA_TSQL = {
    "silver.customer_360": ["customer_id", "email", "phone", "ltv"],
}


def test_tsql_simple_projection_emits_column_edges():
    ddl = (
        "CREATE VIEW gold.customer_revenue_mart AS "
        "SELECT customer_id, email, ltv FROM silver.customer_360"
    )
    edges, unknown = extract_column_edges(
        ddl, dialect="tsql", default_schema="gold",
        schema=SCHEMA_TSQL, qname_for=_q,
    )
    by_pair = {(s, src, tgt) for (s, src, tgt) in edges}
    assert ("silver.customer_360", "customer_id", "customer_id") in by_pair
    assert ("silver.customer_360", "email", "email") in by_pair
    assert ("silver.customer_360", "ltv", "ltv") in by_pair
    assert unknown == []


def test_tsql_alias_is_tracked_as_target_column():
    ddl = (
        "CREATE VIEW gold.v AS "
        "SELECT customer_id AS cust_id, email AS contact_email "
        "FROM silver.customer_360"
    )
    edges, _ = extract_column_edges(
        ddl, dialect="tsql", default_schema="gold",
        schema=SCHEMA_TSQL, qname_for=_q,
    )
    out_cols = {tgt for (_s, _src, tgt) in edges}
    assert {"cust_id", "contact_email"} <= out_cols


def test_select_star_returns_no_column_edges_only_marker():
    ddl = "CREATE VIEW gold.v AS SELECT * FROM silver.customer_360"
    edges, unknown = extract_column_edges(
        ddl, dialect="tsql", default_schema="gold",
        schema=SCHEMA_TSQL, qname_for=_q,
    )
    assert edges == []
    assert unknown == ["*"]


def test_postgres_simple_view():
    schema = {"public.orders": ["id", "customer_id", "total"]}
    ddl = "SELECT id, customer_id, total FROM public.orders"
    edges, _ = extract_column_edges(
        ddl, dialect="postgres", default_schema="public",
        schema=schema, qname_for=_q,
    )
    pairs = {(s, src, tgt) for (s, src, tgt) in edges}
    assert ("public.orders", "id", "id") in pairs
    assert ("public.orders", "customer_id", "customer_id") in pairs


def test_databricks_select_with_alias():
    schema = {"iot.devices_raw": ["device_id", "tenant_id", "reading"]}
    ddl = (
        "CREATE VIEW iot.devices_clean AS "
        "SELECT device_id, tenant_id AS owner_id FROM iot.devices_raw"
    )
    edges, _ = extract_column_edges(
        ddl, dialect="databricks", default_schema="iot",
        schema=schema, qname_for=_q,
    )
    pairs = {(s, src, tgt) for (s, src, tgt) in edges}
    assert ("iot.devices_raw", "device_id", "device_id") in pairs
    assert ("iot.devices_raw", "tenant_id", "owner_id") in pairs


def test_unparseable_ddl_returns_empty():
    edges, unknown = extract_column_edges(
        "this is not sql", dialect="tsql", default_schema="x",
        schema={}, qname_for=_q,
    )
    assert edges == []
    assert unknown == []
