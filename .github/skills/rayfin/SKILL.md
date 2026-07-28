---
name: rayfin
description: "Use when doing ANY task involving Rayfin — scaffolding, data models, decorators, auth, storage, deployment, CLI commands, or client setup. Triggers: rayfin, rayfin init, rayfin dev, rayfin up, rayfin login, RayfinClient, @entity, @role, @anonymous, @authenticated, @text, @uuid, @int, @decimal, @boolean, @date, @email, @set, @one, @many, @blob, DAB, Data API Builder, rayfin.yml, publishableKey, signUp, signIn, signOut, sendMagicLink, handleMagicLinkCallback, ensureSignedInWithFabric, Fabric SSO, Entra ID, rayfin dev db apply, rayfin dev storage apply, rayfin up db apply, rayfin up staticapp deploy, schema.ts, OpaqueSession, onSessionChange, GraphQL select, GraphQL create, GraphQL update, GraphQL delete, findById, executePaginated, storage upload, storage download, storage list, prefix isolation, RLS policy, row-level security, claims.sub, claims.email, TC39 decorators, config generation, dialect, mssql, postgresql"
metadata:
  author: microsoft
  version: "0.2.0"
---

# Rayfin

## Rayfin Docs

Rayfin's documentation is available as markdown files and via MCP tools.
Use these for code examples, API details, and troubleshooting — not this skill.

**MCP tools** (if the `rayfin` MCP server is connected):

- `search_docs(query: '<topic>', module: 'guide')` — builder guides and tutorials
- `search_docs(query: '<topic>', module: 'ts-sdk')` — TypeScript SDK API reference
- `get_doc(symbol: '<decorator or class>')` — resolve a symbol to its docs

**Direct file access** (same content the MCP indexes):

- In a Rayfin project: `node_modules/@microsoft/rayfin-mcp/assets/docs/guide/`
- In the Rayfin repo: `docs/site/docs/guide/`
- If neither path exists, install the docs package: `npm install --save-dev @microsoft/rayfin-mcp`
- Use `grep` or `view` to search/read these files when MCP is unavailable.

Key doc files:

- `guide/known-limitations.md` — FK naming, constraint limits, relationship rules
- `guide/data/permissions.md` — `@role` decorator, policy DSL, field visibility
- `guide/data/graphql.md` — RayfinClient setup, query chain, mutations
- `guide/auth/overview.md` — auth methods, session handling
- `guide/deploy/index.md` — Fabric deployment workflow

**Before creating entities or writing queries**, check known limitations:

```text
search_docs(query: 'known limitations', module: 'guide')
# or: view node_modules/@microsoft/rayfin-mcp/assets/docs/guide/known-limitations.md
```

## Rules

### Platform

- Rayfin uses TC39 Stage 3 decorators — never enable `experimentalDecorators` or `emitDecoratorMetadata`.
- Include `ESNext.Decorators` in the tsconfig `lib` array.
- `rayfin dev` requires Docker Desktop — confirm it is running before troubleshooting startup failures.
- Two deployment targets: Rayfin Local (Docker, MSSQL or PostgreSQL) and Fabric Apps (managed, MSSQL only).
- Prefer `npm create @microsoft/rayfin@latest` for new projects — it generates correct tsconfig and schema boilerplate.

### Security

- Every entity must have an explicit permission decorator (`@role`, `@anonymous`, `@authenticated`) — entities without one are inaccessible.
- Add `policy: (claims, item) => claims.sub.eq(item.user_id)` for row-level filtering on user-scoped data.
- Use `exclude` in role options to hide sensitive fields (e.g., `exclude: ['secret']`).
- Publishable keys (`pk-*`) are safe for client-side code — never expose service secrets or connection strings.
- Keep `allowedRedirectUris` in `rayfin.yml` tightly scoped to your app's origin.
- Email/password auth is local development only — deployed Fabric apps support Fabric SSO (Entra ID) exclusively.
- Fabric SSO only works inside the Fabric Portal — do not attempt it in local development.

### Data Modeling

- Define entities with `@entity()` in `rayfin/data/` and register them in `rayfin/data/schema.ts` as `type AppSchema = { Name: Name }`.
- Every field needs exactly one decorator: `@uuid`, `@text`, `@int`, `@decimal`, `@boolean`, `@date`, `@email`, `@set`.
- Fields are required by default — use `{ optional: true }` and `?` together for nullable fields.
- `@text()` length option is `max` (not `maxLength`) — e.g., `@text({ max: 200 })`.
- Use `@one(() => Target)` with lazy arrow functions for relationships — Rayfin auto-generates FK columns named `{property}_id`.
- Use `import` (not `import type`) for entity classes referenced in `@one()`/`@many()` arrow functions — decorators need the runtime class value.
- FK columns referencing another entity (`{property}_id`) must use `@uuid()` to match the PK type. Auth-based fields like `user_id` from `claims.sub` use `@text()`.
- Many-to-many requires an explicit join entity with two `@one()` fields.
- Use `@many(() => Target)` for the inverse side of relationships.

### Querying

- Query chain: `.select()` → `.where()` → `.orderBy()` → `.execute()`.
- Single record by ID: `client.data.Entity.findById('uuid-here')` — not `findByPk`.
- Filter by FK columns using `{property}_id` (e.g., `customer_id`), not dot-path (e.g., `customer.id`).
- Dot-paths are for `.select()` only (e.g., `customer.companyName`).
- Use `.first(n).executePaginated()` for cursor-based pagination.
- Sort directions must be lowercase: `'asc'` or `'desc'`.

### DAB / Schema

- `rayfin dev db apply` compiles TS decorators → DAB config → applies schema to the local database.
- `rayfin up db apply` applies schema to a remote Fabric endpoint — treat as a production operation.
- `--force` permits destructive changes (drop table, drop column, alter type) — never use without review.
- `--gen-config-only` generates the DAB config JSON without applying — use to inspect before applying.

### Storage

- Define storage folders with `@blob('folder-name')` in `rayfin/storage/`.
- Use `prefix` for user-scoped isolation: `client.storage.Avatar.upload('file', data, { prefix: userId })`.
- Apply storage config with `rayfin dev storage apply`.

### Deployment

- When the user asks to "build and deploy" or "make it live," execute the full workflow — do not present steps as instructions for the user to run manually.
- Workflow: `rayfin login` → `rayfin up` → `rayfin up status`.
- `rayfin up status` checks endpoint health — run after deployment to verify.
- Deployment metadata is written to `.env.fabric-<workspace>` and `rayfin.yml`.

## Anti-Patterns

- Never use raw `fetch()` or hand-built GraphQL for data operations — always use `client.data.<Entity>` (provides type-safe queries and automatic auth).
- Never omit permission decorators on entities — always add an explicit `@permissions(...)`. Forgetting silently applies `authenticated: *` (full CRUD for any signed-in user), which is usually too permissive for production data.
- Never use `@text()` without `max` on MSSQL — always set `@text({ max: N })` (e.g. `max: 200` for typical strings). `NVARCHAR(MAX)` breaks DAB's GraphQL schema generation and cannot be uniquely indexed.
- Never use `@text()` for FK columns that reference another entity's `@uuid()` PK — use `@uuid()` to match types. (`user_id` from `claims.sub` is `@text()`, not a FK.)
- Never skip `search_docs('known limitations')` before implementing entities — always run it first to surface platform constraints (text length caps, supported scalar types, MSSQL-specific gotchas) that affect entity design.

## CLI Quick Reference

```bash
# Scaffold
npm create @microsoft/rayfin@latest <name>   # Create from template
npx rayfin init [directory]                   # Interactive setup

# Local dev
npx rayfin dev                                # Start Docker services
npx rayfin dev --down                         # Stop and remove containers
npx rayfin dev --purge                        # Full reset (delete volumes)
npx rayfin dev db apply                       # Apply schema changes
npx rayfin dev db apply --force               # Allow data-loss migrations
npx rayfin dev storage apply                  # Apply storage config
npx rayfin dev watch                          # Auto-apply on file changes
npx rayfin dev status                         # Show service health

# Deploy to Fabric
npx rayfin login                              # Sign in with Entra ID
npx rayfin up                                 # Deploy to Fabric
npx rayfin up status                          # Check deployment health
npx rayfin up db apply                        # Apply remote schema
npx rayfin up staticapp deploy                # Redeploy static content
```
