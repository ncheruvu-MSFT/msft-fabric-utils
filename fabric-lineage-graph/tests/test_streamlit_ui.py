"""Streamlit UI tests using streamlit's built-in AppTest framework.

Each test runs a page script in-process (no browser, no socket) and asserts on
the resulting widget tree. Networked widgets (UDF calls in glossary/access
pages) are stubbed by clearing UDF_BASE_URL so the early `st.stop()` fires
and the test only validates the "configure first" UX path.

Lineage page is validated by stubbing the Delta read with a small in-memory
edge list — that way we don't need OneLake credentials or a real
SparkSession.
"""
from __future__ import annotations
import importlib
import os
import pathlib
import sys
from typing import Any

import pytest

# Add the package root to sys.path so the page scripts can `from graph...`.
PKG_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))

streamlit = pytest.importorskip("streamlit", reason="streamlit not installed")
from streamlit.testing.v1 import AppTest  # noqa: E402


PAGES = PKG_ROOT / "app" / "pages"


@pytest.fixture(autouse=True)
def _no_udf(monkeypatch):
    """Strip UDF_BASE_URL so glossary/access pages exercise the warning path."""
    monkeypatch.delenv("UDF_BASE_URL", raising=False)


@pytest.fixture(autouse=True)
def _clear_streamlit_caches():
    """`@st.cache_data` is module-level and persists across AppTest invocations;
    clear it so successive tests don't see each other's edge lists."""
    import streamlit as _st
    try:
        _st.cache_data.clear()
    except Exception:
        pass
    yield
    try:
        _st.cache_data.clear()
    except Exception:
        pass


def test_glossary_editor_shows_warning_when_udf_unconfigured():
    at = AppTest.from_file(str(PAGES / "02_glossary_editor.py")).run(timeout=30)
    assert any("UDF_BASE_URL" in w.value for w in at.warning)
    assert at.title[0].value == "Glossary editor"


def test_access_requests_shows_warning_when_udf_unconfigured():
    at = AppTest.from_file(str(PAGES / "03_access_requests.py")).run(timeout=30)
    assert any("UDF_BASE_URL" in w.value for w in at.warning)
    assert at.title[0].value == "Access requests"


def test_lineage_page_renders_metric_and_widgets(monkeypatch):
    # Build a tiny edge set so the page doesn't try to hit OneLake.
    fake_edges = [{
        "source_qname": "azuresql://srv/db/silver/customer_360",
        "source_type": "azure_sql_table",
        "target_qname": "azuresql://srv/db/gold/customer_revenue_mart",
        "target_type": "azure_sql_view",
        "process_name": "p1", "process_type": "tsql_view",
        "artifact_ref": "x", "columns": [("customer_id", "customer_id")],
    }]

    # The page tries `from pyspark.sql import SparkSession` first; force that
    # to fail by inserting a sentinel module that raises ImportError on attr
    # access. Then fall through to the deltalake path which we stub.
    pyspark_mod = type(sys)("pyspark")
    sql_mod = type(sys)("pyspark.sql")

    def _missing(*_a, **_kw):
        raise ImportError("pyspark not available in tests")
    sql_mod.SparkSession = type("S", (), {"builder": type(
        "B", (), {"getOrCreate": staticmethod(_missing)})})
    pyspark_mod.sql = sql_mod
    monkeypatch.setitem(sys.modules, "pyspark", pyspark_mod)
    monkeypatch.setitem(sys.modules, "pyspark.sql", sql_mod)

    # Stub the deltalake fallback so the call returns our fake edges.
    deltalake_mod = type(sys)("deltalake")

    class _FakeDT:
        def __init__(self, *a, **kw): pass
        def to_pandas(self):
            import pandas as pd
            return pd.DataFrame(fake_edges)
    deltalake_mod.DeltaTable = _FakeDT
    monkeypatch.setitem(sys.modules, "deltalake", deltalake_mod)

    # Required by common.onelake_io._onelake_table_path
    monkeypatch.setenv("FABRIC_WORKSPACE_ID", "ws-test")
    monkeypatch.setenv("LINEAGE_LAKEHOUSE_ID", "lh-test")
    monkeypatch.setenv("LAKEHOUSE_ID", "lh-test")

    # azure.identity is referenced inside _load_edges; stub a minimal cred.
    az_mod = sys.modules.setdefault("azure", type(sys)("azure"))
    az_id_mod = type(sys)("azure.identity")

    class _FakeCred:
        def get_token(self, *_a, **_kw):
            return type("Tok", (), {"token": "stub"})
    az_id_mod.DefaultAzureCredential = _FakeCred
    az_mod.identity = az_id_mod
    monkeypatch.setitem(sys.modules, "azure.identity", az_id_mod)

    at = AppTest.from_file(str(PAGES / "01_lineage_graph.py")).run(timeout=60)
    assert not at.exception, f"Streamlit exceptions: {[e.value for e in at.exception]}"
    assert at.title[0].value == "Lineage graph"
    metric_values = [m.value for m in at.metric]
    assert "1" in metric_values


def test_lineage_page_uses_local_edges_path_when_set(monkeypatch, tmp_path):
    """LINEAGE_LOCAL_EDGES_PATH short-circuits Spark / OneLake — container mode."""
    import json
    edges_file = tmp_path / "edges.json"
    edges_file.write_text(json.dumps([
        {
            "source_qname": "azuresql://srv/db/silver/customer_360",
            "source_type": "azure_sql_table",
            "target_qname": "azuresql://srv/db/gold/customer_revenue_mart",
            "target_type": "azure_sql_view",
            "process_name": "p1", "process_type": "tsql_view",
            "artifact_ref": "x", "columns": [["customer_id", "customer_id"]],
        },
        {
            "source_qname": "azuresql://srv/db/silver/orders",
            "source_type": "azure_sql_table",
            "target_qname": "azuresql://srv/db/gold/customer_revenue_mart",
            "target_type": "azure_sql_view",
            "process_name": "p1", "process_type": "tsql_view",
            "artifact_ref": "x", "columns": [["total", "ltv"]],
        },
    ]), encoding="utf-8")

    monkeypatch.setenv("LINEAGE_LOCAL_EDGES_PATH", str(edges_file))
    monkeypatch.delenv("FABRIC_WORKSPACE_ID", raising=False)
    monkeypatch.delenv("LAKEHOUSE_ID", raising=False)

    at = AppTest.from_file(str(PAGES / "01_lineage_graph.py")).run(timeout=60)
    assert not at.exception, f"Streamlit exceptions: {[e.value for e in at.exception]}"
    metric_values = [m.value for m in at.metric]
    assert "2" in metric_values
