"""Push resolved sensitivity labels to Purview + Fabric.

Two-target sync because Purview and Fabric track labels in separate stores:

  * **Purview Atlas** — `POST /datamap/api/atlas/v2/entity/guid/{guid}/classifications`
    Applies a classification named `LABEL_<NAME>` so it shows up on the asset
    card. Mirrors the proxy approach used in
    fabric-sdlc-governance/scripts/purview_apply_labels.py.

  * **Fabric items** — Fabric items (Lakehouse / Warehouse / Power BI dataset)
    take an MIP label via `POST /v1/admin/items/{type}/{id}/setLabel`. Requires
    Fabric Admin + the MIP label GUID (resolved from the policy file).

Idempotent on (asset, label) — re-running with the same label is a no-op.
"""
from __future__ import annotations
import os
from typing import Iterable

import requests

from common import fabric_client
from common.purview_client import _atlas_base, _headers, _session


def _label_guid(policy: dict, label_name: str) -> str | None:
    for lbl in policy.get("labels", []):
        if lbl["name"] == label_name:
            return lbl.get("mip_label_id")
    return None


def push_purview_classifications(assignments: dict[str, str]) -> dict[str, int]:
    """Apply LABEL_<NAME> classification to each Purview asset."""
    s = _session()
    base = _atlas_base()
    counts = {"ok": 0, "fail": 0, "skip": 0}

    for qname, label in assignments.items():
        # Lookup guid by qualifiedName via Atlas search
        try:
            r = s.post(
                f"{_atlas_base()}/search/query",
                headers=_headers(),
                json={"keywords": qname, "limit": 1},
                timeout=30,
            )
            if r.status_code >= 400:
                counts["fail"] += 1
                continue
            hits = r.json().get("value", [])
            if not hits:
                counts["skip"] += 1
                continue
            guid = hits[0]["id"]
        except requests.RequestException:
            counts["fail"] += 1
            continue

        classification = f"LABEL_{label.upper().replace('-', '_')}"
        try:
            r = s.post(
                f"{base}/entity/guid/{guid}/classifications",
                headers=_headers(),
                json=[{"typeName": classification, "attributes": {}, "propagate": True}],
                timeout=30,
            )
            if r.status_code < 300:
                counts["ok"] += 1
            else:
                counts["fail"] += 1
        except requests.RequestException:
            counts["fail"] += 1
    return counts


def push_fabric_labels(assignments: dict[str, str], policy: dict,
                       item_type_for: dict[str, str] | None = None) -> dict[str, int]:
    """Apply MIP label to each Fabric item via /admin/items/{type}/{id}/setLabel.

    `assignments` keys must be Fabric item IDs (not qnames). `item_type_for`
    maps id -> Fabric item type ("Lakehouse", "Warehouse", "SemanticModel").
    """
    item_type_for = item_type_for or {}
    counts = {"ok": 0, "fail": 0, "skip": 0}
    workspace_id = os.environ.get("FABRIC_WORKSPACE_ID", "")
    if not workspace_id:
        return {"ok": 0, "fail": 0, "skip": len(assignments)}

    for item_id, label in assignments.items():
        label_guid = _label_guid(policy, label)
        if not label_guid:
            counts["skip"] += 1
            continue
        item_type = item_type_for.get(item_id, "SemanticModel")
        try:
            r = requests.post(
                f"https://api.fabric.microsoft.com/v1/admin/items/{item_type}/{item_id}/setLabel",
                headers={"Authorization": f"Bearer {fabric_client._token()}",
                         "Content-Type": "application/json"},
                json={"labelId": label_guid},
                timeout=30,
            )
            if r.status_code < 300:
                counts["ok"] += 1
            else:
                counts["fail"] += 1
        except requests.RequestException:
            counts["fail"] += 1
    return counts
