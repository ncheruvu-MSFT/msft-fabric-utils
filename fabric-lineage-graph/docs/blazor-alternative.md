# Hosting a Blazor UI for this app

## TL;DR

Microsoft Fabric **cannot host .NET Blazor natively** as of 2026. Fabric Data
Apps and Fabric User Data Functions are Python-only. The two practical paths
to get a Blazor UI on top of this lineage stack are:

1. **Streamlit now, Blazor later** *(recommended)* — keep the API contract in
   `api/` stable, ship the Streamlit app today, build a Blazor front-end that
   calls the same UDF REST endpoints when .NET hosting becomes available in
   Fabric (on the public roadmap).
2. **Blazor in Azure Container Apps now** — host the Blazor Server app in ACA
   with a user-assigned managed identity that has access to OneLake +
   Purview, and either embed it via an organisational Fabric app link or open
   it as a separate browser tab.

## Path 2 — concrete shape

```
Browser
   |
   v
+--------------------+        +------------------------+
| Blazor Server app  | -----> | Fabric UDF REST API    |
| (Azure Container   |        | (udf_lineage,          |
|  Apps + UAMI)      |        |  udf_glossary, ...)    |
+--------+-----------+        +-----------+------------+
         |                                |
         | OneLake direct read            | Purview Atlas + MS Graph
         v                                v
   abfss://...onelake.dfs              Purview + Graph
```

### Steps

1. Add an ACA environment in the customer subscription (single revision).
2. Container image: `dotnet/aspnet:9.0` base + Blazor Server publish output.
3. Assign a **user-assigned managed identity** with:
   - **Storage Blob Data Reader** on the OneLake workspace (for direct Delta reads via the [Microsoft.Data.Analysis](https://www.nuget.org/packages/Microsoft.Data.Analysis) + `Azure.Storage.Files.DataLake` stack), and
   - **Purview Data Reader** on the target collections.
4. Inject the UDF base URL (from `infra/deploy_fabric_items.py` output) as an env var.
5. Auth users with **Microsoft Entra ID** via the standard ASP.NET Core
   Microsoft Identity Web stack — the same Entra group sync that drives
   self-approval also gates app access.

### What does NOT change

The harvest layer, the OneLake `lineage_edges` Delta table, the UDFs, the
Purview workflows, and the scheduled Fabric pipeline are all unchanged. Only
the UI is swapped.

### Cost / friction tradeoff

| Aspect | Streamlit in Fabric | Blazor in ACA |
|---|---|---|
| Hosting cost | Bundled in F-SKU | ACA consumption (~$10-50/mo idle) |
| Identity | Workspace MI, zero config | UAMI + Entra app reg + RBAC |
| Networking | Inside Fabric VNet by default | ACA VNet integration extra step |
| User experience | Fabric portal, single sign-on free | Either iframe (CSP gotchas) or external tab |
| Skill required | Python | C# / Razor |

For most customers the Streamlit path is right unless there's a hard mandate
on .NET (often a regulated environment with an existing Blazor app fleet and
shared component library).
