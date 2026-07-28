"""Delta materializer / throughput harness — runs locally OR against OneLake.

Writes one EMPTY Delta table (0 rows, typed schema) per bronze/silver/gold table
in the manifest, and reports creation throughput. This is the "how fast can we
stand up thousands of tables" measurement.

* Local (default): writes under --out (real Delta tables, ~KB each) with NO cloud
  cost — proves scale + throughput.
* OneLake: pass --onelake "abfss://<workspace>@onelake.dfs.fabric.microsoft.com/<lh>.Lakehouse/Tables"
  and the tool authenticates with an Entra token (azure-identity) so the tables
  land in a real Fabric Lakehouse.

Usage:
    python materialize_delta.py --limit 2000
    python materialize_delta.py --limit 10000
    python materialize_delta.py --limit 2000 --onelake abfss://ws@onelake.dfs.fabric.microsoft.com/lake.Lakehouse/Tables
"""
from __future__ import annotations

import argparse
import json
import os
import time

import pyarrow as pa
from deltalake import write_deltalake

DELTA_LAYERS = {"bronze", "silver", "gold"}

PATYPES = {
    "Id": pa.int64(), "CustomerId": pa.int64(), "ProductId": pa.int64(),
    "Qty": pa.int32(), "Amount": pa.decimal128(18, 2),
    "Discount": pa.decimal128(5, 4), "Cost": pa.decimal128(18, 2),
    "NetAmount": pa.decimal128(18, 2), "TotalRevenue": pa.decimal128(18, 2),
    "Margin": pa.decimal128(18, 2), "Region": pa.string(), "Status": pa.string(),
    "Channel": pa.string(), "CreatedAt": pa.timestamp("us"),
    "UpdatedAt": pa.timestamp("us"),
}


def _schema(cols: list[str]) -> pa.Schema:
    return pa.schema([(c, PATYPES.get(c, pa.string())) for c in cols])


def _storage_options(onelake: str | None) -> dict | None:
    if not onelake:
        return None
    from azure.identity import DefaultAzureCredential
    cred = DefaultAzureCredential(exclude_interactive_browser_credential=False)
    token = cred.get_token("https://storage.azure.com/.default").token
    return {"bearer_token": token, "use_fabric_endpoint": "true"}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", default=os.path.join("out", "scale", "lakehouses.json"))
    ap.add_argument("--out", default=os.path.join("out", "delta"), help="local base dir")
    ap.add_argument("--onelake", default=None, help="OneLake Tables ABFSS base (overrides --out)")
    ap.add_argument("--limit", type=int, default=2000)
    args = ap.parse_args()

    with open(args.manifest, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    base = args.onelake.rstrip("/") if args.onelake else args.out
    opts = _storage_options(args.onelake)
    empty_cache: dict[tuple, pa.Table] = {}

    created = 0
    t0 = time.time()
    for lh, meta in manifest.items():
        schema_name = ("lh_" + lh).replace("-", "_").replace(".", "_")
        for layer, tables in meta["schemas"].items():
            if layer not in DELTA_LAYERS:
                continue
            for t in tables:
                if created >= args.limit:
                    _report(created, t0)
                    return
                cols = tuple(t["columns"])
                if cols not in empty_cache:
                    sch = _schema(list(cols))
                    empty_cache[cols] = pa.Table.from_pylist([], schema=sch)
                tname = t["table"].split(".", 1)[-1].replace("-", "_")
                path = f"{base}/{schema_name}/{tname}"
                write_deltalake(path, empty_cache[cols], mode="overwrite",
                                storage_options=opts)
                created += 1
                if created % 250 == 0:
                    _report(created, t0)
    _report(created, t0)


def _report(created: int, t0: float) -> None:
    dt = time.time() - t0
    rate = created / dt if dt else 0
    print(f"  tables={created:,}  elapsed={dt:,.1f}s  ({rate:.0f} tables/s)", flush=True)


if __name__ == "__main__":
    main()
