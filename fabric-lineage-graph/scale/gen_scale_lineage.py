"""Synthetic lineage generator — mimic a large data estate for scalability tests.

Generates a realistic medallion lineage graph spanning many "lakehouses" without
provisioning anything: pure stdlib, deterministic (seeded), zero cost.

Outputs (under --out, default ``out/scale``):

* ``lakehouses.json``      manifest: lakehouse -> schema/layer -> tables -> columns
                           (consumed by the OneLake materializer + harvester)
* ``table_edges.json``     table-level LineageEdge[] (same shape as the app's
                           dataClient.ts / rayfin LineageEdge entity)
* ``column_edges.full.json`` complete ScannedColumnGraph (every column edge)
* ``column_edges.json``    a k-hop subgraph capped to ``--col-cap`` assets so the
                           browser column-graph view stays renderable

The medallion flows across lakehouses so the global graph is one big connected
DAG:  ingest (source/bronze)  ->  curate (silver)  ->  mart (gold)  ->  serve
(semantic/report).

Usage:
    python gen_scale_lineage.py --lakehouses 50 --tables-per 200 --cols 8
    python gen_scale_lineage.py --lakehouses 50 --tables-per 40 --seed 7
"""
from __future__ import annotations

import argparse
import json
import os
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

# Global medallion layer order — index drives the "flow direction".
LAYERS = ["source", "bronze", "silver", "gold", "semantic", "report"]
LAYER_IX = {name: i for i, name in enumerate(LAYERS)}

# Which layers each band of lakehouses produces, and how many of the 50 LHs.
# (fractions are scaled to the actual --lakehouses count).
BANDS = [
    ("ingest", ["source", "bronze"], 0.30),
    ("curate", ["silver"], 0.40),
    ("mart", ["gold"], 0.20),
    ("serve", ["semantic", "report"], 0.10),
]

# process_type by target layer (matches common/schema.py KNOWN_PROCESS_TYPES).
PROCESS_BY_TARGET = {
    "bronze": ("adf_copy", "adf"),
    "silver": ("spark_write", "spark"),
    "gold": ("tsql_insert", "tsql"),
    "semantic": ("pbi_m_step", "pbi"),
    "report": ("pbi_dax_measure", "pbi"),
}
TYPE_BY_LAYER = {
    "source": "azure_sql_table",
    "bronze": "fabric_lakehouse_table",
    "silver": "fabric_lakehouse_table",
    "gold": "fabric_warehouse_table",
    "semantic": "powerbi_dataset",
    "report": "powerbi_report",
}

# Human-friendly storage class per layer (shown in lineage + used by the
# materializer to decide what is physically created in OneLake).
STORAGE_BY_LAYER = {
    "source": "external",
    "bronze": "OneLake · Lakehouse Delta",
    "silver": "OneLake · Lakehouse Delta",
    "gold": "OneLake · Warehouse",
    "semantic": "Power BI dataset",
    "report": "Power BI report",
}

# Heterogeneous external source systems feeding the bronze layer. This is what
# makes the graph span RDBMS + NoSQL + Delta Lake + files, not just OneLake.
# (weight, canonical_type, storage_class, scheme, bronze_process_type, proc_prefix)
SOURCE_SYSTEMS = [
    (5, "azure_sql_table", "Azure SQL (RDBMS)", "mssql", "adf_copy", "adf"),
    (3, "azure_postgresql_table", "PostgreSQL (RDBMS)", "postgresql", "adf_copy", "adf"),
    (2, "oracle_table", "Oracle (RDBMS)", "oracle", "adf_copy", "adf"),
    (3, "azure_cosmosdb_sqlapi_collection", "Cosmos DB (NoSQL)", "cosmos", "spark_read", "spark"),
    (3, "databricks_table", "Databricks Delta Lake", "databricks", "spark_read", "spark"),
    (3, "file", "ADLS / OneLake files", "abfss", "spark_read", "spark"),
]
_SOURCE_POOL = [s for s in SOURCE_SYSTEMS for _ in range(s[0])]

TRANSFORMS = [
    "copy", "cast", "trim", "rename", "filter", "join key", "dedupe",
    "SUM by region", "coalesce", "passthrough", "upper()", "RLS view",
]

DOMAINS = [
    "sales", "finance", "hr", "supply", "marketing", "product", "risk",
    "ops", "iot", "web", "billing", "support", "inventory", "logistics",
    "crm", "erp", "pricing", "fraud", "loyalty", "catalog",
]


@dataclass
class Table:
    lh: str            # lakehouse id, e.g. lh_03_finance
    layer: str
    name: str          # schema-qualified table name, e.g. silver.orders_clean
    cols: list[str]
    asset_id: str = ""     # stable id used in the column graph
    qname: str = ""        # qualified name for table edges
    stype: str = ""        # canonical asset type (varies for external sources)
    storage: str = ""      # storage class shown in lineage

    def __post_init__(self) -> None:
        self.asset_id = f"{self.lh}.{self.name}".replace(".", "_")
        if not self.qname:
            self.qname = f"fabric://{self.lh}/{self.name}"
        if not self.stype:
            self.stype = TYPE_BY_LAYER.get(self.layer, "fabric_lakehouse_table")
        if not self.storage:
            self.storage = STORAGE_BY_LAYER.get(self.layer, "OneLake · Lakehouse Delta")


def _band_for(index: int, n: int) -> tuple[str, list[str]]:
    """Map a lakehouse index to a medallion band."""
    cum = 0.0
    frac = (index + 0.5) / n
    for band, layers, weight in BANDS:
        cum += weight
        if frac <= cum:
            return band, layers
    return BANDS[-1][0], BANDS[-1][1]


def _mk_columns(rng: random.Random, layer: str, k: int) -> list[str]:
    base = ["Id", "CustomerId", "Amount", "Qty", "Discount", "Region",
            "Status", "CreatedAt", "UpdatedAt", "ProductId", "Channel", "Cost"]
    cols = base[: max(3, min(k, len(base)))]
    # gold/semantic add measures
    if layer in ("gold", "semantic", "report"):
        cols = cols + ["NetAmount", "TotalRevenue", "Margin"][: max(0, k - len(cols) + 3)]
    return cols[:k]


def _assign_source_system(tbl: "Table", rng: random.Random) -> None:
    """Give a source-layer table a heterogeneous external identity."""
    _, ctype, storage, scheme, _proc, _pfx = rng.choice(_SOURCE_POOL)
    dom = tbl.lh.split("_", 2)[-1]
    short = tbl.name.split(".", 1)[-1]
    host = f"{scheme}{rng.randint(1, 6):02d}"
    if scheme == "cosmos":
        tbl.qname = f"cosmos://{host}/{dom}/{short}"
    elif scheme == "abfss":
        tbl.qname = f"abfss://raw@{host}.dfs.core.windows.net/{dom}/{short}"
    elif scheme == "databricks":
        tbl.qname = f"databricks://{host}.azuredatabricks.net/{dom}/bronze/{short}"
    else:  # mssql / postgresql / oracle
        tbl.qname = f"{scheme}://{host}/{dom}/dbo/{short}"
    tbl.stype = ctype
    tbl.storage = storage


def _process_for(up: "Table", tbl: "Table") -> tuple[str, str]:
    """Pick the process artifact type connecting up -> tbl."""
    if tbl.layer == "bronze":
        for _, ctype, _s, _scheme, proc, pfx in SOURCE_SYSTEMS:
            if ctype == up.stype:
                return proc, pfx
        return "adf_copy", "adf"
    return PROCESS_BY_TARGET.get(tbl.layer, ("spark_write", "spark"))


def generate(
    lakehouses: int,
    tables_per: int,
    cols: int,
    cross_prob: float,
    seed: int,
    col_cap: int,
):
    rng = random.Random(seed)
    all_tables: list[Table] = []
    by_layer: dict[str, list[Table]] = {ly: [] for ly in LAYERS}
    lh_manifest: dict[str, dict] = {}

    for li in range(lakehouses):
        domain = DOMAINS[li % len(DOMAINS)]
        lh = f"lh_{li:02d}_{domain}"
        band, layers = _band_for(li, lakehouses)
        lh_manifest[lh] = {"band": band, "domain": domain, "schemas": {}}
        for t in range(tables_per):
            layer = layers[t % len(layers)]
            tname = f"{layer}.{domain}_{layer}_{t:03d}"
            ncol = rng.randint(max(3, cols - 2), cols + 2)
            columns = _mk_columns(rng, layer, ncol)
            tbl = Table(lh=lh, layer=layer, name=tname, cols=columns)
            if layer == "source":
                _assign_source_system(tbl, rng)
            all_tables.append(tbl)
            by_layer[layer].append(tbl)
            lh_manifest[lh]["schemas"].setdefault(layer, []).append(
                {"table": tname, "columns": columns, "qname": tbl.qname,
                 "type": tbl.stype, "storage": tbl.storage}
            )

    # ---- Build edges: each non-source table draws from the previous layer ----
    table_edges: list[dict] = []
    col_edges: list[dict] = []
    assets: dict[str, dict] = {}
    now = datetime(2026, 6, 30, tzinfo=timezone.utc)

    def reg_asset(tbl: Table) -> None:
        if tbl.asset_id not in assets:
            assets[tbl.asset_id] = {"label": f"{tbl.lh}/{tbl.name}", "type": tbl.layer}

    def upstream_pool(layer: str) -> list[Table]:
        ix = LAYER_IX[layer]
        for prev in range(ix - 1, -1, -1):
            pool = by_layer[LAYERS[prev]]
            if pool:
                return pool
        return []

    eid = 0
    for tbl in all_tables:
        reg_asset(tbl)
        pool = upstream_pool(tbl.layer)
        if not pool:
            continue  # a root (source) table
        # prefer same-lakehouse upstream unless we roll a cross-lakehouse edge
        same = [u for u in pool if u.lh == tbl.lh]
        k = rng.randint(1, 2)
        ups: list[Table] = []
        for _ in range(k):
            if same and rng.random() > cross_prob:
                ups.append(rng.choice(same))
            else:
                ups.append(rng.choice(pool))
        proc_type, proc_prefix = PROCESS_BY_TARGET.get(tbl.layer, ("spark_write", "spark"))
        for up in ups:
            reg_asset(up)
            proc_type, proc_prefix = _process_for(up, tbl)
            eid += 1
            table_edges.append({
                "id": str(eid),
                "sourceQname": up.qname,
                "sourceType": up.stype,
                "sourceStorage": up.storage,
                "targetQname": tbl.qname,
                "targetType": tbl.stype,
                "targetStorage": tbl.storage,
                "processName": f"{proc_prefix}:{tbl.name}",
                "processType": proc_type,
                "artifactRef": f"{proc_prefix}/{tbl.lh}/{tbl.name}.json",
                "harvestedAt": (now - timedelta(minutes=eid % 1440)).isoformat(),
            })
            # column edges: map each target column from an upstream column
            for c in tbl.cols:
                src_col = c if c in up.cols else rng.choice(up.cols)
                col_edges.append({
                    "from": f"{up.asset_id}::{src_col}",
                    "to": f"{tbl.asset_id}::{c}",
                    "transform": rng.choice(TRANSFORMS),
                })

    full_graph = {"assets": assets, "edges": col_edges}

    # ---- Capped, renderable column subgraph (BFS from a mart/gold focus) ----
    capped = _cap_subgraph(full_graph, col_cap, rng)

    stats = {
        "lakehouses": lakehouses,
        "tables": len(all_tables),
        "assets": len(assets),
        "table_edges": len(table_edges),
        "column_edges": len(col_edges),
        "capped_assets": len({a for e in capped["edges"] for a in (e["from"].split("::")[0], e["to"].split("::")[0])}),
        "capped_edges": len(capped["edges"]),
    }
    return lh_manifest, table_edges, full_graph, capped, stats


def _cap_subgraph(full: dict, cap: int, rng: random.Random) -> dict:
    """BFS out from a random gold/semantic asset until ``cap`` assets are covered."""
    if cap <= 0 or len(full["assets"]) <= cap:
        return full
    adj: dict[str, set[str]] = {}
    radj: dict[str, set[str]] = {}
    for e in full["edges"]:
        a = e["from"].split("::")[0]
        b = e["to"].split("::")[0]
        adj.setdefault(a, set()).add(b)
        radj.setdefault(b, set()).add(a)
    seeds = [aid for aid, m in full["assets"].items() if m["type"] in ("gold", "semantic")]
    start = rng.choice(seeds or list(full["assets"].keys()))
    keep: set[str] = set()
    frontier = [start]
    while frontier and len(keep) < cap:
        node = frontier.pop(0)
        if node in keep:
            continue
        keep.add(node)
        frontier.extend(adj.get(node, set()))
        frontier.extend(radj.get(node, set()))
    edges = [e for e in full["edges"]
             if e["from"].split("::")[0] in keep and e["to"].split("::")[0] in keep]
    assets = {aid: m for aid, m in full["assets"].items() if aid in keep}
    return {"assets": assets, "edges": edges}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lakehouses", type=int, default=50)
    ap.add_argument("--tables-per", type=int, default=200, help="tables per lakehouse")
    ap.add_argument("--cols", type=int, default=8, help="approx columns per table")
    ap.add_argument("--cross-prob", type=float, default=0.25, help="cross-lakehouse edge probability")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--col-cap", type=int, default=140, help="max assets in the renderable column_edges.json")
    ap.add_argument("--out", default=os.path.join("out", "scale"))
    args = ap.parse_args()

    lh, table_edges, full, capped, stats = generate(
        args.lakehouses, args.tables_per, args.cols, args.cross_prob, args.seed, args.col_cap
    )
    os.makedirs(args.out, exist_ok=True)

    def dump(name: str, obj) -> str:
        path = os.path.join(args.out, name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, separators=(",", ":"))
        return f"{path}  ({os.path.getsize(path) / 1_048_576:.1f} MB)"

    print("Wrote:")
    print("  " + dump("lakehouses.json", lh))
    print("  " + dump("table_edges.json", table_edges))
    print("  " + dump("column_edges.full.json", full))
    print("  " + dump("column_edges.json", capped))
    print("\nStats:")
    for k, v in stats.items():
        print(f"  {k:>14}: {v:,}")


if __name__ == "__main__":
    main()
