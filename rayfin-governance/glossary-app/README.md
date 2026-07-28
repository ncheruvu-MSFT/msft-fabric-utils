# glossary-app

Rayfin port of [udf_glossary.py](../../fabric-lineage-graph/api/udf_glossary.py)
and [udf_workflows.py](../../fabric-lineage-graph/api/udf_workflows.py).

## Entities

| Entity | Purpose | Source it replaces |
|---|---|---|
| `Domain` | Business domain / subdomain tree | `governance/domains.yml` |
| `Steward` | Per-domain stewardship membership | hard-coded in UDF |
| `Term` | Glossary term (the Purview Atlas term, mirrored) | Atlas `glossary/term` POST |
| `ApprovalRequest` | Stewardship workflow request | Purview `Create-Glossary-Term` workflow run |

## Authorization model

- All authenticated users can read.
- Anyone can submit a new `Term` (create).
- Only the submitter or a `steward` can update/delete a `Term`.
- Only `domain-admin` can create/update domains or assign stewards.

## Local dev

```bash
npm install
npx rayfin login
npx rayfin up --dry-run --verbose   # validate schema + plan
npm run dev                         # frontend against remote backend
```

## Deploy

```bash
npx rayfin up --workspace <fabric-workspace-name>
```

## Outstanding bridges

- One-way sync to Purview Atlas glossary on `Term` create/update (call from a
  Fabric pipeline that reads the GraphQL API).
- Webhook from Purview workflow → POST `ApprovalRequest` decision back.
