---
mode: agent
description: "Scaffold a new Rayfin entity with type decorators, explicit permissions, audit columns, and schema registration."
---

# Scaffold a Rayfin entity

Create a new Rayfin entity named `${input:entityName:EntityName}` for the
`${input:appPath:rayfin/data}` directory.

Follow the `rayfin` and `rayfin-governance` skills. Specifically:

1. Create `${input:appPath}/${input:entityName}.ts` with:
   - `@entity()` on the class.
   - A `@uuid() id!: string;` primary key.
   - One type decorator per field (`@text({ max: N })`, `@uuid`, `@int`, `@decimal`,
     `@boolean`, `@date`, `@email`, `@set`). Never use `@text()` without `max`.
   - An `ownerSub` (`@text({ max: 200 })`) column if records are user-owned.
   - Audit columns: `auditCreatedBy` (`@text`), `auditCreatedAt` (`@date`),
     `auditUpdatedAt` (`@date`, optional).
2. Add explicit permission decorators — never leave an entity without one:
   - `@authenticated(['read'])` for broad read.
   - `@authenticated(['create','update'], { policy: (claims,item) => claims.sub.eq(item.ownerSub) })`
     for owner-scoped writes (adjust the policy to the use case).
   - Admin-gated delete where appropriate: `@authenticated(['delete'], { policy: (claims) => claims.role.eq('<surface>-admin') })`.
3. Register the entity in `${input:appPath}/schema.ts` under `type AppSchema`.
4. Use `import` (not `import type`) for any related entity classes referenced in
   `@one()`/`@many()` arrow functions.

Before finalizing, run `search_docs(query: 'known limitations', module: 'guide')` (or read
`node_modules/@microsoft/rayfin-mcp/assets/docs/guide/known-limitations.md`) to confirm field
types and constraints. Then show the created files. Do not run `db apply` unless asked.
