"""
Validate gold-layer data contracts against the live Fabric SQL endpoint.

Used in the CI step "Run contracts vs UAT" of the ADO release pipeline.
Exits non-zero on any contract violation so the pipeline fails the PR.

Contract format: see contracts/gold/fact_sales.yml
"""
from __future__ import annotations

import argparse
import glob
import os
import sys
from typing import Any

import requests
import yaml
from azure.identity import DefaultAzureCredential

FABRIC_SQL_RESOURCE = "https://analysis.windows.net/powerbi/api/.default"


def load_contract(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def get_token() -> str:
    return DefaultAzureCredential().get_token(FABRIC_SQL_RESOURCE).token


def query_schema(sql_endpoint: str, db: str, table: str, token: str) -> list[dict[str, Any]]:
    """Hit the Fabric SQL endpoint via REST query API for INFORMATION_SCHEMA."""
    schema, name = table.split(".", 1)
    sql = (
        "SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH, "
        "NUMERIC_PRECISION, NUMERIC_SCALE "
        f"FROM {db}.INFORMATION_SCHEMA.COLUMNS "
        f"WHERE TABLE_SCHEMA = '{schema}' AND TABLE_NAME = '{name}'"
    )
    resp = requests.post(
        f"{sql_endpoint}/v1.0/myorg/queries",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": sql},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json().get("results", [])


def validate(contract: dict[str, Any], live: list[dict[str, Any]]) -> list[str]:
    errs: list[str] = []
    live_by_name = {row["COLUMN_NAME"]: row for row in live}

    for col in contract["columns"]:
        actual = live_by_name.get(col["name"])
        if not actual:
            errs.append(f"missing column: {col['name']}")
            continue
        expected_type = col["type"].split("(")[0].lower()
        if actual["DATA_TYPE"].lower() != expected_type:
            errs.append(
                f"type drift on {col['name']}: "
                f"expected {col['type']}, got {actual['DATA_TYPE']}"
            )
        nullable_actual = actual["IS_NULLABLE"] == "YES"
        if col.get("nullable", True) is False and nullable_actual:
            errs.append(f"nullability drift on {col['name']}: expected NOT NULL")

    return errs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("contracts", nargs="+", help="Glob(s) to contract YAML files.")
    parser.add_argument("--sql-endpoint", default=os.getenv("FABRIC_SQL_ENDPOINT"))
    parser.add_argument("--db", default=os.getenv("FABRIC_LAKEHOUSE_DB", "analytics"))
    args = parser.parse_args()

    if not args.sql_endpoint:
        print("FABRIC_SQL_ENDPOINT not set", file=sys.stderr)
        return 2

    token = get_token()
    failures = 0
    for pattern in args.contracts:
        for path in glob.glob(pattern):
            contract = load_contract(path)
            print(f"→ {contract['table']}  ({path})")
            try:
                live = query_schema(args.sql_endpoint, args.db, contract["table"], token)
            except requests.HTTPError as ex:
                print(f"  ✗ HTTP {ex.response.status_code}: {ex.response.text}", file=sys.stderr)
                failures += 1
                continue
            errs = validate(contract, live)
            if errs:
                failures += 1
                for e in errs:
                    print(f"  ✗ {e}")
            else:
                print("  ✓ ok")

    if failures:
        print(f"\n{failures} contract(s) failed", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
