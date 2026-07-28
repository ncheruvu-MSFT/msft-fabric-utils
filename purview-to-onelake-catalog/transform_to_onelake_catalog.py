"""Transform a Purview Data Map export into Microsoft Fabric OneLake catalog payloads.

Consumes the JSON produced by ``pull_purview_datamap.py`` and emits ready-to-POST
request bodies for the Fabric REST APIs that govern the OneLake catalog. This is a
DRY-RUN transformer: it writes JSON files only and never calls Fabric.

Mapping (Purview Data Map -> Fabric OneLake catalog):

  Purview business glossary        -> Fabric domain            (Admin - Create Domain)
  Purview glossary top categories  -> Fabric subdomain         (Admin - Create Domain, parentDomainId)
  Purview classifications + terms  -> Fabric tags              (Admin - Bulk Create Tags)
  Purview asset classifications    -> Apply Tags plan per item (Core - Apply Tags)
  + assigned glossary terms

Outputs (under ``out/fabric/``):
  01-domains.json          list of Create Domain request bodies (domains then subdomains)
  02-tags.json             a single Bulk Create Tags request body
  03-tag-assignments.json  per-asset plan: how to find the Fabric item + which tags to apply
  crosswalk.json           Purview -> Fabric name/id crosswalk for review

Each Apply Tags entry includes a Catalog Search body so a later "apply" step can
resolve the asset name to a Fabric {workspaceId, itemId} before applying tags.

Usage:
  python transform_to_onelake_catalog.py --export out/purview-datamap-export.json
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parent

FABRIC_BASE = "https://api.fabric.microsoft.com/v1"
TAG_MAX_LEN = 40          # Fabric tag displayName hard limit
TAG_TENANT_MAX = 10_000   # Fabric tenant tag ceiling
ITEM_TAG_MAX = 10         # max tags applied per item

# Atlas attributes that are descriptive plumbing rather than business assets.
_SKIP_TYPES = {"AtlasGlossary", "AtlasGlossaryTerm", "AtlasGlossaryCategory"}


# --------------------------------------------------------------------- helpers
def sanitize_tag(name: str) -> str:
    """Fabric tag names: <=40 chars; letters/numbers/spaces/specials, no leading space."""
    cleaned = re.sub(r"\s+", " ", (name or "").strip())
    if len(cleaned) > TAG_MAX_LEN:
        cleaned = cleaned[:TAG_MAX_LEN].rstrip()
    return cleaned


def entity_name(entity: dict[str, Any]) -> str:
    attrs = entity.get("attributes", {}) or {}
    return attrs.get("name") or attrs.get("qualifiedName") or entity.get("guid", "")


def entity_qualified_name(entity: dict[str, Any]) -> str:
    return (entity.get("attributes", {}) or {}).get("qualifiedName", "")


# --------------------------------------------------------- term <-> asset map
def build_term_assignments(glossaries: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Map asset guid -> list of assigned glossary term names (from term.assignedEntities)."""
    guid_to_terms: dict[str, list[str]] = {}
    for gloss in glossaries:
        term_info = gloss.get("termInfo") or {}
        # /detailed returns termInfo as {termGuid: {termDef}}; plain list also handled
        terms = term_info.values() if isinstance(term_info, dict) else gloss.get("terms", [])
        for term in terms:
            term_name = term.get("name") or term.get("displayText", "")
            for assigned in term.get("assignedEntities", []) or []:
                guid = assigned.get("guid")
                if guid and term_name:
                    guid_to_terms.setdefault(guid, []).append(term_name)
    return guid_to_terms


def collect_terms(glossaries: list[dict[str, Any]]) -> list[str]:
    names: list[str] = []
    for gloss in glossaries:
        term_info = gloss.get("termInfo") or {}
        terms = term_info.values() if isinstance(term_info, dict) else gloss.get("terms", [])
        for term in terms:
            n = term.get("name") or term.get("displayText")
            if n:
                names.append(n)
    return names


# ----------------------------------------------------------------- transforms
def transform_domains(glossaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Glossary -> domain; top-level glossary category -> subdomain.

    Domains carry a ``_localId`` so subdomains can reference their parent before the
    real Fabric domain id exists (resolved at apply time).
    """
    payloads: list[dict[str, Any]] = []
    for gi, gloss in enumerate(glossaries):
        gname = gloss.get("name") or gloss.get("qualifiedName") or f"Glossary {gi + 1}"
        domain_local = f"domain::{gname}"
        payloads.append({
            "_localId": domain_local,
            "_source": {"type": "AtlasGlossary", "guid": gloss.get("guid"), "name": gname},
            "_target": {"method": "POST", "url": f"{FABRIC_BASE}/admin/domains"},
            "body": {
                "displayName": gname[:40],
                "description": (gloss.get("shortDescription")
                               or gloss.get("longDescription") or "")[:256],
            },
        })
        cat_info = gloss.get("categoryInfo") or {}
        categories = (cat_info.values() if isinstance(cat_info, dict)
                      else gloss.get("categories", []))
        for cat in categories:
            # subdomain only for top-level categories (no parent category)
            if cat.get("parentCategory") or cat.get("parentCategoryGuid"):
                continue
            cname = cat.get("name") or cat.get("displayText")
            if not cname:
                continue
            payloads.append({
                "_localId": f"subdomain::{gname}::{cname}",
                "_source": {"type": "AtlasGlossaryCategory", "guid": cat.get("guid"),
                            "name": cname},
                "_target": {"method": "POST", "url": f"{FABRIC_BASE}/admin/domains"},
                "_parentLocalId": domain_local,
                "body": {
                    "displayName": cname[:40],
                    "description": (cat.get("shortDescription") or "")[:256],
                    # parentDomainId resolved at apply time from _parentLocalId
                    "parentDomainId": None,
                },
            })
    return payloads


def transform_tags(assets: list[dict[str, Any]],
                   classification_defs: list[dict[str, Any]],
                   glossaries: list[dict[str, Any]]) -> tuple[dict[str, Any], list[str]]:
    """Union classifications + glossary terms into one Bulk Create Tags body."""
    names: set[str] = set()

    for cdef in classification_defs:
        n = cdef.get("name")
        if n:
            names.add(n)
    for asset in assets:
        for c in asset.get("classifications", []) or []:
            n = c.get("typeName")
            if n:
                names.add(n)
    for term in collect_terms(glossaries):
        names.add(term)

    create_requests: list[dict[str, str]] = []
    sanitized_index: dict[str, str] = {}   # original -> sanitized (for assignment lookup)
    seen_sanitized: set[str] = set()
    skipped: list[str] = []
    for original in sorted(names):
        s = sanitize_tag(original)
        sanitized_index[original] = s
        if not s or s.lower() in seen_sanitized:
            continue
        if len(create_requests) >= TAG_TENANT_MAX:
            skipped.append(original)
            continue
        seen_sanitized.add(s.lower())
        create_requests.append({"displayName": s})

    body = {
        "_target": {"method": "POST", "url": f"{FABRIC_BASE}/admin/tags/bulkCreateTags"},
        "_note": ("Apply Tags (03-tag-assignments.json) references tag displayNames. "
                  "After creating tags, resolve names to tag ids via "
                  f"GET {FABRIC_BASE}/admin/tags before applying."),
        "body": {"createTagRequests": create_requests},
    }
    return body, list(sanitized_index.keys())


def transform_assignments(assets: list[dict[str, Any]],
                          guid_to_terms: dict[str, list[str]]) -> list[dict[str, Any]]:
    """Per-asset Apply Tags plan, keyed by asset name for later Fabric item resolution."""
    plan: list[dict[str, Any]] = []
    for asset in assets:
        if asset.get("typeName") in _SKIP_TYPES:
            continue
        guid = asset.get("guid", "")
        tag_names: list[str] = []
        for c in asset.get("classifications", []) or []:
            if c.get("typeName"):
                tag_names.append(sanitize_tag(c["typeName"]))
        for term in guid_to_terms.get(guid, []):
            tag_names.append(sanitize_tag(term))

        tag_names = _dedupe_keep_order(tag_names)
        if not tag_names:
            continue

        name = entity_name(asset)
        entry = {
            "_source": {
                "guid": guid,
                "typeName": asset.get("typeName"),
                "name": name,
                "qualifiedName": entity_qualified_name(asset),
            },
            # Step 1: resolve the Atlas asset to a Fabric item.
            "catalogSearch": {
                "method": "POST",
                "url": f"{FABRIC_BASE}/catalog/search",
                "body": {"searchText": name, "filters": []},
            },
            # Step 2: apply the tags (tag ids substituted at apply time).
            "applyTags": {
                "method": "POST",
                "url": (f"{FABRIC_BASE}/workspaces/{{workspaceId}}"
                        f"/items/{{itemId}}/applyTags"),
                "body": {"tags": tag_names[:ITEM_TAG_MAX]},
            },
        }
        if len(tag_names) > ITEM_TAG_MAX:
            entry["_warning"] = (f"{len(tag_names)} tags exceed the {ITEM_TAG_MAX}-per-item "
                                 "limit; truncated.")
        plan.append(entry)
    return plan


def _dedupe_keep_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for i in items:
        k = i.lower()
        if i and k not in seen:
            seen.add(k)
            out.append(i)
    return out


# --------------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser(
        description="Transform a Purview Data Map export into Fabric OneLake catalog payloads.")
    ap.add_argument("--export", default=str(ROOT / "out" / "purview-datamap-export.json"),
                    help="Path to the pull_purview_datamap.py export JSON.")
    ap.add_argument("--out-dir", default=str(ROOT / "out" / "fabric"))
    args = ap.parse_args()

    export_path = pathlib.Path(args.export)
    if not export_path.exists():
        raise SystemExit(f"Export not found: {export_path}\n"
                         "Run pull_purview_datamap.py first.")
    data = json.loads(export_path.read_text(encoding="utf-8"))

    assets = data.get("assets", []) or []
    glossaries = data.get("glossaries", []) or []
    classification_defs = data.get("classificationDefs", []) or []

    print(f"Loaded export: {len(assets)} assets, {len(glossaries)} glossaries, "
          f"{len(classification_defs)} classification defs\n")

    domains = transform_domains(glossaries)
    tags_body, all_concept_names = transform_tags(assets, classification_defs, glossaries)
    guid_to_terms = build_term_assignments(glossaries)
    assignments = transform_assignments(assets, guid_to_terms)

    out_dir = pathlib.Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    crosswalk = {
        "source": {"account": data.get("account"), "exportedAt": data.get("exportedAt")},
        "fabricTargets": {
            "createDomain": f"{FABRIC_BASE}/admin/domains",
            "bulkCreateTags": f"{FABRIC_BASE}/admin/tags/bulkCreateTags",
            "catalogSearch": f"{FABRIC_BASE}/catalog/search",
            "applyTags": f"{FABRIC_BASE}/workspaces/{{workspaceId}}/items/{{itemId}}/applyTags",
        },
        "summary": {
            "domains": sum(1 for d in domains if d["_localId"].startswith("domain::")),
            "subdomains": sum(1 for d in domains if d["_localId"].startswith("subdomain::")),
            "tags": len(tags_body["body"]["createTagRequests"]),
            "taggedAssets": len(assignments),
        },
    }

    _write(out_dir / "01-domains.json", domains)
    _write(out_dir / "02-tags.json", tags_body)
    _write(out_dir / "03-tag-assignments.json", assignments)
    _write(out_dir / "crosswalk.json", crosswalk)

    s = crosswalk["summary"]
    print("Transformed (dry-run, no Fabric calls made):")
    print(f"  domains            : {s['domains']}")
    print(f"  subdomains         : {s['subdomains']}")
    print(f"  tags               : {s['tags']}")
    print(f"  tagged assets      : {s['taggedAssets']}")
    print(f"\nPayloads written to: {out_dir}")


def _write(path: pathlib.Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  wrote {path.name}")


if __name__ == "__main__":
    main()
