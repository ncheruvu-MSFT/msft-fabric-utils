"""
Purview + Fabric governance bootstrap.

Performs (idempotent):
  1. Authenticates with a Service Principal (or DefaultAzureCredential as fallback)
  2. Creates governance domains in Microsoft Purview Unified Catalog
  3. Registers the Microsoft Fabric tenant as a Purview data source
  4. Creates a recurring scan and triggers an immediate run

Usage:
    python scripts/purview_fabric_governance.py            # real run
    python scripts/purview_fabric_governance.py --dry-run  # show planned calls only

Required env (see .env.example):
    TENANT_ID, SPN_CLIENT_ID, SPN_CLIENT_SECRET,
    PURVIEW_ACCOUNT, PURVIEW_COLLECTION_ID,
    FABRIC_TENANT_ID

References:
    https://learn.microsoft.com/purview/register-scan-fabric-tenant
    https://learn.microsoft.com/rest/api/purview/datamapdataplane/data-sources/create-or-update
    https://learn.microsoft.com/rest/api/purview/datamapdataplane/scans/create-or-update
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from dataclasses import dataclass
from typing import Any

import requests
from azure.identity import ClientSecretCredential, DefaultAzureCredential
from dotenv import load_dotenv

PURVIEW_RESOURCE = "https://purview.azure.net/.default"
TIMEOUT = 60


# ---------------------------------------------------------------- domain plan
DOMAINS: list[dict[str, str]] = [
    {"name": "Sales & Revenue",      "description": "CFO org — revenue, billing, customer LTV."},
    {"name": "Operations",           "description": "COO org — supply chain, shipments, inventory."},
    {"name": "Customer 360",         "description": "CMO org — unified customer view across systems."},
    {"name": "Platform & Telemetry", "description": "Platform team — Spark, capacity, DevOps telemetry."},
]


# --------------------------------------------------------------------- helpers
@dataclass
class Ctx:
    tenant_id: str
    spn_client_id: str | None
    spn_client_secret: str | None
    purview_account: str
    purview_collection: str
    fabric_tenant_id: str
    dry_run: bool

    @property
    def purview_endpoint(self) -> str:
        return f"https://{self.purview_account}.purview.azure.com"


def load_ctx(dry_run: bool) -> Ctx:
    load_dotenv()
    required = ["TENANT_ID", "PURVIEW_ACCOUNT", "PURVIEW_COLLECTION_ID", "FABRIC_TENANT_ID"]
    missing = [k for k in required if not os.getenv(k)]
    if missing and not dry_run:
        raise SystemExit(f"Missing env vars: {missing}. Copy .env.example to .env and fill in.")
    return Ctx(
        tenant_id=os.getenv("TENANT_ID", "<TENANT_ID>"),
        spn_client_id=os.getenv("SPN_CLIENT_ID"),
        spn_client_secret=os.getenv("SPN_CLIENT_SECRET"),
        purview_account=os.getenv("PURVIEW_ACCOUNT", "<PURVIEW_ACCOUNT>"),
        purview_collection=os.getenv("PURVIEW_COLLECTION_ID", "<COLLECTION_ID>"),
        fabric_tenant_id=os.getenv("FABRIC_TENANT_ID", "<FABRIC_TENANT_ID>"),
        dry_run=dry_run,
    )


def get_token(ctx: Ctx) -> str:
    if ctx.dry_run:
        return "<token>"
    # 1) Pre-fetched token wins (avoids DefaultAzureCredential subprocess issues).
    pre = os.getenv("PURVIEW_ACCESS_TOKEN")
    if pre:
        return pre.strip()
    if ctx.spn_client_id and ctx.spn_client_secret:
        cred = ClientSecretCredential(ctx.tenant_id, ctx.spn_client_id, ctx.spn_client_secret)
    else:
        # Pin the tenant so multi-tenant SSO sessions resolve to the right one.
        cred = DefaultAzureCredential(
            interactive_browser_tenant_id=ctx.tenant_id,
            shared_cache_tenant_id=ctx.tenant_id,
            visual_studio_code_tenant_id=ctx.tenant_id,
        )
    return cred.get_token(PURVIEW_RESOURCE, tenant_id=ctx.tenant_id).token


def call(ctx: Ctx, method: str, url: str, token: str, *, body: dict | None = None) -> dict[str, Any]:
    """Single REST helper. Honors --dry-run."""
    if ctx.dry_run:
        print(f"[dry-run] {method} {url}")
        if body:
            print(json.dumps(body, indent=2))
        return {"dryRun": True}

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    resp = requests.request(method, url, headers=headers, json=body, timeout=TIMEOUT)
    if resp.status_code >= 400:
        # Idempotent path: 409 on create-or-update is fine for scans.
        if resp.status_code == 409:
            print(f"  ↪ already exists ({resp.status_code}) — skipping")
            return {"alreadyExists": True}
        print(f"  ✗ {method} {url}\n    HTTP {resp.status_code}: {resp.text}", file=sys.stderr)
        resp.raise_for_status()
    return resp.json() if resp.text else {}


# -------------------------------------------------------------- 1) domains
def create_governance_domains(ctx: Ctx, token: str) -> dict:
    """Create Unified Catalog governance domains (idempotent by name).
    Returns {name: id} mapping for downstream use."""
    print("\n[1/3] Creating Unified Catalog governance domains")
    base = f"{ctx.purview_endpoint}/datagovernance/catalog/businessdomains"

    # 1a) list existing to keep idempotent
    existing = call(ctx, "GET", base, token).get("value", []) or []
    by_name = {d.get("name"): d.get("id") for d in existing}

    result: dict = {}
    for d in DOMAINS:
        if d["name"] in by_name:
            print(f"  • {d['name']}  (exists, id={by_name[d['name']]})")
            result[d["name"]] = by_name[d["name"]]
            continue
        body = {
            "name": d["name"],
            "description": d["description"],
            "type": "FunctionalUnit",
            "status": "Draft",
            "parentId": None,
        }
        print(f"  • {d['name']}  (creating)")
        resp = call(ctx, "POST", base, token, body=body)
        result[d["name"]] = resp.get("id")
    return result


# -------------------------------------------------------------- 2) Fabric source
def register_fabric_source(ctx: Ctx, token: str) -> str:
    """Returns the data source name."""
    print("\n[2/3] Registering Microsoft Fabric tenant as Purview data source")
    ds_name = "fabric-tenant"
    url = (
        f"{ctx.purview_endpoint}/scan/datasources/{ds_name}"
        f"?api-version=2023-09-01"
    )
    body = {
        "kind": "Fabric",
        "name": ds_name,
        "properties": {
            "tenant": ctx.fabric_tenant_id,
            "collection": {"referenceName": ctx.purview_collection, "type": "CollectionReference"},
        },
    }
    print(f"  • source={ds_name}  fabricTenant={ctx.fabric_tenant_id}")
    call(ctx, "PUT", url, token, body=body)
    return ds_name


# -------------------------------------------------------------- 3) scan + run
def create_and_run_scan(ctx: Ctx, token: str, ds_name: str) -> None:
    print("\n[3/3] Creating recurring scan + triggering an immediate run")
    scan_name = "fabric-tenant-weekly"
    ruleset_name = "custom-powerbi"
    base = f"{ctx.purview_endpoint}/scan/datasources/{ds_name}/scans/{scan_name}"

    # 3a) Provision a Custom PowerBI scan ruleset (the System PowerBI ruleset is
    # only auto-created on the first portal-driven scan, which would block
    # hands-free demos. A Custom ruleset works without that bootstrap.)
    ruleset_url = f"{ctx.purview_endpoint}/scan/scanrulesets/{ruleset_name}?api-version=2023-09-01"
    ruleset_body = {
        "kind": "PowerBI",
        "properties": {
            "description": "Default Fabric/PowerBI scan ruleset (auto-provisioned).",
            "excludedSystemClassifications": [],
            "includedCustomClassificationRuleNames": [],
        },
        "scanRulesetType": "Custom",
        "status": "Enabled",
    }
    print(f"  • ruleset={ruleset_name} (Custom, kind=PowerBI)")
    call(ctx, "PUT", ruleset_url, token, body=ruleset_body)

    # 3b) Create or update the scan to use the custom ruleset (managed identity auth).
    create_url = f"{base}?api-version=2023-09-01"
    create_body = {
        "kind": "FabricMsi",
        "properties": {
            "scanRulesetName": ruleset_name,
            "scanRulesetType": "Custom",
            "collection": {"referenceName": ctx.purview_collection, "type": "CollectionReference"},
            "includePersonalWorkspaces": False,
        },
    }
    print(f"  • scan={scan_name}")
    call(ctx, "PUT", create_url, token, body=create_body)

    # Set a recurring trigger — Sundays 02:00 UTC.
    trigger_url = f"{base}/triggers/default?api-version=2023-09-01"
    trigger_body = {
        "properties": {
            "recurrence": {
                "frequency": "Week",
                "interval": 1,
                "schedule": {"hours": [2], "minutes": [0], "weekDays": ["Sunday"]},
                "timezone": "UTC",
            },
            "incrementalScanStartTime": None,
        }
    }
    print("  • trigger=Sundays 02:00 UTC (weekly)")
    call(ctx, "PUT", trigger_url, token, body=trigger_body)

    # Run it now (POST /run triggers an on-demand run; service assigns runId).
    run_url = f"{base}/run?api-version=2023-09-01"
    print("  • triggering on-demand run (POST .../run)")
    call(ctx, "POST", run_url, token, body={"scanLevel": "Incremental"})


# ------------------------------------------------------------------------ main
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Print planned REST calls only.")
    args = parser.parse_args()

    ctx = load_ctx(args.dry_run)
    print(f"Purview endpoint: {ctx.purview_endpoint}")
    print(f"Fabric tenant:    {ctx.fabric_tenant_id}")
    print(f"Mode:             {'DRY-RUN' if ctx.dry_run else 'LIVE'}")

    token = get_token(ctx)
    create_governance_domains(ctx, token)
    ds_name = register_fabric_source(ctx, token)
    create_and_run_scan(ctx, token, ds_name)
    print("\n✓ done")


if __name__ == "__main__":
    main()
