"""Column-level lineage path tracer.

Builds a column graph from the `columns` field of the harvested `LineageEdge`
records and answers "where does this column come from / go to" — the Python
counterpart of the TypeScript `traceColumn` in the Rayfin lineage-app.

A column node id is `"<table_qname>::<column>"`.  Each `(src_col, tgt_col)` pair
on a `LineageEdge` becomes a directed column edge tagged with the edge's
`process_name` (notebook + cell / SQL proc / function) so the path reads as a
chain of named transforms.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from common.schema import LineageEdge


def col_id(table_qname: str, column: str) -> str:
    return f"{table_qname}::{column}"


def split_col_id(node: str) -> tuple[str, str]:
    table, _, column = node.rpartition("::")
    return table, column


@dataclass
class ColEdge:
    src: str          # source column id
    dst: str          # target column id
    transform: str    # process_name
    process_type: str
    artifact: str


@dataclass
class ColumnGraph:
    edges: list[ColEdge] = field(default_factory=list)
    _fwd: dict[str, list[ColEdge]] = field(default_factory=dict)
    _bwd: dict[str, list[ColEdge]] = field(default_factory=dict)

    def add(self, edge: ColEdge) -> None:
        self.edges.append(edge)
        self._fwd.setdefault(edge.src, []).append(edge)
        self._bwd.setdefault(edge.dst, []).append(edge)

    def nodes(self) -> set[str]:
        ns: set[str] = set()
        for e in self.edges:
            ns.add(e.src)
            ns.add(e.dst)
        return ns


def build_column_graph(edges: Iterable[LineageEdge | dict]) -> ColumnGraph:
    g = ColumnGraph()
    for e in edges:
        if isinstance(e, dict):
            src_q = e["source_qname"]
            tgt_q = e["target_qname"]
            pname = e.get("process_name", "")
            ptype = e.get("process_type", "")
            artifact = e.get("artifact_ref", "")
            cols = e.get("columns") or []
        else:
            src_q = e.source_qname
            tgt_q = e.target_qname
            pname = e.process_name
            ptype = e.process_type
            artifact = e.artifact_ref
            cols = e.columns or []
        for pair in cols:
            src_col, tgt_col = (pair["src"], pair["tgt"]) if isinstance(pair, dict) else pair
            g.add(ColEdge(
                src=col_id(src_q, src_col),
                dst=col_id(tgt_q, tgt_col),
                transform=pname,
                process_type=ptype,
                artifact=artifact,
            ))
    return g


@dataclass
class TraceResult:
    start: str
    upstream: list[ColEdge]      # edges reachable going backwards
    downstream: list[ColEdge]    # edges reachable going forwards

    @property
    def columns(self) -> set[str]:
        cols = {self.start}
        for e in self.upstream + self.downstream:
            cols.add(e.src)
            cols.add(e.dst)
        return cols

    def to_dict(self) -> dict:
        def _e(e: ColEdge) -> dict:
            return {
                "src": e.src, "dst": e.dst,
                "transform": e.transform, "processType": e.process_type,
                "artifact": e.artifact,
            }
        return {
            "start": self.start,
            "upstream": [_e(e) for e in self.upstream],
            "downstream": [_e(e) for e in self.downstream],
            "columns": sorted(self.columns),
        }


def _walk(adj: dict[str, list[ColEdge]], start: str,
          pick_next) -> list[ColEdge]:
    seen_edges: list[ColEdge] = []
    seen_ids: set[int] = set()
    visited = {start}
    stack = [start]
    while stack:
        node = stack.pop()
        for e in adj.get(node, []):
            if id(e) not in seen_ids:
                seen_ids.add(id(e))
                seen_edges.append(e)
            nxt = pick_next(e)
            if nxt not in visited:
                visited.add(nxt)
                stack.append(nxt)
    return seen_edges


def trace_column(graph: ColumnGraph, column_node: str) -> TraceResult:
    """Trace one column upstream (origins) and downstream (consumers)."""
    upstream = _walk(graph._bwd, column_node, lambda e: e.src)
    downstream = _walk(graph._fwd, column_node, lambda e: e.dst)
    return TraceResult(start=column_node, upstream=upstream, downstream=downstream)


def resolve_column_node(graph: ColumnGraph, query: str) -> str | None:
    """Find a column node id matching a loose query like 'fact_sales.NetAmount'
    or 'NetAmount'.  Returns the best-ranked matching node, or None."""
    nodes = graph.nodes()
    if query in nodes:
        return query

    def _table_tail(tbl: str) -> str:
        # qname after the scheme prefix, e.g. "spark://gold.fact_sales" -> "gold.fact_sales"
        return tbl.split("://", 1)[-1]

    candidates: list[tuple[int, str]] = []  # (score, node) — higher score = better
    if "." in query and "::" not in query:
        table_part, col_part = query.rsplit(".", 1)
        tp, cp = table_part.lower(), col_part.lower()
        for n in nodes:
            tbl, col = split_col_id(n)
            if col.lower() != cp:
                continue
            tail = _table_tail(tbl).lower()
            if tail == tp:
                candidates.append((100, n))            # exact table + column
            elif tail.endswith("." + tp) or tail.endswith("/" + tp):
                candidates.append((80, n))             # table last-segment match
            elif tp in tail:
                candidates.append((40, n))             # substring fallback
        if candidates:
            candidates.sort(key=lambda x: (-x[0], len(x[1])))
            return candidates[0][1]

    q = query.lower()
    for n in nodes:                                    # bare column name
        _tbl, col = split_col_id(n)
        if col.lower() == q:
            return n
    for n in nodes:                                    # substring fallback
        if q in n.lower():
            return n
    return None
