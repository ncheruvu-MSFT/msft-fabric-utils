"""Seed an Azure Databricks workspace with tables + views so the live
harvester has lineage to discover.

Workflow:
  1. Look up an existing serverless SQL warehouse (or create the smallest XS one).
  2. Run idempotent CREATE SCHEMA / CREATE TABLE / CREATE OR REPLACE VIEW
     against the default `hive_metastore` catalog (UC-agnostic).
  3. Write DATABRICKS_WAREHOUSE_ID + DATABRICKS_HTTP_PATH back into .env.cloud so
     the harvester + validation runner can reuse the same warehouse.

Auth: Entra ID OAuth via DefaultAzureCredential -> AzureDatabricks resource
(`2ff814a6-3304-4ab8-85cb-cd0e6f879c1d`). No PATs, no SP secrets — works
under MCAPS because the token is acquired from the signed-in user.
"""
from __future__ import annotations
import os
import pathlib
import sys
import time
import json
import requests
from azure.identity import DefaultAzureCredential

# AzureDatabricks resource ID (well-known, same in every tenant)
AAD_DATABRICKS_RESOURCE_ID = "2ff814a6-3304-4ab8-85cb-cd0e6f879c1d"
ARM_RESOURCE_ID = "https://management.azure.com/"

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
ENV_FILE = REPO_ROOT / ".env.cloud"


def _load_env() -> None:
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def _append_env(updates: dict) -> None:
    """Idempotently update or append KEY=VALUE lines in .env.cloud."""
    lines = ENV_FILE.read_text(encoding="utf-8").splitlines() if ENV_FILE.exists() else []
    keys = set(updates.keys())
    out = []
    seen = set()
    for line in lines:
        if "=" in line and not line.lstrip().startswith("#"):
            k = line.split("=", 1)[0].strip()
            if k in keys:
                out.append(f"{k}={updates[k]}")
                seen.add(k)
                continue
        out.append(line)
    for k, v in updates.items():
        if k not in seen:
            out.append(f"{k}={v}")
    ENV_FILE.write_text("\n".join(out) + "\n", encoding="utf-8")


def _ensure_workspace_url() -> str:
    host = os.environ.get("DATABRICKS_HOST")
    if not host:
        print("FATAL: DATABRICKS_HOST not set. Run deploy_databricks.ps1 first.")
        sys.exit(2)
    host = host.rstrip("/")
    if not host.startswith("http"):
        host = f"https://{host}"
    return host


def _ensure_warehouse(base: str, dbx_token: str) -> tuple[str, str]:
    """Return (warehouse_id, http_path). Creates XS serverless if none exists."""
    headers = {"Authorization": f"Bearer {dbx_token}"}
    r = requests.get(f"{base}/api/2.0/sql/warehouses", headers=headers, timeout=30)
    r.raise_for_status()
    warehouses = r.json().get("warehouses", [])
    for w in warehouses:
        if w.get("enable_serverless_compute") and w.get("cluster_size") == "2X-Small":
            print(f"  reusing warehouse '{w['name']}' (id={w['id']})")
            return w["id"], f"/sql/1.0/warehouses/{w['id']}"

    print("  no XS serverless warehouse found - creating one (auto-stops at 10 min idle)")
    body = {
        "name": "lineage-demo-xs",
        "cluster_size": "2X-Small",
        "min_num_clusters": 1,
        "max_num_clusters": 1,
        "auto_stop_mins": 10,
        "enable_serverless_compute": True,
        "warehouse_type": "PRO",
        "spot_instance_policy": "COST_OPTIMIZED",
    }
    r = requests.post(f"{base}/api/2.0/sql/warehouses", headers=headers, json=body, timeout=60)
    r.raise_for_status()
    wid = r.json()["id"]
    print(f"  created warehouse id={wid}, waiting for RUNNING state...")
    for _ in range(60):  # up to ~5 min
        time.sleep(5)
        s = requests.get(f"{base}/api/2.0/sql/warehouses/{wid}", headers=headers, timeout=30)
        s.raise_for_status()
        state = s.json().get("state")
        if state == "RUNNING":
            return wid, f"/sql/1.0/warehouses/{wid}"
        if state in ("DELETED", "STOPPED"):
            raise RuntimeError(f"Warehouse landed in {state}")
    raise TimeoutError("Warehouse never reached RUNNING")


def _exec_sql(base: str, dbx_token: str, warehouse_id: str, statement: str) -> None:
    headers = {"Authorization": f"Bearer {dbx_token}"}
    body = {"warehouse_id": warehouse_id, "statement": statement, "wait_timeout": "30s"}
    r = requests.post(
        f"{base}/api/2.0/sql/statements", headers=headers, json=body, timeout=60
    )
    if r.status_code >= 400:
        raise RuntimeError(f"SQL failed [{r.status_code}]: {r.text}\nSQL was:\n{statement}")
    res = r.json()
    state = res.get("status", {}).get("state")
    sid = res.get("statement_id")
    while state in ("PENDING", "RUNNING"):
        time.sleep(1.5)
        g = requests.get(
            f"{base}/api/2.0/sql/statements/{sid}", headers=headers, timeout=30
        )
        g.raise_for_status()
        res = g.json()
        state = res.get("status", {}).get("state")
    if state != "SUCCEEDED":
        raise RuntimeError(f"SQL ended in state={state}: {json.dumps(res)[:500]}\nSQL was:\n{statement}")


DDL_TEMPLATES = [
    "CREATE SCHEMA IF NOT EXISTS {ns}",
    """CREATE TABLE IF NOT EXISTS {ns}.devices (
        device_id STRING,
        manufacturer STRING,
        firmware_version STRING,
        commissioned_at TIMESTAMP
    ) USING DELTA""",
    """CREATE TABLE IF NOT EXISTS {ns}.events (
        event_id STRING,
        device_id STRING,
        event_ts TIMESTAMP,
        temperature DOUBLE,
        humidity DOUBLE,
        battery_pct DOUBLE
    ) USING DELTA""",
    """MERGE INTO {ns}.devices t
       USING (
         SELECT 'd-001' AS device_id, 'AcmeCorp' AS manufacturer,
                '1.4.2' AS firmware_version, TIMESTAMP'2026-01-01 10:00:00' AS commissioned_at
         UNION ALL
         SELECT 'd-002', 'AcmeCorp', '1.4.2', TIMESTAMP'2026-01-15 10:00:00'
         UNION ALL
         SELECT 'd-003', 'WidgetCo', '2.0.0', TIMESTAMP'2026-02-01 10:00:00'
       ) s
       ON t.device_id = s.device_id
       WHEN NOT MATCHED THEN INSERT *""",
    """MERGE INTO {ns}.events t
       USING (
         SELECT 'e-1' AS event_id, 'd-001' AS device_id,
                TIMESTAMP'2026-06-01 08:00:00' AS event_ts,
                22.4 AS temperature, 0.45 AS humidity, 0.98 AS battery_pct
         UNION ALL
         SELECT 'e-2', 'd-002', TIMESTAMP'2026-06-02 08:00:00', 23.1, 0.42, 0.95
         UNION ALL
         SELECT 'e-3', 'd-001', TIMESTAMP'2026-06-03 08:00:00', 24.0, 0.40, 0.91
       ) s
       ON t.event_id = s.event_id
       WHEN NOT MATCHED THEN INSERT *""",
    """CREATE OR REPLACE VIEW {ns}.devices_v AS
       SELECT device_id, manufacturer, firmware_version
       FROM {ns}.devices""",
    """CREATE OR REPLACE VIEW {ns}.events_recent_v AS
       SELECT event_id, device_id, event_ts, temperature, humidity
       FROM {ns}.events
       WHERE event_ts >= current_timestamp() - INTERVAL 90 DAYS""",
    """CREATE OR REPLACE VIEW {ns}.device_event_summary_v AS
       SELECT
         d.device_id,
         d.manufacturer,
         COUNT(*) AS event_count,
         AVG(e.temperature) AS avg_temp
       FROM {ns}.devices_v d
       JOIN {ns}.events_recent_v e USING (device_id)
       GROUP BY d.device_id, d.manufacturer""",
]


def main() -> int:
    _load_env()
    base = _ensure_workspace_url()
    catalog = os.environ.get("DATABRICKS_CATALOG", "hive_metastore")
    schema = os.environ.get("DATABRICKS_SCHEMA", "iot")
    ns = f"{catalog}.{schema}"
    print(f"Databricks workspace: {base}")
    print(f"Target namespace:     {ns}")

    cred = DefaultAzureCredential(exclude_interactive_browser_credential=False)
    dbx_token = cred.get_token(f"{AAD_DATABRICKS_RESOURCE_ID}/.default").token

    warehouse_id, http_path = _ensure_warehouse(base, dbx_token)

    ddl = [stmt.format(ns=ns) for stmt in DDL_TEMPLATES]
    print(f"Running {len(ddl)} DDL/DML statements...")
    for stmt in ddl:
        first = stmt.strip().splitlines()[0][:80]
        print(f"  -> {first}")
        _exec_sql(base, dbx_token, warehouse_id, stmt)

    _append_env({
        "DATABRICKS_WAREHOUSE_ID": warehouse_id,
        "DATABRICKS_HTTP_PATH": http_path,
        "DATABRICKS_CATALOG": "hive_metastore",
        "DATABRICKS_SCHEMA": "iot",
    })
    print("OK - Databricks seed complete; .env.cloud updated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
