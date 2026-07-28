"""Build a NetworkX MultiDiGraph from the lineage edges table."""
from __future__ import annotations
from collections.abc import Iterable

import networkx as nx

from common.schema import LineageEdge


def build_graph(edges: Iterable[LineageEdge | dict]) -> nx.MultiDiGraph:
    g = nx.MultiDiGraph()
    # Per-node accumulated column sets, so a downstream node ends up with the
    # union of columns mentioned by any inbound edge.
    node_cols: dict[str, set[str]] = {}
    for e in edges:
        if isinstance(e, dict):
            src_q, src_t = e["source_qname"], e["source_type"]
            tgt_q, tgt_t = e["target_qname"], e["target_type"]
            pname, ptype = e["process_name"], e["process_type"]
            artifact = e.get("artifact_ref", "")
            cols = e.get("columns") or []
        else:
            src_q, src_t = e.source_qname, e.source_type
            tgt_q, tgt_t = e.target_qname, e.target_type
            pname, ptype = e.process_name, e.process_type
            artifact = e.artifact_ref
            cols = e.columns or []

        g.add_node(src_q, kind=src_t)
        g.add_node(tgt_q, kind=tgt_t)
        # Normalize column edges to tuples so dedup works.
        col_pairs: list[tuple[str, str]] = [tuple(c) for c in cols]  # type: ignore[arg-type]
        for src_col, tgt_col in col_pairs:
            node_cols.setdefault(src_q, set()).add(src_col)
            node_cols.setdefault(tgt_q, set()).add(tgt_col)
        g.add_edge(src_q, tgt_q, key=pname,
                   process_type=ptype, artifact=artifact, columns=col_pairs)

    for node, cols in node_cols.items():
        g.nodes[node]["columns"] = sorted(cols)
    return g


def upstream(g: nx.MultiDiGraph, node: str, depth: int = 3) -> nx.MultiDiGraph:
    nodes = {node}
    frontier = {node}
    for _ in range(depth):
        nxt = {p for n in frontier for p in g.predecessors(n)}
        nodes |= nxt
        frontier = nxt
    return g.subgraph(nodes).copy()


def downstream(g: nx.MultiDiGraph, node: str, depth: int = 3) -> nx.MultiDiGraph:
    nodes = {node}
    frontier = {node}
    for _ in range(depth):
        nxt = {s for n in frontier for s in g.successors(n)}
        nodes |= nxt
        frontier = nxt
    return g.subgraph(nodes).copy()
