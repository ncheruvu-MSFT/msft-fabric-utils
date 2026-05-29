"""Apply governance YAML (domains + glossary + CDEs) to Purview Unified Catalog.

Reads three editable YAML templates under contracts/governance/:
  * domains.yml                  - hierarchical domains, env replication
  * glossary.yml                 - terms (with parent/related, per env)
  * critical_data_elements.yml   - CDEs bound to columns

Behaviour
---------
* Each top-level domain (and its subdomains, recursively) is created once per
  environment listed in domains.yml `environments:`.
* Domain names are suffixed via `name_pattern` (e.g. "Sales-DEV"); the env
  flagged `is_prod: true` keeps the bare name.
* Each domain is linked to a Data Map collection so Data sources scanned into
  that collection can be tagged to the domain.
* Glossary terms are created per env and attached to the matching env-domain.
* CDEs are created per env and attached to the matching env-domain with the
  bound column list rendered into the description.

Idempotent: re-running upserts by (name + parent + domain).

Latest UC REST API:  /datagovernance/catalog/{businessdomains|terms|criticaldataelements}
api-version: 2026-03-20-preview
"""
from __future__ import annotations
import os, sys, uuid, json, pathlib, argparse, requests, yaml
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
GOV  = ROOT / "contracts" / "governance"

# load .env
for env in (ROOT/".env",):
    if env.exists():
        for ln in env.read_text().splitlines():
            if "=" in ln and not ln.startswith("#"):
                k, v = ln.split("=", 1); os.environ.setdefault(k, v)

PURVIEW = os.environ.get("PURVIEW_ACCOUNT", "ngpurview")
TENANT  = os.environ.get("TENANT_ID")
if not TENANT:
    sys.exit("TENANT_ID not set in .env")

UC_BASE = f"https://{TENANT}-api.purview-service.microsoft.com"
API     = "2026-03-20-preview"

# ---------------------------------------------------------------------------
# Auth (cached - DefaultAzureCredential shells out to az CLI which is slow
# and throttles when called hundreds of times in one run).
# ---------------------------------------------------------------------------
_TOKEN_CACHE = {"token": None, "expires_on": 0}

def _token():
    import time
    now = int(time.time())
    if _TOKEN_CACHE["token"] and _TOKEN_CACHE["expires_on"] - 120 > now:
        return _TOKEN_CACHE["token"]
    from azure.identity import DefaultAzureCredential
    t = DefaultAzureCredential().get_token("https://purview.azure.net/.default")
    _TOKEN_CACHE["token"] = t.token
    _TOKEN_CACHE["expires_on"] = t.expires_on
    return t.token

def H():
    return {"Authorization": f"Bearer {_token()}", "Content-Type": "application/json"}

# Session with retry/backoff for transient SSL/connection drops the UC API
# throws under sustained load.
from requests.adapters import HTTPAdapter
try:
    from urllib3.util.retry import Retry
except ImportError:
    from requests.packages.urllib3.util.retry import Retry  # type: ignore

_SESSION = requests.Session()
_retry = Retry(
    total=6, connect=6, read=6, backoff_factor=1.5,
    status_forcelist=(429, 500, 502, 503, 504),
    allowed_methods=frozenset(["GET", "POST", "PUT", "DELETE"]),
    raise_on_status=False,
)
_SESSION.mount("https://", HTTPAdapter(max_retries=_retry, pool_connections=4, pool_maxsize=4))

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def env_name(base_name: str, env: dict, pattern: str) -> str:
    if env.get("is_prod"): return base_name
    return pattern.format(name=base_name, env=env["label"])

def get(url: str, **kw):
    r = _SESSION.get(url, headers=H(), timeout=60, **kw); return r

def post(url: str, body: dict):
    r = _SESSION.post(url, headers=H(), json=body, timeout=60); return r

def put(url: str, body: dict):
    r = _SESSION.put(url, headers=H(), json=body, timeout=60); return r

# ---------------------------------------------------------------------------
# Domain operations
# ---------------------------------------------------------------------------
_domain_cache: dict[str, dict] = {}

def list_domains() -> list[dict]:
    r = get(f"{UC_BASE}/datagovernance/catalog/businessdomains?api-version={API}")
    if not r.ok:
        print(f"  ! list domains {r.status_code}: {r.text[:200]}"); return []
    return r.json().get("value", [])

def find_domain(name: str, parent_id: str | None = None) -> dict | None:
    if not _domain_cache:
        for d in list_domains():
            _domain_cache[d["id"]] = d
    for d in _domain_cache.values():
        if d.get("name") == name and d.get("parentId") == parent_id:
            return d
    return None

def upsert_domain(name: str, description: str, status: str,
                  parent_id: str | None, owners: list[str], dtype: str = "FunctionalUnit") -> str | None:
    existing = find_domain(name, parent_id)
    if existing:
        print(f"    = domain exists: {name} ({existing['id']})")
        return existing["id"]
    payload = {
        "id": str(uuid.uuid4()),
        "name": name,
        "description": description,
        "type": dtype,
        "status": status,
        "isRestricted": False,
    }
    if parent_id:
        payload["parentId"] = parent_id
    r = post(f"{UC_BASE}/datagovernance/catalog/businessdomains?api-version={API}", payload)
    if r.status_code in (200, 201):
        did = r.json()["id"]
        _domain_cache[did] = r.json()
        print(f"    + domain created: {name} -> {did}")
        return did
    print(f"    ! domain FAILED {name}: {r.status_code} {r.text[:300]}")
    return None

def link_domain_to_collection(domain_id: str, name: str, description: str,
                              status: str, parent_id: str | None,
                              collection_name: str):
    payload = {
        "id": domain_id, "name": name, "description": description,
        "type": "FunctionalUnit", "status": status, "isRestricted": False,
        "domains": [{
            "name": collection_name,
            "friendlyName": collection_name,
            "relatedCollections": [{
                "name": collection_name,
                "friendlyName": collection_name,
                "parentCollection": {"type": "CollectionReference", "refName": collection_name},
            }],
        }],
    }
    if parent_id: payload["parentId"] = parent_id
    r = put(f"{UC_BASE}/datagovernance/catalog/businessdomains/{domain_id}?api-version={API}", payload)
    if r.status_code in (200, 201):
        print(f"      linked -> collection '{collection_name}'")
    else:
        print(f"      ! link FAILED: {r.status_code} {r.text[:200]}")

# ---------------------------------------------------------------------------
# Glossary terms
# ---------------------------------------------------------------------------
_term_cache: dict[tuple[str, str], str] = {}  # (domain_id, name) -> term_id
_term_loaded: set[str] = set()

def list_terms(domain_id: str) -> list[dict]:
    r = get(f"{UC_BASE}/datagovernance/catalog/terms?domainId={domain_id}&api-version={API}")
    if not r.ok: return []
    return r.json().get("value", [])

def upsert_term(domain_id: str, name: str, definition: str,
                acronyms: list[str], parent_id: str | None, status: str) -> str | None:
    if domain_id not in _term_loaded:
        for t in list_terms(domain_id):
            _term_cache[(domain_id, t["name"])] = t["id"]
        _term_loaded.add(domain_id)
    key = (domain_id, name)
    if key in _term_cache:
        print(f"      = term exists: {name}")
        return _term_cache[key]
    payload = {
        "id": str(uuid.uuid4()),
        "name": name, "definition": definition, "description": definition,
        "domain": domain_id, "status": status, "acronyms": acronyms or [],
    }
    if parent_id: payload["parentId"] = parent_id
    r = post(f"{UC_BASE}/datagovernance/catalog/terms?api-version={API}", payload)
    if r.status_code in (200, 201):
        tid = r.json().get("id") or payload["id"]
        _term_cache[key] = tid
        print(f"      + term: {name}")
        return tid
    print(f"      ! term FAILED {name}: {r.status_code} {r.text[:200]}")
    return None

def link_related_terms(src_id: str, dst_id: str):
    body = {"relationshipType": "Related", "entityId": dst_id}
    r = post(f"{UC_BASE}/datagovernance/catalog/terms/{src_id}/relationships?api-version={API}&entityType=Term", body)
    if r.status_code >= 400 and r.status_code != 409:
        print(f"        ! related link {src_id}->{dst_id} {r.status_code} {r.text[:160]}")

# ---------------------------------------------------------------------------
# Critical Data Elements
# ---------------------------------------------------------------------------
_cde_cache: dict[tuple[str, str], str] = {}
_cde_loaded: set[str] = set()

def list_cdes(domain_id: str) -> list[dict]:
    r = get(f"{UC_BASE}/datagovernance/catalog/criticaldataelements?domainId={domain_id}&api-version={API}")
    if not r.ok: return []
    return r.json().get("value", [])

# Purview UC CriticalDataElement.dataType enum (case-insensitive) only supports:
#   Number | Text | DateTime | Boolean
# Map common aliases from YAML to the canonical value.
_DATA_TYPE_ALIASES = {
    "number": "Number", "int": "Number", "integer": "Number", "long": "Number",
    "decimal": "Number", "double": "Number", "float": "Number", "money": "Number",
    "text": "Text", "string": "Text", "varchar": "Text", "char": "Text",
    "date": "DateTime", "datetime": "DateTime", "timestamp": "DateTime",
    "bool": "Boolean", "boolean": "Boolean", "bit": "Boolean",
}

def upsert_cde(domain_id: str, cde: dict, status: str) -> str | None:
    name = cde["name"]
    key = (domain_id, name)
    if domain_id not in _cde_loaded:
        for x in list_cdes(domain_id):
            _cde_cache[(domain_id, x["name"])] = x["id"]
        _cde_loaded.add(domain_id)
    if key in _cde_cache:
        print(f"      = CDE exists: {name}")
        return _cde_cache[key]
    cols = cde.get("columns", [])
    col_lines = "\n".join(f"- {c['dataset']}.{c['column']}" for c in cols)
    description = f"{cde.get('description','')}\n\nBound columns:\n{col_lines}".strip()
    raw_dt = (cde.get("data_type") or "Text").strip()
    data_type = _DATA_TYPE_ALIASES.get(raw_dt.lower(), raw_dt)
    owner_oid = os.environ.get("GOVERNANCE_OWNER_OID", "").strip()
    contacts = {"owner": [], "expert": []}
    if owner_oid:
        contacts["owner"].append({"id": owner_oid, "description": "Domain owner"})
    payload = {
        "id": str(uuid.uuid4()),
        "name": name,
        "description": description,
        "domain": domain_id,
        "dataType": data_type,
        "status": status,
        "contacts": contacts,
    }
    r = post(f"{UC_BASE}/datagovernance/catalog/criticaldataelements?api-version={API}", payload)
    if r.status_code in (200, 201):
        cid = r.json().get("id") or payload["id"]
        _cde_cache[key] = cid
        print(f"      + CDE: {name}  ({data_type})")
        return cid
    print(f"      ! CDE FAILED {name}: {r.status_code} {r.text[:200]}")
    return None

# ---------------------------------------------------------------------------
# Recursive domain walk
# ---------------------------------------------------------------------------
def walk_domains(node: dict, env: dict, pattern: str, parent_id: str | None,
                 default_owners: list[str],
                 created: dict[str, dict]):
    """Create node + descendants for one env. Records {bare_name -> {env_id, env_name}}."""
    bare = node["name"]
    full = env_name(bare, env, pattern)
    desc = node.get("description", "")
    owners = node.get("owners", default_owners)
    did = upsert_domain(full, desc, env["status"], parent_id, owners, node.get("type", "FunctionalUnit"))
    if did:
        link_domain_to_collection(did, full, desc, env["status"], parent_id, env["purview_collection"])
        # remember by *bare* name so glossary/CDEs can find it
        created.setdefault(bare, {})[env["key"]] = {"id": did, "name": full}
    for child in node.get("subdomains", []) or []:
        walk_domains(child, env, pattern, did, owners, created)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only-env", help="Apply to a single env key (dev/test/prod) instead of all")
    ap.add_argument("--skip-domains", action="store_true")
    ap.add_argument("--skip-glossary", action="store_true")
    ap.add_argument("--skip-cdes",     action="store_true")
    args = ap.parse_args()

    cfg_d = yaml.safe_load((GOV / "domains.yml").read_text(encoding="utf-8"))
    cfg_g = yaml.safe_load((GOV / "glossary.yml").read_text(encoding="utf-8"))
    cfg_c = yaml.safe_load((GOV / "critical_data_elements.yml").read_text(encoding="utf-8"))

    pattern        = cfg_d.get("name_pattern", "{name}-{env}")
    environments   = cfg_d["environments"]
    default_owners = cfg_d.get("default_owners", [])
    if args.only_env:
        environments = [e for e in environments if e["key"] == args.only_env]

    created: dict[str, dict[str, dict]] = {}  # bare_name -> {env_key -> {id,name}}

    print(f"Purview UC: {UC_BASE}")
    print(f"Envs: {[e['key'] for e in environments]}\n")

    # ---- 1. Domains tree ---------------------------------------------------
    if not args.skip_domains:
        for env in environments:
            print(f"\n=== Domains for env: {env['key'].upper()} (workspace: {env['fabric_workspace']}) ===")
            for top in cfg_d["domains"]:
                walk_domains(top, env, pattern, None, default_owners, created)
    else:
        # still need created index for terms/CDEs - load existing
        for d in list_domains():
            for env in environments:
                # reverse-derive bare name
                full = d["name"]
                bare = full
                if not env.get("is_prod"):
                    suf = "-" + env["label"]
                    if full.endswith(suf): bare = full[:-len(suf)]
                created.setdefault(bare, {})[env["key"]] = {"id": d["id"], "name": full}

    # ---- 2. Glossary terms -------------------------------------------------
    if not args.skip_glossary:
        for env in environments:
            print(f"\n=== Glossary for env: {env['key'].upper()} ===")
            term_ids: dict[str, str] = {}
            # pass 1 - parents-aware (loop until all created)
            pending = list(cfg_g.get("terms", []))
            while pending:
                progressed = False
                for t in list(pending):
                    parent_term = t.get("parent")
                    parent_id = term_ids.get(parent_term) if parent_term else None
                    if parent_term and parent_id is None:
                        continue  # need parent first
                    dom_bare = t["domain"]
                    dom = created.get(dom_bare, {}).get(env["key"])
                    if not dom:
                        print(f"      ! term {t['name']}: no domain '{dom_bare}' in env {env['key']}"); pending.remove(t); continue
                    tid = upsert_term(dom["id"], t["name"], t.get("definition", ""),
                                      t.get("acronyms", []), parent_id, env["status"])
                    if tid:
                        term_ids[t["name"]] = tid
                    pending.remove(t); progressed = True
                if not progressed:
                    print("      ! term parent loop blocked, leftover:", [t["name"] for t in pending]); break
            # pass 2 - related links
            for t in cfg_g.get("terms", []):
                src = term_ids.get(t["name"])
                if not src: continue
                for rel in t.get("related", []) or []:
                    dst = term_ids.get(rel)
                    if dst: link_related_terms(src, dst)

    # ---- 3. Critical Data Elements ----------------------------------------
    if not args.skip_cdes:
        for env in environments:
            print(f"\n=== CDEs for env: {env['key'].upper()} ===")
            for cde in cfg_c.get("critical_data_elements", []):
                dom_bare = cde["domain"]
                dom = created.get(dom_bare, {}).get(env["key"])
                if not dom:
                    print(f"      ! CDE {cde['name']}: no domain '{dom_bare}' in env {env['key']}"); continue
                upsert_cde(dom["id"], cde, env["status"])

    print("\nDone. View at:")
    print(f"  https://purview.microsoft.com/{PURVIEW}/catalog")

if __name__ == "__main__":
    main()
