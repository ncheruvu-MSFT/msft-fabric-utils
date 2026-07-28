"""Unit tests for TsqlHarvester. Run with: pytest tests/test_tsql_parser.py"""
from __future__ import annotations
import pathlib
import tempfile

from harvesters.tsql import parse_sql_file


def _write(tmp: pathlib.Path, sql: str) -> pathlib.Path:
    p = tmp / "f.sql"
    p.write_text(sql, encoding="utf-8")
    return p


def test_insert_select_emits_one_edge_with_columns():
    with tempfile.TemporaryDirectory() as d:
        f = _write(pathlib.Path(d), "INSERT INTO t (a) SELECT a FROM s;")
        edges = parse_sql_file(f, server="srv", db="db")
        assert len(edges) == 1
        e = edges[0]
        assert e.process_type == "tsql_insert"
        assert e.source_qname.endswith("/s")
        assert e.target_qname.endswith("/t")
        assert e.columns == [("a", "a")]


def test_create_view_emits_view_edge():
    sql = "CREATE OR ALTER VIEW v AS SELECT id, name FROM tbl;"
    with tempfile.TemporaryDirectory() as d:
        f = _write(pathlib.Path(d), sql)
        edges = parse_sql_file(f, "srv", "db")
        assert any(e.process_type == "tsql_view" for e in edges)


def test_multi_source_join_emits_edge_per_source():
    sql = """
    INSERT INTO target (id) SELECT a.id FROM a JOIN b ON a.id = b.id;
    """
    with tempfile.TemporaryDirectory() as d:
        f = _write(pathlib.Path(d), sql)
        edges = parse_sql_file(f, "srv", "db")
        sources = {e.source_qname.rsplit("/", 1)[-1] for e in edges}
        assert sources == {"a", "b"}
