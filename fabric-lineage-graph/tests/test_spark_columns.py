"""Tests for the column-aware PySpark/notebook scanner."""
from __future__ import annotations

from harvesters.spark_columns import analyze_python


def _by_target(edges):
    """Map target column -> set of (source_qname, source_col)."""
    out: dict[str, set[tuple[str, str]]] = {}
    for e in edges:
        for src_col, tgt_col in e.columns or []:
            out.setdefault(tgt_col, set()).add((e.source_qname, src_col))
    return out


def test_select_tracks_passthrough_columns():
    src = (
        'df = spark.read.table("silver.orders")\n'
        'sel = df.select("CustomerId", "Amount")\n'
        'sel.write.saveAsTable("gold.fact")\n'
    )
    edges = analyze_python(src, notebook="nb", unit="cell01")
    bt = _by_target(edges)
    assert ("spark://silver.orders", "CustomerId") in bt["CustomerId"]
    assert ("spark://silver.orders", "Amount") in bt["Amount"]


def test_withcolumn_resolves_referenced_source_columns():
    src = (
        'from pyspark.sql.functions import col\n'
        'df = spark.read.table("silver.orders")\n'
        'd2 = df.withColumn("Net", col("Gross") * (1 - col("Disc")))\n'
        'd2.select("Net").write.saveAsTable("gold.fact")\n'
    )
    edges = analyze_python(src, notebook="nb", unit="cell01")
    bt = _by_target(edges)
    assert ("spark://silver.orders", "Gross") in bt["Net"]
    assert ("spark://silver.orders", "Disc") in bt["Net"]


def test_withcolumnrenamed_maps_old_to_new():
    src = (
        'df = spark.read.table("silver.orders")\n'
        'r = df.withColumnRenamed("Qty", "Units")\n'
        'r.select("Units").write.saveAsTable("gold.fact")\n'
    )
    edges = analyze_python(src, notebook="nb", unit="cell01")
    bt = _by_target(edges)
    assert ("spark://silver.orders", "Qty") in bt["Units"]


def test_selectexpr_alias_tracks_source():
    src = (
        'df = spark.read.table("silver.orders")\n'
        'e = df.selectExpr("amount * qty as total")\n'
        'e.write.saveAsTable("gold.fact")\n'
    )
    edges = analyze_python(src, notebook="nb", unit="cell01")
    bt = _by_target(edges)
    assert "total" in bt
    sources = {c for (_q, c) in bt["total"]}
    assert {"amount", "qty"} <= sources


def test_process_name_includes_notebook_and_function():
    src = (
        'def build():\n'
        '    df = spark.read.table("silver.orders")\n'
        '    df.select("Amount").write.saveAsTable("gold.fact")\n'
    )
    edges = analyze_python(src, notebook="build_gold", unit="module")
    assert edges
    assert all(e.process_name.startswith("spark:build_gold:build:") for e in edges)


def test_spark_sql_create_table_as_emits_column_edges():
    src = (
        'spark.sql("""\n'
        'CREATE TABLE gold.agg AS\n'
        'SELECT region, SUM(net) AS total_net FROM gold.fact GROUP BY region\n'
        '""")\n'
    )
    edges = analyze_python(src, notebook="nb", unit="cell01")
    bt = _by_target(edges)
    assert "total_net" in bt
    assert any(c == "net" for (_q, c) in bt["total_net"])


def test_select_star_falls_back_to_table_level_edge():
    src = (
        'df = spark.read.table("silver.orders")\n'
        's = df.select("*")\n'
        's.write.saveAsTable("gold.copy")\n'
    )
    edges = analyze_python(src, notebook="nb", unit="cell01")
    assert edges
    # table-level edge, no column mapping
    assert all((e.columns is None) for e in edges)
    assert edges[0].source_qname == "spark://silver.orders"
    assert edges[0].target_qname == "spark://gold.copy"
