"""Column-level provenance for PySpark DataFrame code.

`analyze_python` walks a Python AST and tracks, per DataFrame variable, where
each output column came from.  It understands the common medallion-pipeline
shape:

    orders = spark.read.table("silver.orders_clean")          # read  -> source frame
    typed  = orders.withColumn("AmountDec", col("Amount").cast("decimal"))
    sel    = typed.select("CustomerId", "AmountDec")           # projection
    ren    = sel.withColumnRenamed("AmountDec", "GrossAmount") # rename
    ren.write.mode("overwrite").saveAsTable("gold.fact_sales") # write -> edges

For every write it emits one `LineageEdge` per (source_table -> target_table)
pair, with a `columns` list of (src_col, tgt_col) where the mapping is
derivable.  Identity passthroughs (`select("*")`, untouched columns) fall back
to a table-level edge with `columns=None`.

`spark.sql("...")` statements are handed to `common.column_lineage` so the SQL
column extractor (sqlglot) does the work and the result is folded into the same
edge stream.

Provenance is best-effort: linear single-source chains are tracked precisely;
joins attribute a referenced column to *every* contributing source (ambiguous
but not wrong for impact analysis).
"""
from __future__ import annotations

import ast
from dataclasses import dataclass, field

from common.schema import LineageEdge
from common.column_lineage import extract_column_edges


# (source_qname, source_col)
Provenance = set[tuple[str, str]]

_READ_CHAIN = {"load", "table", "parquet", "csv", "json"}
_WRITE_TERMINAL = {"saveAsTable", "insertInto", "save"}
_RENAME = "withColumnRenamed"
_WITH_COLUMN = "withColumn"
_SELECT = {"select", "selectExpr"}
_PASSTHROUGH = {"filter", "where", "distinct", "dropDuplicates", "orderBy",
                "sort", "limit", "repartition", "cache", "persist", "alias",
                "drop", "fillna", "na", "dropna", "coalesce", "checkpoint"}


def _qname_for(arg: str) -> tuple[str, str]:
    """Map a read/write argument to (type, qualified_name)."""
    if arg.startswith("abfss://") and "onelake" in arg:
        return ("fabric_lakehouse_table", arg)
    if "://" in arg:
        return ("file", arg)
    # "schema.table" style — a Spark catalog reference.
    return ("fabric_lakehouse_table", f"spark://{arg}")


@dataclass
class ColFrame:
    """Column provenance for one DataFrame value."""
    sources: set[str] = field(default_factory=set)        # source qnames
    source_type: str = "fabric_lakehouse_table"
    overrides: dict[str, Provenance] = field(default_factory=dict)
    projected: list[str] | None = None                    # exact output cols, if known

    def resolve(self, name: str) -> Provenance:
        if name in self.overrides:
            return set(self.overrides[name])
        return {(s, name) for s in self.sources}

    def output_columns(self) -> list[str]:
        if self.projected is not None:
            return self.projected
        return sorted(self.overrides)

    def copy(self) -> "ColFrame":
        return ColFrame(
            sources=set(self.sources),
            source_type=self.source_type,
            overrides={k: set(v) for k, v in self.overrides.items()},
            projected=list(self.projected) if self.projected is not None else None,
        )


def _str_literal(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _referenced_columns(node: ast.AST) -> list[str]:
    """Best-effort: every string literal and `col('x')`/attribute in an expr."""
    cols: list[str] = []
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name) \
                and sub.func.id in {"col", "column"} and sub.args:
            lit = _str_literal(sub.args[0])
            if lit:
                cols.append(lit)
        elif isinstance(sub, ast.Constant) and isinstance(sub.value, str):
            # bare string column reference, e.g. inside expr("a + b") handled below
            pass
    return cols


def _flatten_call_chain(node: ast.Call) -> tuple[ast.AST, list[tuple[str, ast.Call]]]:
    """Return (base_expr, [(method, call), ...]) left-to-right for a.b().c()."""
    methods: list[tuple[str, ast.Call]] = []
    cur: ast.AST = node
    while isinstance(cur, ast.Call) and isinstance(cur.func, ast.Attribute):
        methods.append((cur.func.attr, cur))
        cur = cur.func.value
    methods.reverse()
    return cur, methods


class _SparkVisitor(ast.NodeVisitor):
    def __init__(self, notebook: str, unit: str) -> None:
        self.notebook = notebook
        self._base_unit = unit
        self.frames: dict[str, ColFrame] = {}
        self.edges: list[LineageEdge] = []
        self._artifact = notebook
        self._func_stack: list[str] = []

    @property
    def unit(self) -> str:
        """Process unit name — the enclosing function, else the cell/module."""
        return self._func_stack[-1] if self._func_stack else self._base_unit

    # -- public ----------------------------------------------------------------
    def run(self, tree: ast.AST) -> list[LineageEdge]:
        self.visit(tree)
        return self.edges

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._func_stack.append(node.name)
        self.generic_visit(node)
        self._func_stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef  # type: ignore[assignment]

    # -- assignments build / mutate frames ------------------------------------
    def visit_Assign(self, node: ast.Assign) -> None:
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) \
                and isinstance(node.value, ast.Call):
            frame = self._eval_chain(node.value)
            if frame is not None:
                self.frames[node.targets[0].id] = frame
        self.generic_visit(node)

    def visit_Expr(self, node: ast.Expr) -> None:
        # Terminal writes / spark.sql() not bound to a variable.
        if isinstance(node.value, ast.Call):
            self._eval_chain(node.value)
        self.generic_visit(node)

    # -- chain evaluation ------------------------------------------------------
    def _eval_chain(self, call: ast.Call) -> ColFrame | None:
        base, methods = _flatten_call_chain(call)

        # spark.sql("...") -> hand to the SQL column extractor.
        if self._is_spark_sql(base, methods):
            sql = self._first_sql_arg(methods)
            if sql:
                self._emit_sql(sql)
            return None

        frame = self._seed_frame(base)

        for method, mcall in methods:
            frame = self._apply_method(frame, method, mcall)
            if frame is None:
                return None
        return frame

    def _seed_frame(self, base: ast.AST) -> ColFrame | None:
        """Resolve the DataFrame value a method chain starts from."""
        if isinstance(base, ast.Name):
            if base.id in self.frames:
                return self.frames[base.id].copy()
            if base.id == "spark":
                return ColFrame()  # spark.read... starts an empty source frame
            return ColFrame()
        if isinstance(base, ast.Call):
            # nested chain, e.g. df.select(...).<more>
            return self._eval_chain(base)
        if isinstance(base, ast.Attribute):
            # e.g. `<expr>.write` / `<expr>.read` — unwrap to the DataFrame.
            if base.attr in {"write", "read"}:
                return self._seed_frame(base.value)
            return ColFrame()
        return ColFrame()

    def _apply_method(self, frame: ColFrame | None, method: str,
                      call: ast.Call) -> ColFrame | None:
        if frame is None:
            frame = ColFrame()

        arg0 = _str_literal(call.args[0]) if call.args else None

        if method in _READ_CHAIN and arg0:
            stype, qname = _qname_for(arg0)
            frame.sources = {qname}
            frame.source_type = stype
            frame.projected = None
            frame.overrides = {}
            return frame

        if method == "format" or method == "option" or method == "options" \
                or method == "mode" or method == "schema":
            return frame  # config no-op in the chain

        if method == "read" or method == "write" or method == "na":
            return frame  # attribute-like accessors

        if method in _SELECT:
            return self._apply_select(frame, method, call)

        if method == _RENAME and len(call.args) >= 2:
            old = _str_literal(call.args[0])
            new = _str_literal(call.args[1])
            if old and new:
                prov = frame.resolve(old)
                frame.overrides.pop(old, None)
                frame.overrides[new] = prov
                if frame.projected is not None:
                    frame.projected = [new if c == old else c for c in frame.projected]
            return frame

        if method == _WITH_COLUMN and call.args:
            new = _str_literal(call.args[0])
            if new and len(call.args) >= 2:
                refs = _referenced_columns(call.args[1])
                prov: Provenance = set()
                for r in refs:
                    prov |= frame.resolve(r)
                frame.overrides[new] = prov
                if frame.projected is not None and new not in frame.projected:
                    frame.projected.append(new)
            return frame

        if method in _WRITE_TERMINAL and arg0:
            self._emit_write(frame, method, arg0, call)
            return frame

        if method in _PASSTHROUGH:
            return frame

        # Unknown method — keep the frame so downstream writes still resolve.
        return frame

    def _apply_select(self, frame: ColFrame, method: str,
                      call: ast.Call) -> ColFrame:
        new_proj: list[str] = []
        new_overrides: dict[str, Provenance] = {}
        for a in call.args:
            lit = _str_literal(a)
            if lit == "*":
                # identity projection — keep passthrough semantics
                frame.projected = None
                return frame
            if method == "selectExpr" and lit:
                tgt, prov = self._parse_select_expr(frame, lit)
                new_proj.append(tgt)
                new_overrides[tgt] = prov
                continue
            if lit:
                new_proj.append(lit)
                new_overrides[lit] = frame.resolve(lit)
                continue
            # col("a").alias("b") style
            tgt, prov = self._parse_col_expr(frame, a)
            if tgt:
                new_proj.append(tgt)
                new_overrides[tgt] = prov
        frame.projected = new_proj or None
        # keep prior overrides only for cols still projected
        merged = {k: v for k, v in frame.overrides.items() if k in new_proj}
        merged.update(new_overrides)
        frame.overrides = merged
        return frame

    def _parse_col_expr(self, frame: ColFrame,
                        node: ast.AST) -> tuple[str | None, Provenance]:
        """Handle col('a').alias('b') and similar Column expressions."""
        alias: str | None = None
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr == "alias" and node.args:
            alias = _str_literal(node.args[0])
        refs = _referenced_columns(node)
        prov: Provenance = set()
        for r in refs:
            prov |= frame.resolve(r)
        tgt = alias or (refs[0] if refs else None)
        return tgt, prov

    def _parse_select_expr(self, frame: ColFrame,
                           expr: str) -> tuple[str, Provenance]:
        """Parse a selectExpr string like 'amount * qty as total' via sqlglot."""
        try:
            import sqlglot
            from sqlglot import exp
            parsed = sqlglot.parse_one(f"SELECT {expr}", read="spark")
            proj = parsed.find(exp.Select).expressions[0]
            tgt = proj.alias_or_name
            prov: Provenance = set()
            for c in proj.find_all(exp.Column):
                prov |= frame.resolve(c.name)
            return tgt or expr, prov
        except Exception:
            return expr, set()

    # -- spark.sql() -----------------------------------------------------------
    def _is_spark_sql(self, base: ast.AST, methods: list[tuple[str, ast.Call]]) -> bool:
        return (
            isinstance(base, ast.Name)
            and base.id == "spark"
            and len(methods) == 1
            and methods[0][0] == "sql"
        )

    def _first_sql_arg(self, methods: list[tuple[str, ast.Call]]) -> str | None:
        call = methods[0][1]
        if not call.args:
            return None
        a = call.args[0]
        lit = _str_literal(a)
        if lit:
            return lit
        if isinstance(a, ast.JoinedStr):  # f-string — keep literal parts
            return "".join(
                v.value for v in a.values
                if isinstance(v, ast.Constant) and isinstance(v.value, str)
            )
        return None

    def _emit_sql(self, sql: str) -> None:
        edges = sql_to_edges(sql, notebook=self.notebook, unit=self.unit)
        self.edges.extend(edges)

    # -- write emission --------------------------------------------------------
    def _emit_write(self, frame: ColFrame, method: str, target_arg: str,
                    call: ast.Call) -> None:
        tgt_type, tgt_qname = _qname_for(target_arg)
        out_cols = frame.output_columns()

        # Group column pairs by their source table.
        by_source: dict[str, list[tuple[str, str]]] = {}
        for tgt_col in out_cols:
            for src_qname, src_col in frame.resolve(tgt_col):
                by_source.setdefault(src_qname, []).append((src_col, tgt_col))

        proc = f"spark:{self.notebook}:{self.unit}:{method}:{target_arg}"
        sources = by_source.keys() or frame.sources
        for src_qname in sources:
            cols = by_source.get(src_qname)
            self.edges.append(LineageEdge(
                source_qname=src_qname,
                source_type=frame.source_type,
                target_qname=tgt_qname,
                target_type=tgt_type,
                process_name=proc,
                process_type=("spark_save_as_table"
                              if method == "saveAsTable" else "spark_write"),
                artifact_ref=self._artifact,
                columns=cols or None,
                extra={"notebook": self.notebook, "unit": self.unit},
            ))


def sql_to_edges(sql: str, *, notebook: str, unit: str) -> list[LineageEdge]:
    """Extract column edges from a SQL string embedded in notebook code.

    Handles CREATE VIEW / CREATE TABLE AS / INSERT...SELECT by delegating to the
    shared sqlglot column extractor.  Returns [] when the statement is not a
    derivation we can map.
    """
    try:
        import sqlglot
        from sqlglot import exp
    except Exception:
        return []
    try:
        parsed = sqlglot.parse_one(sql, read="spark")
    except Exception:
        return []
    if parsed is None:
        return []

    # Determine the target table name (CREATE / INSERT).
    target = None
    if isinstance(parsed, exp.Create):
        tgt = parsed.this
        if isinstance(tgt, exp.Schema):
            tgt = tgt.this
        if isinstance(tgt, exp.Table):
            target = tgt.sql(dialect="spark")
    elif isinstance(parsed, exp.Insert):
        tgt = parsed.this
        if isinstance(tgt, exp.Schema):
            tgt = tgt.this
        if isinstance(tgt, exp.Table):
            target = tgt.sql(dialect="spark")
    if target is None:
        return []

    def _q(schema: str, table: str) -> str:
        ref = f"{schema}.{table}" if schema else table
        return f"spark://{ref}"

    col_edges, _unknown = extract_column_edges(
        sql, dialect="spark", default_schema="", schema={}, qname_for=_q,
    )

    # Fold (src_qname, src_col, tgt_col) triples into LineageEdges per source.
    by_source: dict[str, list[tuple[str, str]]] = {}
    for src_qname, src_col, tgt_col in col_edges:
        by_source.setdefault(src_qname, []).append((src_col, tgt_col))

    _tt, tgt_qname = _qname_for(target)
    proc = f"spark:{notebook}:{unit}:sql:{target}"
    edges: list[LineageEdge] = []
    for src_qname, cols in by_source.items():
        edges.append(LineageEdge(
            source_qname=src_qname,
            source_type="fabric_lakehouse_table",
            target_qname=tgt_qname,
            target_type="fabric_lakehouse_table",
            process_name=proc,
            process_type="spark_sql",
            artifact_ref=notebook,
            columns=cols or None,
            extra={"notebook": notebook, "unit": unit},
        ))
    return edges


def analyze_python(src: str, *, notebook: str, unit: str = "module") -> list[LineageEdge]:
    """Parse one Python source unit and return its column-level lineage edges."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    return _SparkVisitor(notebook, unit).run(tree)
