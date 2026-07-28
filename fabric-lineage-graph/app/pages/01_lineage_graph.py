"""Interactive lineage graph page."""
from __future__ import annotations
import os
import pathlib
import tempfile

import streamlit as st

from common.onelake_io import _onelake_table_path  # noqa: F401 — path helper
from graph.build_graph import build_graph, upstream, downstream
from graph.render_pyvis import render


st.title("Lineage graph")


@st.cache_data(ttl=300)
def _load_edges() -> list[dict]:
    """Read the edges Delta table. Order of precedence:
    1. `LINEAGE_LOCAL_EDGES_PATH` — JSON file (local/container dev, offline).
    2. Spark `EDGES_TABLE` — inside a Fabric notebook.
    3. Delta on OneLake via `deltalake` + AAD token — local against live Fabric.
    """
    local = os.environ.get("LINEAGE_LOCAL_EDGES_PATH")
    if local and pathlib.Path(local).exists():
        import json
        return json.loads(pathlib.Path(local).read_text(encoding="utf-8"))
    try:
        from pyspark.sql import SparkSession  # type: ignore
        spark = SparkSession.builder.getOrCreate()
        return [r.asDict(recursive=True)
                for r in spark.table(os.environ.get("EDGES_TABLE", "lineage_edges")).collect()]
    except Exception:
        from deltalake import DeltaTable  # type: ignore
        from azure.identity import DefaultAzureCredential
        token = DefaultAzureCredential().get_token("https://storage.azure.com/.default").token
        dt = DeltaTable(
            _onelake_table_path(),
            storage_options={"bearer_token": token, "use_fabric_endpoint": "true"},
        )
        return dt.to_pandas().to_dict(orient="records")


edges = _load_edges()
st.metric("Edges loaded", len(edges))

g = build_graph(edges)
st.write(f"Nodes: {g.number_of_nodes()} — Edges: {g.number_of_edges()}")

focus = st.selectbox("Focus node (optional)", [""] + sorted(g.nodes()))
direction = st.radio("Trace", ["both", "upstream", "downstream"], horizontal=True)
depth = st.slider("Depth", 1, 6, 3)

if focus:
    if direction == "upstream":
        sg = upstream(g, focus, depth)
    elif direction == "downstream":
        sg = downstream(g, focus, depth)
    else:
        sg = upstream(g, focus, depth)
        sg.add_nodes_from(downstream(g, focus, depth).nodes(data=True))
        sg.add_edges_from(downstream(g, focus, depth).edges(data=True, keys=True))
else:
    sg = g

with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp:
    html_path = render(sg, tmp.name)

st.components.v1.html(pathlib.Path(html_path).read_text(encoding="utf-8"), height=780)
