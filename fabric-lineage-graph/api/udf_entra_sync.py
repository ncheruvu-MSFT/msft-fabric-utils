"""Fabric User Data Function — Entra group <-> Purview collection role sync.

When a Data-Access-Request workflow is approved, the approver invokes this
function which:

1. Adds the requester to the configured Entra security group via MS Graph.
2. Ensures the group is bound to the target Purview collection role
   (idempotent — only adds when missing).

This is the "self-approval" gate referenced in the README: the requester
never touches Purview RBAC directly, and the approver never has to manage
group membership manually.
"""
from __future__ import annotations
import json
import os
import requests

from azure.identity import DefaultAzureCredential


GRAPH = "https://graph.microsoft.com/v1.0"
PURVIEW = os.environ.get("PURVIEW_ACCOUNT", "ngpurview")
PURVIEW_MGMT = "https://management.azure.com"


def _graph_hdr() -> dict[str, str]:
    tok = DefaultAzureCredential().get_token("https://graph.microsoft.com/.default").token
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


def _arm_hdr() -> dict[str, str]:
    tok = DefaultAzureCredential().get_token("https://management.azure.com/.default").token
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


def _purview_hdr() -> dict[str, str]:
    tok = DefaultAzureCredential().get_token("https://purview.azure.net/.default").token
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


def add_user_to_group(user_oid: str, group_oid: str) -> dict:
    body = {"@odata.id": f"{GRAPH}/directoryObjects/{user_oid}"}
    r = requests.post(f"{GRAPH}/groups/{group_oid}/members/$ref",
                      headers=_graph_hdr(), json=body, timeout=30)
    # 204 No Content on success, 400 if already a member
    return {"status": r.status_code, "user_oid": user_oid, "group_oid": group_oid}


# Purview built-in role IDs (collection-scoped). Source: Purview docs.
_ROLE_NAME_TO_PERMISSION = {
    "collection-reader": "reader",
    "data-source-administrator": "data-source-administrator",
    "data-curator": "data-curator",
    "data-reader": "reader",
    "data-share-contributor": "data-share-contributor",
}


def _ensure_principal_in_rule(rule: dict, principal_oid: str) -> bool:
    """Mutate `rule` in-place so principal_oid appears in any
    principal.microsoft.id attributeMatcher. Returns True when a change was
    made, False when the principal was already present.
    """
    changed = False
    for clause in rule.get("dnfCondition", []):
        for matcher in clause:
            if matcher.get("attributeName") != "principal.microsoft.id":
                continue
            values = matcher.setdefault("attributeValueIncludedIn", [])
            if principal_oid not in values:
                values.append(principal_oid)
                changed = True
    return changed


def ensure_group_on_collection(group_oid: str, collection_id: str,
                               role: str = "collection-reader") -> dict:
    """Adds the Entra group to the Purview metadata policy that governs
    `collection_id`, binding it to `role`.

    Idempotent: returns ``already_bound`` if the group is already listed.

    Calls the Purview policystore API:
      * GET  /policystore/metadataPolicies/{collectionId}
      * PUT  /policystore/metadataPolicies/{collectionId}
    """
    base = f"https://{PURVIEW}.purview.azure.com/policystore/metadataPolicies/{collection_id}"
    api = "api-version=2021-07-01-preview"
    headers = _purview_hdr()

    r = requests.get(f"{base}?{api}", headers=headers, timeout=30)
    if r.status_code == 404:
        return {"status": "collection_not_found", "collection_id": collection_id}
    r.raise_for_status()
    policy = r.json()

    perm_token = _ROLE_NAME_TO_PERMISSION.get(role, role)
    matched = False
    changed = False
    for rule in policy.get("properties", {}).get("attributeRules", []):
        rule_id = rule.get("id", "")
        if perm_token not in rule_id:
            continue
        matched = True
        if _ensure_principal_in_rule(rule, group_oid):
            changed = True

    if not matched:
        return {"status": "role_not_found", "role": role, "group_oid": group_oid}
    if not changed:
        return {"status": "already_bound", "role": role, "group_oid": group_oid}

    put = requests.put(f"{base}?{api}", headers=headers, json=policy, timeout=30)
    put.raise_for_status()
    return {"status": "bound", "role": role, "group_oid": group_oid,
            "collection_id": collection_id}


def main(req):  # Fabric UDF entrypoint
    body = json.loads(req.body or "{}")
    user_oid = body["user_oid"]
    group_oid = body.get("group_oid", os.environ.get("ENTRA_GROUP_OBJECT_ID", ""))
    collection_id = body.get("collection_id", os.environ.get("PURVIEW_COLLECTION_ID", ""))
    role = body.get("role", os.environ.get("PURVIEW_COLLECTION_ROLE", "collection-reader"))

    add_res = add_user_to_group(user_oid, group_oid)
    bind_res = ensure_group_on_collection(group_oid, collection_id, role)
    return {"group_add": add_res, "collection_bind": bind_res}
