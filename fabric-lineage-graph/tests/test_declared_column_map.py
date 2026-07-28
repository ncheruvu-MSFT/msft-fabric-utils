"""Tests for the declared-edges harvester column_map extension."""
from __future__ import annotations
import json
import pathlib
import tempfile

from harvesters.declared import DeclaredEdgesHarvester


def _write(path: pathlib.Path, doc: dict) -> pathlib.Path:
    p = path / "edges.json"
    p.write_text(json.dumps(doc), encoding="utf-8")
    return p


def test_declared_harvester_parses_column_map():
    doc = {"edges": [{
        "source_qname": "azuresql://srv/db/silver/customer_360",
        "source_type": "azure_sql_view",
        "target_qname": "fabric://ws/lh/customer_360",
        "target_type": "fabric_lakehouse_table",
        "process_name": "adf:copy:customer_360",
        "process_type": "adf_copy",
        "column_map": {
            "customer_id": "customer_id",
            "email": "primary_email",
            "ltv": "lifetime_value",
        },
    }]}
    with tempfile.TemporaryDirectory() as d:
        p = _write(pathlib.Path(d), doc)
        edges = list(DeclaredEdgesHarvester(p).harvest())
    assert len(edges) == 1
    e = edges[0]
    assert e.columns is not None
    pairs = set(e.columns)
    assert ("customer_id", "customer_id") in pairs
    assert ("email", "primary_email") in pairs
    assert ("ltv", "lifetime_value") in pairs


def test_declared_harvester_without_column_map_leaves_columns_none():
    doc = {"edges": [{
        "source_qname": "azuresql://srv/db/silver/c",
        "source_type": "azure_sql_view",
        "target_qname": "fabric://ws/lh/c",
        "target_type": "fabric_lakehouse_table",
        "process_name": "adf:copy:c",
        "process_type": "adf_copy",
    }]}
    with tempfile.TemporaryDirectory() as d:
        p = _write(pathlib.Path(d), doc)
        edges = list(DeclaredEdgesHarvester(p).harvest())
    assert edges[0].columns is None


def test_env_var_expansion_still_works():
    import os
    os.environ["LG_TEST_HOST"] = "srv1"
    doc = {"edges": [{
        "source_qname": "azuresql://${LG_TEST_HOST}/db/s/t",
        "source_type": "azure_sql_table",
        "target_qname": "azuresql://${LG_TEST_HOST}/db/s/v",
        "target_type": "azure_sql_view",
        "process_name": "x", "process_type": "tsql_view",
    }]}
    with tempfile.TemporaryDirectory() as d:
        p = _write(pathlib.Path(d), doc)
        edges = list(DeclaredEdgesHarvester(p).harvest())
    assert "srv1" in edges[0].source_qname
    assert "srv1" in edges[0].target_qname
