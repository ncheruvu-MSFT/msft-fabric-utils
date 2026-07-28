---
mode: agent
description: "Run the full Rayfin deploy-to-Fabric workflow: login, dry-run, deploy, verify."
---

# Deploy a Rayfin app to Fabric

Deploy the Rayfin app in `${input:appPath:.}` to Fabric. Execute the workflow — do not just
print the steps.

Preflight:

1. Confirm `rayfin.yml` has `services.auth.fabric.enabled: true` and
   `services.auth.password.enabled: false` for the deployed environment.
2. Confirm `allowedRedirectUris` includes the production `https://<app>.webapp.fabricapps.net`
   origin (and localhost only for dev).
3. Confirm the target Fabric workspace exists on a capacity and Fabric apps (preview) is enabled.

Deploy:

```bash
npx rayfin login
npx rayfin up --dry-run --verbose            # review the plan first
npx rayfin up --workspace ${input:workspace:<wsname>}
npx rayfin up status                         # verify endpoint health
```

If schema changes are pending, run `npx rayfin up db apply` — but never pass `--force`
(data-loss migration) without explicit confirmation from the user.

After deploy, report the endpoint URL, `rayfin up status` output, and any values written to
`.env.fabric-<workspace>` / `rayfin.yml`.
