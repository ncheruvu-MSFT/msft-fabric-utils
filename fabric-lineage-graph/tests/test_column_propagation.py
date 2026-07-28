"""Column-aware label propagation tests."""
from __future__ import annotations
import pathlib

import networkx as nx
import pytest

from graph.build_graph import build_graph
from common.schema import LineageEdge
from governance.label_propagation import propagate, load_policy
from governance.column_propagation import (
    propagate_columns,
    flatten_column_classifications,
    column_labels_for_asset,
)
from governance.dlp_gate import evaluate


POLICY = load_policy(
    pathlib.Path(__file__).resolve().parents[2]
    / "fabric-sdlc-governance" / "contracts" / "labels" / "sensitivity-labels.yml"
)


def _edge(src, src_cols, tgt, tgt_cols, columns=None):
    return LineageEdge(
        source_qname=src, source_type="azure_sql_table",
        target_qname=tgt, target_type="azure_sql_view",
        process_name=f"p:{src}:{tgt}", process_type="tsql_view",
        artifact_ref="x",
        columns=columns,
    )


def test_pii_column_propagates_only_to_downstream_columns_it_feeds():
    edges = [
        _edge(
            "raw.customers", ["customer_id", "email", "ltv"],
            "silver.customer_360", ["customer_id", "email", "ltv"],
            columns=[("customer_id", "customer_id"),
                     ("email", "email"), ("ltv", "ltv")],
        ),
        _edge(
            "silver.customer_360", [], "gold.revenue_mart", [],
            columns=[("customer_id", "customer_id"), ("ltv", "ltv")],  # email NOT propagated
        ),
    ]
    g = build_graph(edges)
    asset_labels = propagate(g, {}, POLICY)
    col_cls = flatten_column_classifications({
        "raw.customers": {"email": ["MICROSOFT.PERSONAL.EMAIL"]},
    })
    col_labels = propagate_columns(g, col_cls, asset_labels, POLICY)
    # The PII flows from raw.customers.email -> silver.customer_360.email
    assert col_labels[("raw.customers", "email")] == "Confidential-PII"
    assert col_labels[("silver.customer_360", "email")] == "Confidential-PII"
    # It does NOT flow to gold (no email edge) — gold columns stay at the
    # asset default.
    assert col_labels.get(("gold.revenue_mart", "customer_id")) != "Confidential-PII"
    assert col_labels.get(("gold.revenue_mart", "ltv")) != "Confidential-PII"


def test_column_classification_uses_max_priority():
    edges = [_edge(
        "src.t", ["a", "b"], "tgt.v", ["a", "b"],
        columns=[("a", "a"), ("b", "b")],
    )]
    g = build_graph(edges)
    asset_labels = propagate(g, {}, POLICY)
    col_cls = flatten_column_classifications({
        "src.t": {
            "a": ["MICROSOFT.PERSONAL.EMAIL"],          # -> Confidential-PII
            "b": ["HR_COMPENSATION"],                    # -> Highly-Confidential-Restricted
        },
    })
    col_labels = propagate_columns(g, col_cls, asset_labels, POLICY)
    assert col_labels[("src.t", "a")] == "Confidential-PII"
    assert col_labels[("src.t", "b")] == "Highly-Confidential-Restricted"
    assert col_labels[("tgt.v", "a")] == "Confidential-PII"
    assert col_labels[("tgt.v", "b")] == "Highly-Confidential-Restricted"


def test_column_labels_for_asset_filters_correctly():
    col_labels = {
        ("a.t", "x"): "Internal",
        ("a.t", "y"): "Confidential-PII",
        ("b.v", "x"): "Public",
    }
    assert column_labels_for_asset(col_labels, "a.t") == {
        "x": "Internal", "y": "Confidential-PII",
    }
    assert column_labels_for_asset(col_labels, "b.v") == {"x": "Public"}


def test_column_level_dlp_blocks_pii_landing_in_public_column():
    edges = [_edge(
        "src.pii", ["email"], "pub.dest", ["email"],
        columns=[("email", "email")],
    )]
    g = build_graph(edges)
    asset_labels = propagate(g, {}, POLICY, seed_labels={"pub.dest": "Public"})
    col_cls = flatten_column_classifications({
        "src.pii": {"email": ["HR_COMPENSATION"]},
    })
    col_labels = propagate_columns(g, col_cls, asset_labels, POLICY)
    column_seed = {("pub.dest", "email"): "Public"}
    violations = evaluate(
        g, asset_labels, {"pub.dest": "Public"}, POLICY,
        column_labels=col_labels, column_seed_labels=column_seed,
    )
    rules = {v["rule"] for v in violations}
    assert "column_highly_confidential_to_public" in rules


def test_existing_per_asset_propagation_still_passes_with_column_extension():
    g = nx.MultiDiGraph()
    g.add_edge("src", "tgt", key="p")
    labels = propagate(g, {"src": ["MICROSOFT.PERSONAL.EMAIL"]}, POLICY)
    assert labels["tgt"] == "Confidential-PII"
