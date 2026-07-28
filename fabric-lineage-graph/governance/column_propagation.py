"""Per-column sensitivity propagation, complementing label_propagation.propagate.

Inputs:
  * NetworkX MultiDiGraph produced by graph.build_graph (edges may carry
    a ``columns`` list of (src_col, tgt_col) pairs and nodes a ``columns``
    attribute).
  * `column_classifications`: dict[(node_qname, column_name), list[classification]].
    Tip: pass `flatten_column_classifications(seed_dict)` to convert a nested
    structure into the flat form this function expects.
  * `policy`: loaded sensitivity-labels.yml.

Returns:
    dict[(node_qname, column_name), label_name]

Algorithm: build a column-DAG `(asset, col) -> (asset, col)` from edge
``columns`` lists; for nodes whose edges have no column info, fall through to
the asset-level propagated label so downstream columns inherit something sane.
"""
from __future__ import annotations
from typing import Any

import networkx as nx

from .label_propagation import _own_label, _priority


ColumnKey = tuple[str, str]


def flatten_column_classifications(
    nested: dict[str, dict[str, list[str]]],
) -> dict[ColumnKey, list[str]]:
    out: dict[ColumnKey, list[str]] = {}
    for asset, cols in nested.items():
        for col, cls in cols.items():
            out[(asset, col)] = list(cls)
    return out


def _column_edges(graph: nx.MultiDiGraph) -> list[tuple[ColumnKey, ColumnKey]]:
    edges: list[tuple[ColumnKey, ColumnKey]] = []
    for src, tgt, data in graph.edges(data=True):
        cols = data.get("columns") or []
        for pair in cols:
            if len(pair) != 2:
                continue
            src_col, tgt_col = pair
            edges.append(((src, src_col), (tgt, tgt_col)))
    return edges


def propagate_columns(
    graph: nx.MultiDiGraph,
    column_classifications: dict[ColumnKey, list[str]],
    asset_labels: dict[str, str],
    policy: dict[str, Any],
    default_label: str = "Internal",
) -> dict[ColumnKey, str]:
    """Propagate sensitivity at the column granularity.

    Columns inherit the MAX-priority label of:
      * their own classifications (via policy.auto_label_rules), OR
      * any upstream column's label, OR
      * the asset-level label of their owning node (fallback).
    """
    rules = policy.get("auto_label_rules", [])
    cg = nx.DiGraph()

    # Seed the graph with every (asset, column) we know about — from the
    # graph's node `columns` attribute, the edge column lists, and the
    # explicit classifications.
    for node, data in graph.nodes(data=True):
        for col in data.get("columns") or []:
            cg.add_node((node, col))
    for key in column_classifications:
        cg.add_node(key)
    for (s, t) in _column_edges(graph):
        cg.add_node(s); cg.add_node(t)
        cg.add_edge(s, t)

    # Own label per column.
    own: dict[ColumnKey, str] = {}
    for key in cg.nodes():
        asset, _col = key
        seed = asset_labels.get(asset, default_label)
        cls = column_classifications.get(key, [])
        own[key] = _own_label(cls, rules, seed)
        # Asset label dominates if it's stricter than what classifications imply.
        if _priority(policy, seed) > _priority(policy, own[key]):
            own[key] = seed

    try:
        order = list(nx.topological_sort(cg))
    except nx.NetworkXUnfeasible:
        order = list(cg.nodes())

    propagated = dict(own)
    changed = True
    iterations = 0
    while changed and iterations < len(order) + 5:
        changed = False
        for node in order:
            best = propagated[node]
            best_prio = _priority(policy, best)
            for pred in cg.predecessors(node):
                pred_lbl = propagated.get(pred, default_label)
                pred_prio = _priority(policy, pred_lbl)
                if pred_prio > best_prio:
                    best, best_prio = pred_lbl, pred_prio
            if best != propagated[node]:
                propagated[node] = best
                changed = True
        iterations += 1

    return propagated


def column_labels_for_asset(
    column_labels: dict[ColumnKey, str], asset: str
) -> dict[str, str]:
    return {col: lbl for (a, col), lbl in column_labels.items() if a == asset}
