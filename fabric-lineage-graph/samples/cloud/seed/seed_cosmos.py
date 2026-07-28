"""samples/cloud/seed/seed_cosmos.py

Creates / upserts sample documents in the two containers provisioned by the
bicep template:
  * telemetry/web_sessions   — clickstream events (no PII)
  * telemetry/iot_telemetry  — device readings (no PII)

Auth: DefaultAzureCredential. The deployer (you) gets `Cosmos DB Built-in Data
Contributor` via the deploy script, so this works without keys.

These containers are CONSUMERS of upstream data in the demo lineage. The
cross-system edges (mssql -> cosmos for example) are declared in
samples/cloud/cross_system_edges.json — see harvesters/declared.py.
"""
from __future__ import annotations
import os
import sys
import datetime as dt
import uuid

from azure.cosmos import CosmosClient, PartitionKey
from azure.identity import DefaultAzureCredential


def _env(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        print(f"ERROR: env var {name} not set (run deploy.ps1 first to populate .env.cloud)",
              file=sys.stderr)
        sys.exit(2)
    return v


def main() -> int:
    endpoint = _env("COSMOS_ENDPOINT")
    database_name = _env("COSMOS_DATABASE")

    cred = DefaultAzureCredential()
    client = CosmosClient(endpoint, credential=cred)
    db = client.get_database_client(database_name)

    # web_sessions
    sessions = db.get_container_client("web_sessions")
    for i in range(5):
        sessions.upsert_item({
            "id": str(uuid.uuid4()),
            "sessionId": f"sess-{i:03d}",
            "userAgent": "Mozilla/5.0",
            "ts": dt.datetime.utcnow().isoformat(),
            "path": "/products" if i % 2 else "/home",
            "durationMs": 1000 + i * 250,
        })
    print(f"web_sessions:  upserted 5 documents")

    # iot_telemetry
    iot = db.get_container_client("iot_telemetry")
    for i in range(5):
        iot.upsert_item({
            "id": str(uuid.uuid4()),
            "deviceId": f"device-{i:03d}",
            "tempC": 20.0 + i * 1.5,
            "humidity": 45 + i,
            "ts": dt.datetime.utcnow().isoformat(),
        })
    print(f"iot_telemetry: upserted 5 documents")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
