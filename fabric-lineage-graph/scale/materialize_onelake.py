# Fabric notebook — materialize the synthetic estate as tiny Delta tables in OneLake.
#
# Run this INSIDE a Microsoft Fabric notebook attached to a (schema-enabled)
# Lakehouse. It reads `lakehouses.json` produced by gen_scale_lineage.py and
# creates one Delta schema per "lakehouse" and an EMPTY Delta table per table in
# the manifest. Empty tables are just a _delta_log + schema (~KB each), so 1000s
# of them cost almost nothing in OneLake storage — the only cost is the capacity
# CU while this runs.
#
# Cost/scale controls:
#   MAX_TABLES   cap the number of tables actually created (raise toward 10_000
#                once you've confirmed throughput). Each CREATE TABLE is a small
#                metadata write, so ~2_000 is a good first pass.
#   DROP_FIRST   drop the schemas first for a clean re-run.
#
# Upload lakehouses.json to the Lakehouse Files area first (Files/scale/), or set
# MANIFEST_PATH to an abfss:// path.

import json
import time

from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

# ---- Config -----------------------------------------------------------------
MANIFEST_PATH = "Files/scale/lakehouses.json"   # relative to the attached Lakehouse
MAX_TABLES = 2000                                 # raise toward 10_000 to go full-scale
DROP_FIRST = False
SCHEMA_PREFIX = "lh_"                             # each lakehouse -> one Delta schema
DELTA_LAYERS = {"bronze", "silver", "gold"}      # only these live in OneLake;
#   external sources (RDBMS/Cosmos/files) and Power BI exist only in lineage metadata.

# Map generator layer -> a minimal column set (kept tiny on purpose).
COLTYPES = {
    "Id": "bigint", "CustomerId": "bigint", "ProductId": "bigint",
    "Amount": "decimal(18,2)", "Qty": "int", "Discount": "decimal(5,4)",
    "Cost": "decimal(18,2)", "NetAmount": "decimal(18,2)",
    "TotalRevenue": "decimal(18,2)", "Margin": "decimal(18,2)",
    "Region": "string", "Status": "string", "Channel": "string",
    "CreatedAt": "timestamp", "UpdatedAt": "timestamp",
}


def _coltype(col: str) -> str:
    return COLTYPES.get(col, "string")


def load_manifest(path: str) -> dict:
    # Works for a Files/ relative path via the local FUSE mount, else abfss.
    if path.startswith("abfss://") or path.startswith("Files/") is False:
        raw = "".join(r.value for r in spark.read.text(path).collect())
    else:
        with open("/lakehouse/default/" + path, "r", encoding="utf-8") as f:
            raw = f.read()
    return json.loads(raw)


def main() -> None:
    manifest = load_manifest(MANIFEST_PATH)
    print(f"Manifest: {len(manifest)} lakehouses")

    created = 0
    schemas = 0
    t0 = time.time()

    for lh, meta in manifest.items():
        schema = (SCHEMA_PREFIX + lh).replace("-", "_").replace(".", "_")
        if DROP_FIRST:
            spark.sql(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
        spark.sql(f"CREATE SCHEMA IF NOT EXISTS {schema}")
        schemas += 1

        for layer, tables in meta["schemas"].items():
            if layer not in DELTA_LAYERS:
                continue  # external / Power BI assets are lineage-only
            for t in tables:
                if created >= MAX_TABLES:
                    _report(created, schemas, t0)
                    print(f"Hit MAX_TABLES={MAX_TABLES}. Raise it to go further.")
                    return
                # table name: <layer>_<name-without-layer-prefix>
                tname = t["table"].split(".", 1)[-1].replace("-", "_")
                cols = ", ".join(f"`{c}` {_coltype(c)}" for c in t["columns"])
                spark.sql(
                    f"CREATE TABLE IF NOT EXISTS {schema}.`{tname}` ({cols}) USING DELTA"
                )
                created += 1
                if created % 250 == 0:
                    _report(created, schemas, t0)

    _report(created, schemas, t0)
    print("Done.")


def _report(created: int, schemas: int, t0: float) -> None:
    dt = time.time() - t0
    rate = created / dt if dt else 0
    print(f"  schemas={schemas}  tables={created:,}  elapsed={dt:,.0f}s  ({rate:.0f} tables/s)")


main()
