---
description: "Coding conventions for Rayfin (Fabric Apps) projects — entity, auth, query and deployment rules. Auto-applied to Rayfin source files."
applyTo: "**/rayfin/**/*.ts, **/rayfin.yml, **/data/schema.ts"
---

# Rayfin Coding Instructions

These rules apply automatically when editing Rayfin project files. For deep API detail and
examples, consult the `rayfin` skill and the Rayfin docs MCP (`search_docs` / `get_doc`).

## Decorators & TypeScript

- Use TC39 Stage 3 decorators only. Never enable `experimentalDecorators` or `emitDecoratorMetadata`.
- Ensure `ESNext.Decorators` is in the tsconfig `lib` array.
- Import entity classes with `import` (not `import type`) when referenced in `@one()`/`@many()`
  arrow functions — decorators need the runtime class value.

## Entities

- One entity per file in `rayfin/data/`, exported, and registered in `rayfin/data/schema.ts`.
- Every field needs exactly one type decorator: `@uuid`, `@text`, `@int`, `@decimal`,
  `@boolean`, `@date`, `@email`, `@set`.
- Always pass `max` to `@text()` (e.g. `@text({ max: 200 })`). Never use `NVARCHAR(MAX)` —
  it breaks DAB GraphQL schema generation on MSSQL.
- Required by default; use `{ optional: true }` together with `?` for nullable fields.
- FK columns (`{property}_id`) referencing another entity's `@uuid()` PK must be `@uuid()`.
  Auth-derived fields like `user_id`/`ownerSub` from `claims.sub` are `@text()`.

## Authorization (required)

- Every entity must have an explicit permission decorator (`@role`, `@authenticated`,
  `@anonymous`). An entity with none is inaccessible; never rely on implicit defaults.
- Add a row-level `policy` for user-scoped data:
  `policy: (claims, item) => claims.sub.eq(item.ownerSub)`.
- Hide sensitive fields with `exclude: ['secret']` in role options.
- Publishable keys (`pk-*`) are the only secrets allowed in client code. Never put service
  secrets, connection strings, or policy data in the frontend bundle.

## Querying

- Use the typed client: `client.data.<Entity>` — never raw `fetch()` or hand-built GraphQL.
- Chain order: `.select()` → `.where()` → `.orderBy()` → `.execute()`.
- Single record: `client.data.Entity.findById('uuid')` (not `findByPk`).
- Filter by FK columns with `{property}_id`; dot-paths (`customer.name`) are for `.select()` only.
- Sort directions are lowercase `'asc'` / `'desc'`. Paginate with `.first(n).executePaginated()`.

## Schema & deployment safety

- `rayfin dev db apply` is local; `rayfin up db apply` is a production operation against Fabric.
- Never pass `--force` (drop/alter) without explicit review — it permits data-loss migrations.
- Keep `allowedRedirectUris` in `rayfin.yml` tightly scoped. In deployed Fabric apps disable
  password auth (`password.enabled: false`) and use Fabric SSO (`fabric.enabled: true`).
- When asked to "build and deploy", run the workflow (`rayfin login` → `rayfin up` →
  `rayfin up status`) rather than printing steps for the user.
