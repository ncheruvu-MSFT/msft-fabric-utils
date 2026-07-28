# infra-request-app

A Rayfin (Fabric Apps) self-service surface for requesting **Fabric capacity or
workspaces**. A signed-in user fills in a Fluent UI form; the request lands in a
Fabric SQL DB via the generated GraphQL API; an approver gates it; and a GitHub
Actions workflow opens a labelled GitHub issue for the platform team to action.

```
┌────────────────────┐   create    ┌──────────────────────┐   poll approved   ┌──────────────────┐
│  Fluent UI form     │ ──────────▶ │  Rayfin GraphQL API   │ ◀──────────────── │  GitHub Actions   │
│  (Fabric App, SSO)  │   approve   │  + Fabric SQL DB      │   stamp issue url │  provision job    │
└────────────────────┘ ──────────▶ │  (InfraRequest)       │ ────────────────▶ │  -> GitHub Issue  │
                                    └──────────────────────┘                    └──────────────────┘
```

Why this shape: a static Fabric App bundle is **public**, so it must never hold a
GitHub token. The form only writes request rows (authorized server-side by
`@authenticated` policies); the GitHub credential lives in the Actions runner.

## Lifecycle

`Pending` → `Approved` | `Rejected` → `Submitted` (GitHub issue opened) →
`Completed` (platform team closes the loop).

| Action | Who | Where |
|---|---|---|
| Submit request | any signed-in user | form (`create`) |
| Approve / Reject | `infra-approver` or `governance-admin` | grid action (`update`) |
| Open GitHub issue + stamp `Submitted` | `pipeline` role (workflow) | [provision-requests.mjs](./scripts/provision-requests.mjs) |

## Entity

[rayfin/data/infra_request.ts](./rayfin/data/infra_request.ts) — `InfraRequest`
with capacity fields (`capacitySku`, `region`), workspace field
(`targetCapacity`), approval fields, GitHub linkage, and audit columns
(`auditCreatedBy`, `auditCreatedAt`, `auditUpdatedAt`).

Permissions:

- `read` — any authenticated user.
- `create` — any authenticated user (sets `ownerSub` = requester).
- `update` — `infra-approver` / `governance-admin` (approval), `pipeline`
  (GitHub stamping), or the owner while their request is pending.
- `delete` — `governance-admin` only.

## Local development

```bash
npm install
npm run dev            # http://localhost:5173 — runs with seed data, no backend

# With the Rayfin local backend (Docker Desktop required):
npx rayfin dev
npx rayfin dev db apply
# set VITE_RAYFIN_API_URL in .env to the local backend, then `npm run dev`
```

Without a backend the app uses an in-memory seed store so the form, approval
actions, and grid all work for demos.

## Deploy to Fabric

A Rayfin app deploys into an **existing** Fabric workspace (it is itself a Fabric
item). Prereqs: tenant admin has enabled **Fabric apps (preview)**, a workspace
on a Fabric capacity, Node 20+, and the Rayfin CLI.

```powershell
$env:FABRIC_WORKSPACE_ID = '<workspace-guid>'
./deploy.ps1                      # builds dist/ and runs `rayfin up`
./deploy.ps1 -WhatIf              # preview the deploy command only
```

CI/CD: this app is included in the
[rayfin-governance.yml](../../.github/workflows/rayfin-governance.yml) deploy
matrix.

After deploying, add `https://<app>.webapp.fabricapps.net` (and `/auth/callback`)
to `allowedRedirectUris` in [rayfin/rayfin.yml](./rayfin/rayfin.yml).

## Provisioning workflow

[.github/workflows/infra-request-provision.yml](../../.github/workflows/infra-request-provision.yml)
runs every 15 minutes (and on demand). It needs:

- Variable `RAYFIN_API_URL` — the deployed backend base URL.
- Secret `RAYFIN_API_TOKEN` — a bearer token whose claims map to the `pipeline`
  role (read all requests + update GitHub fields).
- Built-in `GITHUB_TOKEN` with `issues: write` (already granted in the workflow).

To wire requests into the repo's Terraform instead of issues, point
`createIssue` in the script at a PR that adds tfvars to
[fabric-private-terraform](../../fabric-private-terraform), or swap it for a
`repository_dispatch` call that triggers a provisioning workflow.

## References

- [Fabric Apps overview](https://learn.microsoft.com/fabric/apps/overview)
- [Define data permissions](https://learn.microsoft.com/fabric/apps/data-permissions)
- [Manage Fabric capacities](https://learn.microsoft.com/fabric/admin/capacity-settings)
- [GitHub REST — create an issue](https://docs.github.com/rest/issues/issues#create-an-issue)
