"""Thin Atlas v2 client — mirrors the auth/retry pattern already used in
fabric-sdlc-governance/scripts/lineage_demo.py so behaviour is consistent.
"""
from __future__ import annotations
import os
import uuid
import requests
from requests.adapters import HTTPAdapter
try:
    from urllib3.util.retry import Retry
except ImportError:  # older urllib3 vendored under requests
    from requests.packages.urllib3.util.retry import Retry  # type: ignore

from .schema import LineageEdge


def _account() -> str:
    return os.environ.get("PURVIEW_ACCOUNT", "ngpurview")


def _atlas_base() -> str:
    return f"https://{_account()}.purview.azure.com/datamap/api/atlas/v2"


def _session() -> requests.Session:
    s = requests.Session()
    s.mount("https://", HTTPAdapter(max_retries=Retry(
        total=6, backoff_factor=1.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET", "POST", "PUT", "DELETE"]),
    )))
    return s


def _token() -> str:
    from azure.identity import DefaultAzureCredential
    return DefaultAzureCredential().get_token("https://purview.azure.net/.default").token


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {_token()}", "Content-Type": "application/json"}


def _entity(type_name: str, qname: str, name: str | None = None,
            extra: dict | None = None) -> dict:
    return {
        "typeName": type_name,
        "guid": f"-{uuid.uuid4().int % 10_000_000}",
        "attributes": {
            "qualifiedName": qname,
            "name": name or qname.rsplit("/", 1)[-1],
            **(extra or {}),
        },
    }


def upsert_edges(edges: list[LineageEdge]) -> dict[str, int]:
    """Push a batch of LineageEdge records to Purview as Process entities.

    Returns a counter dict with ok/skip/fail totals. Atlas upserts on
    qualifiedName so the call is idempotent.
    """
    s = _session()
    base = _atlas_base()
    headers = _headers()
    counts = {"ok": 0, "fail": 0}

    for e in edges:
        src = _entity(e.source_type, e.source_qname)
        tgt = _entity(e.target_type, e.target_qname)
        proc = {
            "typeName": "Process",
            "guid": f"-{uuid.uuid4().int % 10_000_000}",
            "attributes": {
                "qualifiedName": e.process_name,
                "name": e.process_name.split(":")[-1],
                "inputs":  [{"typeName": e.source_type, "uniqueAttributes": {"qualifiedName": e.source_qname}}],
                "outputs": [{"typeName": e.target_type, "uniqueAttributes": {"qualifiedName": e.target_qname}}],
                "description": f"Harvested by {e.process_type} from {e.artifact_ref}",
            },
        }
        body = {"entities": [src, tgt, proc]}
        try:
            r = s.post(f"{base}/entity/bulk", headers=headers, json=body, timeout=60)
            if r.status_code < 300:
                counts["ok"] += 1
            else:
                counts["fail"] += 1
        except requests.RequestException:
            counts["fail"] += 1
    return counts
