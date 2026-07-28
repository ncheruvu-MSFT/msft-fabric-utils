# Cost Guard

Tiny Azure Function App that runs **nightly at 8 PM Eastern**, finds anything billable that's still on, and stops it. Built after an unplanned ~$580/month surprise in this subscription.

| What it does | How |
|---|---|
| Suspend Fabric capacities in `Active` state | ARM `POST .../capacities/{name}/suspend?api-version=2023-11-01` |
| Stop Azure Database for PostgreSQL — Flexible Server in `Ready` state | `azure-mgmt-rdbms` SDK |
| Terminate running Databricks interactive clusters | Databricks REST `clusters/delete` with AAD token |
| Notify a Teams channel with the per-run summary | Incoming Webhook |
| Skip anything tagged `KeepRunning=true` | Tag check on every resource |

**Cost of the guard itself: $0/month** (Y1 Consumption + 30-day Log Analytics retention + ~1 timer trigger/day fits inside the free grant).

## Layout

```
cost-guard/
├── app/
│   ├── function_app.py        Python v2 model — single timer trigger
│   ├── host.json
│   ├── requirements.txt
│   └── .funcignore
├── infra/
│   ├── main.bicep             sub scope — RG + custom role + role assignment
│   ├── app.bicep              RG scope — storage, plan, AI, Log Analytics, function app
│   └── main.bicepparam
├── deploy.ps1
└── README.md
```

## Deploy

```powershell
# from this folder
.\deploy.ps1                   # bicep + code; starts in DRY_RUN=true
.\deploy.ps1 -Run              # also trigger one manual run as a smoke test
.\deploy.ps1 -InfraOnly        # bicep only
.\deploy.ps1 -CodeOnly         # push code to an existing deploy
```

Prereqs:
- `az login` (you already have a cached token)
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local) — recommended; falls back to `az functionapp deployment source config-zip` if missing.

The deployment is **idempotent**. Re-running just re-deploys.

## Configuration

All knobs are app settings on the function app — change them with `az functionapp config appsettings set`.

| Setting | Default | Notes |
|---|---|---|
| `DRY_RUN` | `true` | Set to `false` after verifying one run. |
| `SUBSCRIPTION_ID` | (current sub) | Auto-set by Bicep. |
| `TEAMS_WEBHOOK_URL` | empty | Paste a Teams Incoming Webhook URL to enable Teams notifications. |
| `DATABRICKS_WORKSPACE_URL` | empty | e.g. `https://adb-12345.7.azuredatabricks.net`. Empty disables the Databricks pass. See note below. |
| `WEBSITE_TIME_ZONE` | `America/New_York` | Schedule is `0 0 20 * * *` = 8 PM in this zone. |

Schedule lives in code (the `@app.timer_trigger(...)` decorator in `function_app.py`). To change, edit and `-CodeOnly` redeploy.

### Flip out of dry-run

```powershell
az functionapp config appsettings set `
  -g rg-cost-guard-eastus2-01 `
  -n <function-app-name> `
  --settings DRY_RUN=false
```

### Tag a resource to keep it running

Anything with `KeepRunning=true` is skipped:

```powershell
az tag update --operation merge `
  --resource-id /subscriptions/.../providers/Microsoft.Fabric/capacities/myCap `
  --tags KeepRunning=true
```

## Databricks setup (manual, one-time)

The function uses the function app's managed identity to call the Databricks REST API. For that to work, the MI must exist **inside the workspace** as either an admin or a user with cluster control. After deploy:

1. Open the workspace → **Settings → Identity & access → Service principals → Add service principal**.
2. Paste the function app's MI object ID (output as `principalId` from the Bicep deploy).
3. Grant **Workspace admin** (simplest) or just **Allow cluster creation** + add to a group with terminate permission on shared clusters.

If you skip this, leave `DATABRICKS_WORKSPACE_URL` empty and the function skips that pass cleanly.

## Teams webhook (optional)

Workflows app → "Post to a channel when a webhook request is received" → save → paste URL into `TEAMS_WEBHOOK_URL`. Each run posts a code-fenced summary.

## What it touches

Discovered dynamically every run:

- `Microsoft.Fabric/capacities` — every F-SKU in the sub, state `Active` → `suspend`. Compute billing stops; capacity and OneLake data persist.
- `Microsoft.DBforPostgreSQL/flexibleServers` — state `Ready` → `stop`. **Azure auto-resumes these after 7 days**, so the guard re-stops them on the next nightly run.
- `Microsoft.Databricks/workspaces/*/clusters` (interactive) — `RUNNING|PENDING|RESTARTING|RESIZING` → `clusters/delete`. Note: in Databricks, "delete" on a cluster = terminate (not destroy). Configuration is preserved.

Not touched: serverless SQL, serverless Cosmos, paused capacities, stopped servers, storage accounts, key vaults, anything tagged `KeepRunning=true`.

## RBAC

Bicep creates a least-privilege custom role `Cost Guard Operator (<sub>)` containing only:

```
Microsoft.Resources/subscriptions/read
Microsoft.Resources/subscriptions/resourceGroups/read
Microsoft.Resources/subscriptions/resources/read
Microsoft.Resources/resources/read
Microsoft.Fabric/capacities/read
Microsoft.Fabric/capacities/suspend/action
Microsoft.DBforPostgreSQL/flexibleServers/read
Microsoft.DBforPostgreSQL/flexibleServers/stop/action
Microsoft.Databricks/workspaces/read
```

…and assigns it to the function app's system-assigned MI at subscription scope.

## Observability

```powershell
# live logs
az webapp log tail -g rg-cost-guard-eastus2-01 -n <function-app-name>

# query the last 7 days of runs in Log Analytics
az monitor log-analytics query `
  --workspace <law-resource-id> `
  --analytics-query "traces | where message has 'Cost Guard' | order by timestamp desc | take 50"
```

## Caveats

- **MCAPS** may flip the function-app's storage `publicNetworkAccess` to `Disabled` minutes after create, which breaks the function. If you see triggers stop firing, run:
  ```powershell
  az storage account update -g rg-cost-guard-eastus2-01 -n <storage-name> --public-network-access Enabled
  ```
- Fabric `suspend` returns `BadRequest: Service is not ready to be updated` if a capacity is already paused or mid-transition. The function logs this and moves on — it is not a real error.
- PG flex `begin_stop()` is synchronous (the SDK polls). A nightly run touching 3 servers takes ~1–2 minutes total.
