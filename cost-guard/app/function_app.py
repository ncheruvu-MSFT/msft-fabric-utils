"""
Cost Guard — nightly Azure cost containment.

Discovers in the current subscription and (unless DRY_RUN) stops:
  - Microsoft.Fabric/capacities in state 'Active'  -> suspend
  - Microsoft.DBforPostgreSQL/flexibleServers in state 'Ready' -> stop
  - Microsoft.Databricks running clusters (only if DATABRICKS_WORKSPACE_URL is set)

Resources tagged KeepRunning=true are skipped.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Iterable

import azure.functions as func
from azure.core.exceptions import HttpResponseError
from azure.identity import DefaultAzureCredential
from azure.mgmt.rdbms.postgresql_flexibleservers import PostgreSQLManagementClient
from azure.mgmt.resource import ResourceManagementClient

SUBSCRIPTION_ID = os.environ["SUBSCRIPTION_ID"]
DRY_RUN = os.environ.get("DRY_RUN", "false").strip().lower() == "true"
TEAMS_WEBHOOK = os.environ.get("TEAMS_WEBHOOK_URL", "").strip()
DATABRICKS_WORKSPACE_URL = os.environ.get("DATABRICKS_WORKSPACE_URL", "").strip().rstrip("/")
SKIP_TAG = "KeepRunning"

ARM_BASE = "https://management.azure.com"
FABRIC_API_VERSION = "2023-11-01"
DATABRICKS_RESOURCE_ID = "2ff814a6-3304-4ab8-85cb-cd0e6f879c1d"

app = func.FunctionApp()


@app.timer_trigger(
    schedule="0 0 20 * * *",
    arg_name="timer",
    run_on_startup=False,
    use_monitor=True,
)
def nightly_cost_guard(timer: func.TimerRequest) -> None:
    started = datetime.now(timezone.utc)
    logging.info(
        "Cost Guard starting | sub=%s | dry_run=%s | databricks=%s",
        SUBSCRIPTION_ID,
        DRY_RUN,
        bool(DATABRICKS_WORKSPACE_URL),
    )

    cred = DefaultAzureCredential(exclude_interactive_browser_credential=True)
    actions: list[str] = []

    actions.extend(_handle_fabric(cred))
    actions.extend(_handle_postgres(cred))
    if DATABRICKS_WORKSPACE_URL:
        actions.extend(_handle_databricks(cred))

    summary = "\n".join(actions) if actions else "(nothing to do — everything already stopped/paused)"
    elapsed = (datetime.now(timezone.utc) - started).total_seconds()
    header = f"Cost Guard {'(DRY RUN)' if DRY_RUN else ''} — {started.isoformat()} — {elapsed:.1f}s"
    logging.info("%s\n%s", header, summary)

    if TEAMS_WEBHOOK:
        _post_teams(f"**{header}**\n```\n{summary}\n```")


def _handle_fabric(cred: DefaultAzureCredential) -> list[str]:
    out: list[str] = []
    rm = ResourceManagementClient(cred, SUBSCRIPTION_ID)
    try:
        capacities = list(
            rm.resources.list(filter="resourceType eq 'Microsoft.Fabric/capacities'")
        )
    except HttpResponseError as e:
        return [f"FAIL list Fabric: {e.message}"]

    for r in capacities:
        if _has_keep_tag(r.tags):
            out.append(f"SKIP Fabric {r.name} (KeepRunning tag)")
            continue
        try:
            full = rm.resources.get_by_id(r.id, api_version=FABRIC_API_VERSION)
            state = (full.properties or {}).get("state")
        except HttpResponseError as e:
            out.append(f"FAIL read Fabric {r.name}: {e.message}")
            continue
        if state != "Active":
            out.append(f"SKIP Fabric {r.name} (state={state})")
            continue
        if DRY_RUN:
            out.append(f"DRY_RUN suspend Fabric {r.name}")
            continue
        try:
            _arm_post(cred, f"{r.id}/suspend", FABRIC_API_VERSION)
            out.append(f"SUSPENDED Fabric {r.name}")
        except Exception as e:
            out.append(f"FAIL suspend Fabric {r.name}: {e}")
    return out


def _handle_postgres(cred: DefaultAzureCredential) -> list[str]:
    out: list[str] = []
    pg = PostgreSQLManagementClient(cred, SUBSCRIPTION_ID)
    try:
        servers = list(pg.servers.list())
    except HttpResponseError as e:
        return [f"FAIL list PG: {e.message}"]

    for s in servers:
        rg = s.id.split("/")[4]
        if _has_keep_tag(s.tags):
            out.append(f"SKIP PG {s.name} (KeepRunning tag)")
            continue
        if s.state != "Ready":
            out.append(f"SKIP PG {s.name} (state={s.state})")
            continue
        if DRY_RUN:
            out.append(f"DRY_RUN stop PG {s.name}")
            continue
        try:
            pg.servers.begin_stop(rg, s.name).result()
            out.append(f"STOPPED PG {s.name}")
        except Exception as e:
            out.append(f"FAIL stop PG {s.name}: {e}")
    return out


def _handle_databricks(cred: DefaultAzureCredential) -> list[str]:
    out: list[str] = []
    try:
        token = cred.get_token(f"{DATABRICKS_RESOURCE_ID}/.default").token
    except Exception as e:
        return [f"FAIL Databricks token: {e}"]

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        clusters = _http_json(
            f"{DATABRICKS_WORKSPACE_URL}/api/2.0/clusters/list",
            headers=headers,
        ).get("clusters", [])
    except Exception as e:
        return [f"FAIL Databricks list: {e}"]

    running_states = {"RUNNING", "PENDING", "RESTARTING", "RESIZING"}
    for c in clusters:
        name = c.get("cluster_name") or c.get("cluster_id")
        state = c.get("state")
        if state not in running_states:
            continue
        if DRY_RUN:
            out.append(f"DRY_RUN terminate cluster {name} (state={state})")
            continue
        try:
            _http_json(
                f"{DATABRICKS_WORKSPACE_URL}/api/2.0/clusters/delete",
                headers=headers,
                body={"cluster_id": c["cluster_id"]},
            )
            out.append(f"TERMINATED cluster {name}")
        except Exception as e:
            out.append(f"FAIL terminate cluster {name}: {e}")
    if not out:
        out.append("Databricks: no running clusters")
    return out


def _arm_post(cred: DefaultAzureCredential, resource_path: str, api_version: str) -> None:
    token = cred.get_token("https://management.azure.com/.default").token
    url = f"{ARM_BASE}{resource_path}?api-version={api_version}"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        if resp.status not in (200, 202, 204):
            raise RuntimeError(f"ARM POST {url} -> {resp.status}")


def _http_json(url: str, headers: dict, body: dict | None = None) -> dict:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    method = "POST" if body is not None else "GET"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = resp.read()
            return json.loads(payload) if payload else {}
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {url} -> {e.code} {e.read().decode('utf-8', 'ignore')}") from e


def _post_teams(text: str) -> None:
    req = urllib.request.Request(
        TEAMS_WEBHOOK,
        data=json.dumps({"text": text}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=15).read()
    except Exception as e:
        logging.warning("Teams webhook POST failed: %s", e)


def _has_keep_tag(tags: dict | None) -> bool:
    if not tags:
        return False
    return str(tags.get(SKIP_TAG, "")).strip().lower() == "true"
