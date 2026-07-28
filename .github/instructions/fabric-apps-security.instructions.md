---
description: "Fabric Apps security & Entra authentication best practices (sourced from Microsoft Learn). Applies to Fabric Apps / Rayfin deployment and data-permission design."
applyTo: "**/rayfin.yml, **/rayfin/data/**/*.ts"
---

# Fabric Apps Security Best Practices

Grounding for designing data permissions and deployment auth on Fabric Apps. Sources are
Microsoft Learn (linked at the end). Rayfin enforces these via `@role`/`@authenticated`
policies + `rayfin.yml`; the principles below explain *why*.

## Fabric's three-level permission model

Fabric evaluates access in order — a user must pass every level
([permission model](https://learn.microsoft.com/fabric/security/permission-model)):

1. **Entra authentication** — can the user authenticate to the Entra tenant?
2. **Fabric access** — can the user access Microsoft Fabric / the workspace?
3. **Data security** — can the user perform the requested action on the table/row?

Design your Rayfin app so that workspace RBAC handles levels 1–2 and your `@role` policies
handle level 3. Do not re-implement authentication in app code.

## Least privilege

- Grant access at the narrowest level that works
  ([OneLake security best practices](https://learn.microsoft.com/fabric/onelake/security/best-practices-secure-data-in-onelake)).
  Prefer item-level **Share** over workspace roles when a user needs only one item.
- In Rayfin terms: default entities to `@authenticated(['read'])` and gate writes behind
  explicit `policy` predicates rather than granting blanket CRUD.
- Manage permissions via **Entra ID groups**, not per-user grants, wherever possible
  ([Entra auth in Fabric](https://learn.microsoft.com/fabric/data-warehouse/entra-id-authentication)).

## Entra-only authentication (no SQL auth)

- Use Microsoft Entra authentication as the alternative to SQL authentication. In deployed
  Fabric apps, password auth is local-dev only — set `password.enabled: false` and
  `fabric.enabled: true` in `rayfin.yml`.
- Service principals (SPN) are supported for app identities but have **less granular**
  permission configuration than users, and may be blocked on the data plane by tenant
  Conditional Access. Prefer signed-in user identity for runtime data access.

## Row-level security mindset

- RLS restricts data access by filtering rows based on the user's identity, enforced at
  query time ([RLS in Fabric](https://learn.microsoft.com/fabric/data-warehouse/row-level-security)).
- Keep predicates **strongly typed and simple** — integer/string equality lookups are the most
  secure and easiest to reason about
  ([RLS in OneLake](https://learn.microsoft.com/fabric/onelake/security/row-level-security)).
  Avoid vague or overly complex predicates.
- Map this to Rayfin policies: `claims.sub.eq(item.ownerSub)` or `claims.role.eq('steward')`
  — simple equality on an owner/role column beats clever expressions.

## Sensitive data

- Use column-level controls / field `exclude` to prevent unauthorized viewing of sensitive
  columns; mask where appropriate
  ([share & manage permissions](https://learn.microsoft.com/fabric/data-warehouse/share-warehouse-manage-permissions)).
- Never embed secrets or policy data in a public static frontend bundle.
