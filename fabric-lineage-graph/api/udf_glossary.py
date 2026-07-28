"""Fabric User Data Function — glossary REST API.

Proxies CRUD operations to the Purview Atlas glossary API. The Streamlit
Glossary editor page calls these endpoints; external clients (CI hooks, dbt
plugins) can call them too.

Reuses the workflow definitions already published by
fabric-sdlc-governance/scripts/purview_setup_workflows.py — POSTing a new term
triggers the `Create-Glossary-Term` workflow which routes to an approver.
"""
from __future__ import annotations
import json
import os
import uuid
import requests

from azure.identity import DefaultAzureCredential


PURVIEW = os.environ.get("PURVIEW_ACCOUNT", "ngpurview")
GLOSSARY_ID = os.environ.get("GOV_GLOSSARY_ID", "")
ATLAS = f"https://{PURVIEW}.purview.azure.com/datamap/api/atlas/v2"


def _hdr() -> dict[str, str]:
    tok = DefaultAzureCredential().get_token("https://purview.azure.net/.default").token
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


def list_terms() -> dict:
    r = requests.get(f"{ATLAS}/glossary/{GLOSSARY_ID}/terms", headers=_hdr(), timeout=60)
    r.raise_for_status()
    return {"value": r.json()}


def create_term(name: str, definition: str, steward: str) -> dict:
    body = {
        "name": name,
        "longDescription": definition,
        "anchor": {"glossaryGuid": GLOSSARY_ID},
        "additionalAttributes": {"steward": steward, "submittedVia": "fabric-app"},
        "qualifiedName": f"{name}@{uuid.uuid4().hex[:8]}",
    }
    r = requests.post(f"{ATLAS}/glossary/term", headers=_hdr(), json=body, timeout=60)
    r.raise_for_status()
    # The Create-Glossary-Term workflow (registered via purview_apply_workflows.py)
    # is bound to underGlossaryHierarchy and triggers automatically.
    return r.json()


def main(req):  # Fabric UDF entrypoint
    method = req.method.upper()
    if method == "GET":
        return list_terms()
    if method == "POST":
        body = json.loads(req.body or "{}")
        return create_term(body["name"], body["definition"], body.get("steward", ""))
    return {"error": "method_not_allowed", "method": method}
