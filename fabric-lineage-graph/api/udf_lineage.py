"""Fabric User Data Function — lineage REST API.

Deployed as a UDF item in the Fabric workspace. Endpoints:
  GET  /edges                 -> latest edges from lineage.edges
  GET  /graph?node=&depth=    -> upstream+downstream subgraph as JSON
  POST /edges                 -> append edges (e.g. from external CI runs)

Inside Fabric UDF runtime the entrypoint signature is `def main(req)` per the
Fabric UDF Python SDK. Locally this module is importable and the handlers can
be wrapped in any HTTP framework for testing.
"""
from __future__ import annotations
import json

from common.schema import LineageEdge
from common.onelake_io import write_edges
from graph.build_graph import build_graph, upstream, downstream


def list_edges() -> dict:
    try:
        from pyspark.sql import SparkSession  # type: ignore
        spark = SparkSession.builder.getOrCreate()
        rows = [r.asDict(recursive=True) for r in spark.table("lineage_edges").collect()]
        return {"value": rows, "count": len(rows)}
    except Exception as exc:
        return {"value": [], "count": 0, "error": str(exc)}


def graph_subset(node: str, depth: int = 3) -> dict:
    rows = list_edges()["value"]
    g = build_graph(rows)
    if node not in g:
        return {"nodes": [], "edges": []}
    sg = upstream(g, node, depth)
    sg.add_nodes_from(downstream(g, node, depth).nodes(data=True))
    sg.add_edges_from(downstream(g, node, depth).edges(data=True, keys=True))
    return {
        "nodes": [{"id": n, **d} for n, d in sg.nodes(data=True)],
        "edges": [{"source": s, "target": t, "key": k, **d}
                  for s, t, k, d in sg.edges(data=True, keys=True)],
    }


def append_edges(payload: list[dict]) -> dict:
    edges = [LineageEdge(**e) for e in payload]
    n = write_edges(edges)
    return {"appended": n}


def main(req):  # Fabric UDF entrypoint
    method = req.method.upper()
    path = req.url.path

    if method == "GET" and path.endswith("/edges"):
        return list_edges()
    if method == "GET" and "/graph" in path:
        return graph_subset(req.params.get("node", ""), int(req.params.get("depth", 3)))
    if method == "POST" and path.endswith("/edges"):
        body = json.loads(req.body or "[]")
        return append_edges(body)
    return {"error": "not_found", "path": path, "method": method}
