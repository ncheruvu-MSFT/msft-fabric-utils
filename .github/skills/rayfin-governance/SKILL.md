---
name: rayfin-governance
description: "Use when building Rayfin apps that implement DATA GOVERNANCE surfaces (glossary, SDLC/domain governance, data-agent governance, lineage) on Fabric Apps. Triggers: rayfin governance, glossary app, sdlc governance, domain governance, critical data element, attestation, data agent governance, red team finding, prompt template, run log, steward, owner policy, @role steward, claims.role, auditCreatedBy, auditCreatedAt, auditUpdatedAt, Fabric apps preview, rayfin up workspace, governance entity, ownerSub, attestation run, approval request, lineage app, harvest run."
metadata:
  author: microsoft
  version: "0.1.0"
---

# Rayfin Governance

Patterns for building **data-governance surfaces** as Rayfin apps on Fabric Apps —
replacing Fabric UDFs + Streamlit pages with TypeScript entity classes, GraphQL CRUD,
a typed client, and Fabric-native RBAC. Read the base `rayfin` skill first; this skill
adds governance-specific conventions.

## When Rayfin Fits a Governance Surface

Use Rayfin when the surface is **transactional metadata** with row-level ownership:

- Business glossary (terms, domains, stewards, approval requests).
- SDLC / domain governance (domains, subdomains, critical data elements, workspaces, attestation runs).
- Data-agent governance (agents, tools, prompt templates, run logs, red-team findings).
- Lineage catalogs (data assets, lineage edges, harvest runs, domains).

**Keep elsewhere** (not a Rayfin fit):

- T-SQL stored procs / multi-step survivorship logic → Fabric Warehouse.
- Heavy lakehouse joins → notebooks/pipelines that write back via the generated GraphQL API.
- Anything that needs a non-Entra IdP after deployment.

## Why Rayfin over SP/MSAL for governance apps

- Fabric SSO (Entra) is built in — avoids hand-wired SP/MSAL patterns that collide with
  MCAPS Conditional Access (service principals are blocked on the data plane on some tenants).
- Apps + their child Fabric SQL DB are first-class Fabric items → inherit workspace RBAC,
  sensitivity labels, audit, and capacity governance for free.
- TypeScript entity classes → Fabric SQL DB schema + GraphQL CRUD + typed client, with
  row-level authorization expressed in code.

## Authorization Patterns

Express role/owner authorization with stacked permission decorators. Governance surfaces
almost always combine a **broad read** with **narrow, policy-gated writes**.

```ts
import { entity, uuid, text, boolean, date, authenticated } from '@microsoft/rayfin-core';

@entity()
@authenticated(['read'])                                   // any signed-in user can read
@authenticated(['create', 'update'], {
  policy: (claims, item) =>
    claims.role.eq('agent-author').or(claims.sub.eq(item.ownerSub)),
})                                                         // authors OR the record owner
@authenticated(['delete'], {
  policy: (claims) => claims.role.eq('agent-admin'),       // admins only
})
export class Agent {
  @uuid() id!: string;
  @text({ max: 200 }) name!: string;
  @text({ max: 4000 }) description!: string;
  @text({ max: 200 }) domainId!: string;
  @text({ max: 200 }) ownerSub!: string;
  @boolean() requiresHumanApproval!: boolean;
  @date() auditCreatedAt!: Date;
  @date({ optional: true }) auditUpdatedAt?: Date;
}
```

Common policy shapes:

- Steward / owner write: `claims.role.eq('steward').or(claims.sub.eq(item.ownerSub))`.
- Admin-only delete: `claims.role.eq('<surface>-admin')`.
- Domain-scoped read: `claims.role.eq('steward').or(claims.sub.eq(item.ownerSub))` plus a
  `domainId` filter applied in the query layer.

## Mandatory Conventions

- **One entity per file** in `rayfin/data/*.ts`, exported and registered in
  `rayfin/data/schema.ts` as `type AppSchema = { Agent: Agent; Tool: Tool; ... }`.
- **Audit columns on every entity**: `auditCreatedBy` (`@text`), `auditCreatedAt` (`@date`),
  `auditUpdatedAt` (`@date`, optional). Rayfin does **not** auto-stamp these — set them in
  the API caller / mutation. Treat them as required governance metadata.
- **Owner column** for owner policies: `ownerSub` (`@text({ max: 200 })`), populated from
  `claims.sub` on create.
- **Reference IDs** to other governance entities are `@text({ max: 200 })` natural keys
  (e.g. `domainId`) unless you model a true `@one()` relationship (then it is a `_id` `@uuid`).
- **Static frontend is public** — never embed secrets, connection strings, or policy data in
  the Vite/React bundle. Authorization lives in `@role`/`@authenticated` policies, enforced
  server-side by the generated GraphQL API.

## Fabric Apps Deployment (governance)

Prerequisites (one-time):

1. Tenant admin enables **Fabric apps (preview)**: Fabric admin portal → Tenant settings →
   Fabric apps (preview).
2. A Fabric workspace per environment (dev/prod) on a Fabric capacity.
3. Node 20+, then `npm i -g @microsoft/rayfin-cli` (or use `npx`).

Per app:

```bash
npx rayfin login
npx rayfin up --dry-run --verbose          # preview the deployment plan
npx rayfin up --workspace <wsname>         # deploy to the target workspace
npx rayfin up status                       # verify endpoint health
```

`rayfin.yml` for a governance app: `services.data.dialect: mssql`, `services.auth.fabric.enabled: true`,
`services.auth.password.enabled: false` (Fabric SSO only in deployed environments), and
`allowedRedirectUris` scoped to `http://localhost:5173` (+ `/auth/callback`) for dev and the
`https://<app>.webapp.fabricapps.net` origin for prod.

## References (Microsoft Learn)

- [Fabric Apps overview](https://learn.microsoft.com/fabric/apps/overview)
- [Define data permissions](https://learn.microsoft.com/fabric/apps/data-permissions)
- [Project structure](https://learn.microsoft.com/fabric/apps/project-structure)
- [CLI reference](https://learn.microsoft.com/fabric/apps/cli-reference)
- [Microsoft Entra authentication in Fabric](https://learn.microsoft.com/fabric/data-warehouse/entra-id-authentication)
- [Fabric permission model](https://learn.microsoft.com/fabric/security/permission-model)
