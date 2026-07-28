"""Fabric User Data Function — workflow trigger + access-request API.

Endpoints:
  POST /access-requests          -> trigger Data-Access-Request workflow
  GET  /access-requests/mine     -> list requester's open tasks
  POST /catalog/bulk-update      -> trigger Asset-Curation-Update workflow

The workflow IDs are deterministic (UUIDv5) — same scheme used by
fabric-sdlc-governance/scripts/purview_apply_workflows.py.
"""
from __future__ import annotations
import json
import os
import uuid
import requests

from azure.identity import DefaultAzureCredential


PURVIEW = os.environ.get("PURVIEW_ACCOUNT", "ngpurview")
WF_BASE = f"https://{PURVIEW}.purview.azure.com/workflow"
APIV = "2023-10-01-preview"
NS = uuid.UUID("11111111-1111-1111-1111-111111111111")


def _hdr() -> dict[str, str]:
    tok = DefaultAzureCredential().get_token("https://purview.azure.net/.default").token
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


def _wf_id(name: str) -> str:
    return str(uuid.uuid5(NS, name))


def trigger_access_request(asset_qname: str, permission: str,
                           justification: str, requester_oid: str) -> dict:
    wf_id = _wf_id("Data-Access-Request")
    body = {
        "payload": {
            "assetQualifiedName": asset_qname,
            "permission": permission,
            "justification": justification,
            "requesterOid": requester_oid,
        },
    }
    r = requests.post(f"{WF_BASE}/workflows/{wf_id}/runs?api-version={APIV}",
                      headers=_hdr(), json=body, timeout=60)
    r.raise_for_status()
    return r.json()


def list_my_tasks(requester_oid: str) -> dict:
    r = requests.get(f"{WF_BASE}/workitems?api-version={APIV}&$filter=assignee eq '{requester_oid}'",
                     headers=_hdr(), timeout=60)
    r.raise_for_status()
    return {"value": r.json().get("value", [])}


def trigger_bulk_update(asset_qnames: list[str], description: str | None,
                       tags: list[str] | None) -> dict:
    wf_id = _wf_id("Asset-Curation-Update")
    body = {
        "payload": {
            "assetQualifiedNames": asset_qnames,
            "description": description,
            "tags": tags or [],
        },
    }
    r = requests.post(f"{WF_BASE}/workflows/{wf_id}/runs?api-version={APIV}",
                      headers=_hdr(), json=body, timeout=60)
    r.raise_for_status()
    return r.json()


def main(req):  # Fabric UDF entrypoint
    method = req.method.upper()
    path = req.url.path
    requester = req.headers.get("x-ms-client-principal-oid", "")

    if method == "POST" and path.endswith("/access-requests"):
        body = json.loads(req.body or "{}")
        return trigger_access_request(
            body["asset_qname"], body["permission"],
            body.get("justification", ""), requester,
        )
    if method == "GET" and "/access-requests/mine" in path:
        return list_my_tasks(requester)
    if method == "POST" and path.endswith("/catalog/bulk-update"):
        body = json.loads(req.body or "{}")
        return trigger_bulk_update(
            body["asset_qnames"], body.get("description"), body.get("tags"),
        )
    return {"error": "not_found", "path": path}
