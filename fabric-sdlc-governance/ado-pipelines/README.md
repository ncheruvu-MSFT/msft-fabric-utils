# ADO pipeline templates — Fabric CI/CD

These three pipelines target the customer's ADO org **`ncheruvu0468/NagaDevops`** and use the marketplace extension **Microsoft Fabric DevOps Pipelines** (`ms-fabric.fabric-devops-pipelines`) plus the `fabric-cicd` Python package.

| File | Owns | Promotes from → to | Trigger |
|---|---|---|---|
| [`pipeline-de.yml`](pipeline-de.yml) | DE Lakehouses, Notebooks, Pipelines, Warehouses | dev → uat → prod | PR merge to `dev` / `test` / `main` |
| [`pipeline-reporting.yml`](pipeline-reporting.yml) | Power BI semantic models + reports | dev → uat → prod | Same |
| [`pipeline-analytics.yml`](pipeline-analytics.yml) | KQL DBs, Real-Time dashboards, Eventstreams | dev → uat → prod | Same |

All three use the shared steps in [`templates/`](templates/).

## One-time ADO setup

1. **Service connection (FIC / WIF)** — ARM service connection of type *Workload identity federation*, scoped to the SPN granted on Fabric + Purview. **No client secret.**
   This repo uses the existing connection **`azure-fabric-sso`** (Entra app `00000000-0000-0000-0000-000000000000`, subscription `00000000-0000-0000-0000-000000000000`).
   Register the federated trust on the Entra app once — the script reads the issuer/subject directly from ADO so the values are always correct:
   ```pwsh
   $env:ADO_PAT = '<pat with Service Connections (Read)>'
   pwsh ./scripts/register_ado_fic.ps1 `
     -SpnAppId          00000000-0000-0000-0000-000000000000 `
     -AdoOrg            ncheruvu0468 `
     -AdoProject        NagaDevops `
     -ServiceConnection azure-fabric-sso
   ```
   > If the *Workload identity federation (manual)* option isn't visible when creating a new connection in the ADO portal, use [`scripts/create_ado_wif_connection.ps1`](../scripts/create_ado_wif_connection.ps1) to create one via REST.
2. **Variable groups** (Pipelines → Library):
   - `fabric_cicd_nonsensitive` — plain values (`AZURE_SERVICE_CONNECTION=azure-fabric-sso`, `TENANT_ID`, `SPN_CLIENT_ID`, workspace names, capacity id).
   - *(Optional)* `fabric_cicd_kv` — only for non-Fabric secrets (e.g. `PURVIEW_KEY`). `SPN_CLIENT_SECRET` is **no longer required**.
3. **Environments**: `dev`, `test`, `prod` with **manual approval** check on `test` and `prod`.
4. **Pipeline permissions**: each pipeline has access to the variable group(s) + all three environments.

> Auth flow: every `AzureCLI@2` step uses `addSpnToEnvironment: true`; the task receives a fresh OIDC `idToken`, exchanges it at the Entra token endpoint, and exposes `AZURE_CLIENT_ID`/`AZURE_TENANT_ID`/`AZURE_FEDERATED_TOKEN` so `DefaultAzureCredential` (used by `fabric-cicd` and the Python scripts) authenticates without secrets. For steps that need the `fab` CLI directly, include [`templates/fab-auth-wif.yml`](templates/fab-auth-wif.yml).

## Why this layout answers the customer's questions

- **Three pipelines, one shared Prod workspace** → per-team autonomy, single business view.
- **Extension-native `FabricCli@0` task** → service-principal auth, no custom shell wrappers.
- **`fabric-cicd` parameter file** → automatic GUID swap per environment using `$workspace.$id` and `$items.<Type>.<name>.id` tokens.
- **Contracts step gates promotion** → schema drift fails the merge.
- **Purview scan trigger as the last step** → governance is part of CD, not an afterthought.
