# rayfin-governance

Rayfin-based replacements for the governance surfaces currently implemented as
Fabric UDFs + Streamlit pages elsewhere in this repo.

| App | Replaces | Key entities |
|---|---|---|
| [glossary-app](./glossary-app) | [udf_glossary.py](../fabric-lineage-graph/api/udf_glossary.py), [udf_workflows.py](../fabric-lineage-graph/api/udf_workflows.py) | `Term`, `Domain`, `Steward`, `ApprovalRequest` |
| [sdlc-governance-app](./sdlc-governance-app) | [domains.yml](../fabric-sdlc-governance/contracts/governance/domains.yml), [critical_data_elements.yml](../fabric-sdlc-governance/contracts/governance/critical_data_elements.yml), `out_alldomains.txt` state | `Domain`, `Subdomain`, `CriticalDataElement`, `Workspace`, `AttestationRun` |
| [data-agent-governance-app](./data-agent-governance-app) | [fabric-data-agent-governance](../fabric-data-agent-governance) | `Agent`, `Tool`, `PromptTemplate`, `RunLog`, `RedTeamFinding` |
| [infra-request-app](./infra-request-app) | Manual capacity/workspace request tickets | `InfraRequest` (form → approval → GitHub issue) |

## Status

Local scaffolding only — no `rayfin up` yet. Entities, `@role` policies,
`rayfin.yml`, and a minimal Vite + React frontend are in place per app.

## Prerequisites before first deploy

1. Tenant admin enables **Fabric apps (preview)** in
   [Fabric admin portal](https://app.fabric.microsoft.com/admin-portal)
   → Tenant settings → Fabric apps (preview).
2. A Fabric workspace per environment (dev/prod) on a Fabric capacity.
3. Node 20+, then `npm i -g @microsoft/rayfin-cli` (or use `npx`).
4. `npx rayfin login`, then in each app folder:
   ```bash
   npx rayfin up --dry-run --verbose          # preview
   npx rayfin up --workspace <wsname>         # deploy
   ```

## Why Rayfin for these surfaces

- TypeScript entity classes → Fabric SQL DB schema, GraphQL CRUD, typed client.
- Row-level authorization via `@role('authenticated', actions, { policy })`
  with `claims.sub | claims.email | claims.role`.
- Fabric SSO (Entra) built in — avoids the SP/MSAL wiring patterns that
  collide with MCAPS Conditional Access on this tenant.
- Apps + child SQL DB are first-class Fabric items → inherit workspace RBAC,
  sensitivity labels, audit, capacity governance.

## Not a fit (keep elsewhere)

- T-SQL stored procs / multi-step survivorship → Fabric Warehouse.
- Heavy lakehouse joins → notebooks/pipelines that write back via the
  generated GraphQL API.
- Anything needing a non-Entra IdP post-deploy.

## Shared conventions

- `rayfin/data/*.ts` — one entity per file, exported and registered in
  `rayfin/data/schema.ts`.
- `claims.role.eq('steward').or(claims.sub.eq(item.ownerSub))` for steward /
  owner patterns.
- `auditCreatedBy`, `auditCreatedAt`, `auditUpdatedAt` columns on every
  entity (set by API callers; Rayfin does not auto-stamp).
- Static frontend is **public** — never embed secrets or policy data in the
  bundle.

## References

- [Fabric Apps overview](https://learn.microsoft.com/fabric/apps/overview)
- [Rayfin SDK overview](https://learn.microsoft.com/javascript/api/fabric-apps-sdk-javascript/rayfin-overview)
- [Define data permissions](https://learn.microsoft.com/fabric/apps/data-permissions)
- [Project structure](https://learn.microsoft.com/fabric/apps/project-structure)
- [CLI reference](https://learn.microsoft.com/fabric/apps/cli-reference)
- GitHub: [aka.ms/rayfin/GH](https://aka.ms/rayfin/GH)
