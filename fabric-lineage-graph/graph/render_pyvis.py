"""Render a NetworkX graph as an interactive PyVis HTML.

Used both by the Streamlit app (embedded iframe) and the demo notebook
(displayed inline via IPython.display.HTML).
"""
from __future__ import annotations
import pathlib

import networkx as nx
from pyvis.network import Network


# Match the dark theme convention from .github/copilot-instructions.md
_BG = "#16213e"
_FONT = "#CCCCDD"

_KIND_COLORS = {
    "azure_sql_table": "#1565C0",
    "azure_postgresql_table": "#7B1FA2",
    "azure_cosmosdb_sqlapi_collection": "#283593",
    "databricks_table": "#FF7043",
    "fabric_lakehouse_table": "#2E7D32",
    "fabric_warehouse_table": "#388E3C",
    "fabric_kql_table": "#00897B",
    "powerbi_dataset": "#FBC02D",
    "powerbi_report": "#F9A825",
    "adf_pipeline": "#6644AA",
    "fabric_data_pipeline": "#AB47BC",
    "fabric_notebook": "#4499DD",
    "fabric_dataflow_gen2": "#26A69A",
    "file": "#90A4AE",
}


def render(g: nx.MultiDiGraph, out_path: str | pathlib.Path = "lineage.html",
           height: str = "750px",
           column_labels: dict[tuple[str, str], str] | None = None,
           show_columns: bool = True) -> str:
    """Render the lineage graph as an interactive PyVis HTML file.

    When ``show_columns`` is True and edges carry column-map info, columns are
    rendered as sub-nodes attached to their owning asset (dashed bracket
    edges) so the user can see column-level lineage inline.
    """
    net = Network(height=height, width="100%", directed=True,
                  bgcolor=_BG, font_color=_FONT)
    net.barnes_hut(gravity=-3000, spring_length=180)

    column_labels = column_labels or {}

    for node, data in g.nodes(data=True):
        kind = data.get("kind", "file")
        cols = data.get("columns") or []
        title_lines = [kind, node]
        if cols:
            title_lines.append(f"columns ({len(cols)}):")
            title_lines.extend(f"  - {c}" for c in cols[:30])
        net.add_node(
            node,
            label=node.rsplit("/", 1)[-1],
            title="\n".join(title_lines),
            color=_KIND_COLORS.get(kind, "#888888"),
            shape="box",
        )

        if show_columns:
            for col in cols:
                col_id = f"{node}::col::{col}"
                col_lbl = column_labels.get((node, col))
                col_title = f"{node}.{col}" + (f"\nlabel: {col_lbl}" if col_lbl else "")
                net.add_node(
                    col_id, label=col, title=col_title,
                    color="#0d1b3e" if col_lbl != "Highly-Confidential-Restricted"
                          else "#C62828",
                    shape="ellipse", size=8, font={"size": 10, "color": _FONT},
                )
                net.add_edge(node, col_id, color="#444466",
                             dashes=True, arrows="")

    for s, t, data in g.edges(data=True):
        net.add_edge(s, t, title=data.get("process_type", ""),
                     color="#4499DD", arrows="to")
        if show_columns:
            for pair in data.get("columns") or []:
                if len(pair) != 2:
                    continue
                src_col, tgt_col = pair
                net.add_edge(
                    f"{s}::col::{src_col}", f"{t}::col::{tgt_col}",
                    color="#88BBEE", arrows="to", dashes=True,
                    title=f"{src_col} -> {tgt_col}",
                )

    out = pathlib.Path(out_path)
    net.write_html(str(out), notebook=False)
    return str(out)
