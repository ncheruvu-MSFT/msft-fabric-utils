"""Tests for the column-level path tracer and repo scan."""
from __future__ import annotations

import pathlib

from common.schema import LineageEdge
from graph.column_path import (
    build_column_graph,
    col_id,
    resolve_column_node,
    trace_column,
)
from harvesters.scan_repo import scan_repo, to_app_graph


def _edge(src_q, tgt_q, cols, name="p"):
    return LineageEdge(
        source_qname=src_q, source_type="t",
        target_qname=tgt_q, target_type="t",
        process_name=name, process_type="spark_write",
        artifact_ref="a", columns=cols,
    )


def test_trace_walks_upstream_and_downstream():
    edges = [
        _edge("a", "b", [("x", "x")], "load"),
        _edge("b", "c", [("x", "y")], "rename"),
        _edge("c", "d", [("y", "z")], "agg"),
    ]
    g = build_column_graph(edges)
    res = trace_column(g, col_id("b", "x"))
    cols = res.columns
    assert col_id("a", "x") in cols      # upstream origin
    assert col_id("c", "y") in cols      # downstream
    assert col_id("d", "z") in cols      # downstream (transitive)


def test_resolve_prefers_exact_table_over_substring():
    edges = [
        _edge("src", "spark://gold.fact_sales", [("a", "NetAmount")]),
        _edge("src", "spark://gold.fact_sales_secured", [("a", "netamount")]),
    ]
    g = build_column_graph(edges)
    node = resolve_column_node(g, "gold.fact_sales.NetAmount")
    assert node == col_id("spark://gold.fact_sales", "NetAmount")


def test_scan_repo_sample_traces_net_amount():
    root = pathlib.Path(__file__).resolve().parents[1] / "samples" / "complex" / "gold"
    edges = scan_repo(root)
    g = build_column_graph(edges)
    node = resolve_column_node(g, "gold.fact_sales.NetAmount")
    assert node is not None
    res = trace_column(g, node)
    upstream_cols = {c for e in res.upstream for c in (e.src, e.dst)}
    assert col_id("spark://silver.orders_valid", "Amount") in upstream_cols
    assert col_id("spark://silver.orders_valid", "Discount") in upstream_cols


def test_app_graph_export_shape():
    edges = [_edge("spark://silver.orders", "spark://gold.fact",
                   [("Amount", "Net")], "spark:nb:cell:saveAsTable:gold.fact")]
    payload = to_app_graph(edges)
    assert "assets" in payload and "edges" in payload
    assert {"from", "to", "transform"} <= set(payload["edges"][0])
    assert payload["assets"]["spark://gold.fact"]["type"] == "gold"
    assert payload["assets"]["spark://silver.orders"]["type"] == "silver"
