"""Scan a code repository and build column-level lineage.

Walks a directory for Fabric notebooks (`.ipynb` / `.py`) and T-SQL (`.sql`)
files, harvests **column-level** lineage edges, and lets you:

  * print the lineage **path for a single column** (upstream origins +
    downstream consumers), each hop tagged with the transform that produced it
    (notebook + cell / SQL procedure / python function);
  * export the raw `LineageEdge` rows as JSON (`--export-json`);
  * export a column graph in the shape the Rayfin **lineage-app** consumes
    (`--app-export`), so the in-app "Column graph" view renders *real* scanned
    lineage instead of demo data.

Usage::

    python -m harvesters.scan_repo --root ./samples/complex \
        --column "gold.fact_sales.NetAmount"

    python -m harvesters.scan_repo --root ../my-fabric-repo \
        --app-export ../rayfin-governance/lineage-app/public/column_edges.json
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

from common.schema import LineageEdge
from graph.column_path import (
    build_column_graph,
    resolve_column_node,
    split_col_id,
    trace_column,
)
from harvesters.notebook import NotebookHarvester
from harvesters.tsql import TsqlHarvester


# ---- scanning ---------------------------------------------------------------

def scan_repo(root: str | pathlib.Path, *, server: str = "fabric",
              database: str = "warehouse") -> list[LineageEdge]:
    """Harvest column-level edges from notebooks + .sql under `root`."""
    root = pathlib.Path(root)
    edges: list[LineageEdge] = []
    edges.extend(NotebookHarvester(root).harvest())
    edges.extend(TsqlHarvester(root, server=server, database=database).harvest())
    return edges


# ---- app export -------------------------------------------------------------

def _short_label(qname: str) -> str:
    trimmed = re.sub(r"/+$", "", qname)
    seg = re.split(r"[:/]", trimmed)
    seg = [s for s in seg if s]
    return seg[-1] if seg else qname


def _infer_layer(qname: str, kind: str) -> str:
    q = qname.lower()
    k = kind.lower()
    if "report" in q or "kpi" in q or k.endswith("report") or ".pbix" in q:
        return "report"
    if "semantic" in q or "dataset" in q or "measure" in q or k.endswith("dataset"):
        return "semantic"
    if "gold" in q:
        return "gold"
    if "silver" in q:
        return "silver"
    if "bronze" in q or "raw" in q:
        return "bronze"
    if "warehouse" in k or "lakehouse" in k:
        # medallion not in the name — treat warehouse facts as gold, else silver
        return "gold" if ("fact" in q or "agg" in q or "dim" in q) else "silver"
    return "source"


def to_app_graph(edges: list[LineageEdge]) -> dict:
    """Build the `{assets, edges}` payload the lineage-app column graph wants."""
    asset_meta: dict[str, dict[str, str]] = {}
    asset_kind: dict[str, str] = {}
    col_edges: list[dict[str, str]] = []

    def _note(qname: str, kind: str) -> None:
        asset_kind.setdefault(qname, kind)

    for e in edges:
        _note(e.source_qname, e.source_type)
        _note(e.target_qname, e.target_type)
        for pair in e.columns or []:
            src_col, tgt_col = (
                (pair["src"], pair["tgt"]) if isinstance(pair, dict) else pair
            )
            col_edges.append({
                "from": f"{e.source_qname}::{src_col}",
                "to": f"{e.target_qname}::{tgt_col}",
                "transform": e.process_name,
            })

    for qname, kind in asset_kind.items():
        asset_meta[qname] = {
            "label": _short_label(qname),
            "type": _infer_layer(qname, kind),
        }

    return {"assets": asset_meta, "edges": col_edges}


# ---- column path printing ---------------------------------------------------

def print_column_path(edges: list[LineageEdge], query: str) -> int:
    graph = build_column_graph(edges)
    node = resolve_column_node(graph, query)
    if node is None:
        print(f"No column matching '{query}' found in {len(graph.nodes())} "
              f"column nodes.", file=sys.stderr)
        return 2
    result = trace_column(graph, node)
    tbl, col = split_col_id(node)
    print(f"\nColumn: {col}   ({tbl})")
    print("=" * 72)

    print("\n  Upstream (where it comes from):")
    if not result.upstream:
        print("    (origin — no upstream column edges)")
    for e in result.upstream:
        s_tbl, s_col = split_col_id(e.src)
        d_tbl, d_col = split_col_id(e.dst)
        print(f"    {s_tbl}.{s_col}  ->  {d_tbl}.{d_col}")
        print(f"        via {e.transform}")

    print("\n  Downstream (what it feeds):")
    if not result.downstream:
        print("    (leaf — no downstream column edges)")
    for e in result.downstream:
        s_tbl, s_col = split_col_id(e.src)
        d_tbl, d_col = split_col_id(e.dst)
        print(f"    {s_tbl}.{s_col}  ->  {d_tbl}.{d_col}")
        print(f"        via {e.transform}")
    print()
    return 0


# ---- CLI --------------------------------------------------------------------

def _cli(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--root", required=True, help="Repo directory to scan")
    p.add_argument("--column", help="Trace this column (e.g. 'gold.fact_sales.NetAmount')")
    p.add_argument("--export-json", help="Write harvested LineageEdge rows to this path")
    p.add_argument("--app-export", help="Write the lineage-app column-graph JSON to this path")
    p.add_argument("--server", default="fabric")
    p.add_argument("--database", default="warehouse")
    args = p.parse_args(argv)

    edges = scan_repo(args.root, server=args.server, database=args.database)
    col_edge_count = sum(len(e.columns or []) for e in edges)
    print(f"Scanned {args.root}: {len(edges)} lineage edges, "
          f"{col_edge_count} column-level mappings.")

    if args.export_json:
        rows = [e.to_row() for e in edges]
        pathlib.Path(args.export_json).write_text(
            json.dumps(rows, indent=2, default=str), encoding="utf-8")
        print(f"  wrote edges -> {args.export_json}")

    if args.app_export:
        payload = to_app_graph(edges)
        pathlib.Path(args.app_export).write_text(
            json.dumps(payload, indent=2), encoding="utf-8")
        print(f"  wrote app column graph -> {args.app_export} "
              f"({len(payload['edges'])} column edges, "
              f"{len(payload['assets'])} assets)")

    if args.column:
        return print_column_path(edges, args.column)
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
