"""Fabric notebook harvester — column-level static analysis of Spark code.

For each notebook (`.ipynb`) or Python file (`.py`) this:

  * Names every transform by **notebook + cell/function** so the lineage edge
    carries a human process name
    (e.g. `spark:build_gold:enrich_orders:withColumn:NetAmount`).
  * Tracks **column provenance** through PySpark DataFrame chains
    (`select`, `withColumn`, `withColumnRenamed`, `selectExpr`, …) so writes
    emit `(src_col -> tgt_col)` pairs, not just table->table edges.
  * Parses **`spark.sql("…")`** strings through the shared sqlglot column
    extractor so SQL transformations inside notebooks are captured too.

`.ipynb` cells become individual units (named by a leading `# CELL: <name>` or
the preceding markdown title, else `cellNN`).  `.py` files use the enclosing
`def` name, falling back to `module`.

Identity passthroughs (`select("*")`, untouched columns) degrade gracefully to
a table-level edge with `columns=None`.
"""
from __future__ import annotations
import json
import pathlib
import re
from collections.abc import Iterable

from common.schema import LineageEdge
from .base import Harvester
from .spark_columns import analyze_python


_CELL_NAME_RE = re.compile(r"#\s*CELL:\s*(.+)", re.IGNORECASE)
_MD_TITLE_RE = re.compile(r"#+\s*(.+)")


def _slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", text.strip()).strip("_")[:40] or "cell"


def _cell_unit_name(source: str, index: int, prev_md_title: str | None) -> str:
    """Pick a readable unit name for a code cell."""
    m = _CELL_NAME_RE.search(source)
    if m:
        return _slug(m.group(1))
    if prev_md_title:
        return _slug(prev_md_title)
    return f"cell{index:02d}"


def parse_notebook(path: pathlib.Path) -> list[LineageEdge]:
    notebook = path.stem
    edges: list[LineageEdge] = []

    if path.suffix == ".ipynb":
        try:
            nb = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
        prev_md_title: str | None = None
        code_index = 0
        for cell in nb.get("cells", []):
            ctype = cell.get("cell_type")
            text = "".join(cell.get("source", []))
            if ctype == "markdown":
                m = _MD_TITLE_RE.search(text)
                prev_md_title = m.group(1) if m else None
                continue
            if ctype != "code" or not text.strip():
                continue
            code_index += 1
            unit = _cell_unit_name(text, code_index, prev_md_title)
            prev_md_title = None
            edges.extend(analyze_python(text, notebook=notebook, unit=unit))
        return edges

    # Plain .py — analyze the whole module; the visitor names units by the
    # enclosing function, falling back to "module".
    try:
        src = path.read_text(encoding="utf-8")
    except OSError:
        return []
    edges.extend(analyze_python(src, notebook=notebook, unit="module"))
    return edges


class NotebookHarvester(Harvester):
    name = "notebook"

    def __init__(self, root: str | pathlib.Path) -> None:
        self.root = pathlib.Path(root)

    def harvest(self) -> Iterable[LineageEdge]:
        for ext in ("*.ipynb", "*.py"):
            for f in self.root.rglob(ext):
                yield from parse_notebook(f)
