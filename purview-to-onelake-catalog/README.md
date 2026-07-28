# Purview Data Map → Fabric OneLake catalog

Two-step toolkit that exports the **classic Microsoft Purview Data Map (Atlas)**
estate and transforms it into **Microsoft Fabric OneLake catalog** REST payloads
(domains, tags, and per-item tag assignments).

The transform is **dry-run**: it produces ready-to-POST JSON request bodies and
makes **no** calls to Fabric. Review the payloads, then push them with your own
applier (or extend the transform script with an `--apply` mode).

## Why these mappings

The OneLake catalog REST surface is largely *read* (search / list / get item). The
*writable* governance surfaces in Fabric are **domains** and **tags**, so the
crosswalk targets those:

| Purview Data Map (Atlas) | Fabric OneLake catalog | Fabric REST API |
|--------------------------|------------------------|-----------------|
| Business glossary | Domain | `POST /v1/admin/domains` |
| Top-level glossary category | Subdomain | `POST /v1/admin/domains` (`parentDomainId`) |
| Classifications + glossary terms | Tags (tenant) | `POST /v1/admin/tags/bulkCreateTags` |
| Asset classifications + assigned terms | Apply Tags to item | `POST /v1/workspaces/{wsId}/items/{itemId}/applyTags` |
| Asset (for item resolution) | Catalog item match | `POST /v1/catalog/search` |

## Setup

```powershell
cd purview-to-onelake-catalog
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env   # then set PURVIEW_ACCOUNT
```

Auth resolution order: `PURVIEW_ACCESS_TOKEN` env → `az account get-access-token
--resource https://purview.azure.net` → `DefaultAzureCredential`.

> On locked-down tenants where service-principal **data-plane** auth is blocked,
> use a cached `az` user token (`PURVIEW_ACCESS_TOKEN`).

## 1. Pull the Data Map

```powershell
python pull_purview_datamap.py                  # full estate
python pull_purview_datamap.py --with-lineage   # also capture lineage (slower)
python pull_purview_datamap.py --max-assets 2000
```

Writes `out/purview-datamap-export.json` containing `assets`, `glossaries`,
`classificationDefs`, and (optional) `lineage`.

## 2. Transform to Fabric payloads

```powershell
python transform_to_onelake_catalog.py --export out/purview-datamap-export.json
```

Writes to `out/fabric/`:

| File | Contents |
|------|----------|
| `01-domains.json` | Create Domain bodies (domains first, then subdomains with `_parentLocalId`) |
| `02-tags.json` | One Bulk Create Tags body (`createTagRequests`) |
| `03-tag-assignments.json` | Per-asset plan: Catalog Search body + Apply Tags body |
| `crosswalk.json` | Purview→Fabric target map + counts for review |

## Applying the payloads (when ready)

The dry-run files carry helper keys (`_localId`, `_parentLocalId`, `_target`,
`_source`) so an applier can:

1. POST `01-domains.json` domains, capture returned ids, then POST subdomains
   substituting the parent's real `id` for `parentDomainId`.
2. POST `02-tags.json`, then `GET /v1/admin/tags` to resolve tag **names → ids**.
3. For each `03-tag-assignments.json` entry: run the `catalogSearch` to find the
   Fabric `{workspaceId, itemId}`, swap the tag names for ids, then POST `applyTags`.

## Limits enforced by the transform

- Tag `displayName` truncated to **40 chars**; tenant capped at **10,000** tags.
- Max **10 tags per item** (extra tags truncated, entry flagged with `_warning`).

## Files

- [pull_purview_datamap.py](pull_purview_datamap.py) — Atlas export
- [transform_to_onelake_catalog.py](transform_to_onelake_catalog.py) — dry-run Fabric payloads
