"""Resolve Microsoft Information Protection (MIP) sensitivity label GUIDs by name.

The push_labels module needs a GUID for each label name in
``sensitivity-labels.yml``. Operators can either:

  1. Pre-populate ``mip_label_id`` on each policy entry (offline scenario), or
  2. Call ``resolve_label_guids_from_graph()`` once with an Entra token that
     has ``InformationProtectionPolicy.Read.All`` to fetch all tenant labels
     and merge their GUIDs into the policy.

Graph API: ``GET /v1.0/security/informationProtection/sensitivityLabels``
(Returns ``id``, ``name``, ``displayName`` per label.)
"""
from __future__ import annotations
import pathlib
from typing import Any

import requests
import yaml

from azure.identity import DefaultAzureCredential

GRAPH = "https://graph.microsoft.com/v1.0"


def _graph_token() -> str:
    return DefaultAzureCredential().get_token(
        "https://graph.microsoft.com/.default"
    ).token


def fetch_tenant_labels(token: str | None = None) -> list[dict[str, Any]]:
    headers = {"Authorization": f"Bearer {token or _graph_token()}"}
    r = requests.get(
        f"{GRAPH}/security/informationProtection/sensitivityLabels",
        headers=headers, timeout=30,
    )
    r.raise_for_status()
    return r.json().get("value", [])


def resolve_label_guids(policy: dict[str, Any],
                        tenant_labels: list[dict[str, Any]]) -> dict[str, Any]:
    """Return a *new* policy dict where each label entry has ``mip_label_id``
    populated from the matching tenant label (by ``name``, then ``displayName``).
    """
    by_name = {lbl.get("name"): lbl.get("id") for lbl in tenant_labels}
    by_display = {lbl.get("displayName"): lbl.get("id") for lbl in tenant_labels}

    new_policy = dict(policy)
    new_labels = []
    for lbl in policy.get("labels", []):
        guid = by_name.get(lbl["name"]) or by_display.get(lbl["name"])
        merged = dict(lbl)
        if guid:
            merged["mip_label_id"] = guid
        new_labels.append(merged)
    new_policy["labels"] = new_labels
    return new_policy


def resolve_label_guids_from_graph(policy_path: str | pathlib.Path,
                                   write: bool = False) -> dict[str, Any]:
    """Convenience: load ``policy_path``, call Graph, return updated policy.

    Set ``write=True`` to overwrite the YAML file in place.
    """
    p = pathlib.Path(policy_path)
    policy = yaml.safe_load(p.read_text(encoding="utf-8"))
    tenant_labels = fetch_tenant_labels()
    updated = resolve_label_guids(policy, tenant_labels)
    if write:
        p.write_text(yaml.safe_dump(updated, sort_keys=False), encoding="utf-8")
    return updated
