# Fabric SDLC + Governance Demo Pack

End-to-end demo for **Microsoft Fabric CI/CD with Azure DevOps + GitHub + Microsoft Purview governance** — designed to drive a customer conversation around their three teams (Data Engineering, Reporting, Analytics) and answer the practical questions about pipelines, capacities, contracts, and governance.

> Customer ADO org used in the live demo: <https://dev.azure.com/ncheruvu0468/NagaDevops>
> Marketplace extension installed: **Microsoft Fabric DevOps Pipelines** (`ms-fabric.fabric-devops-pipelines`)

## 📦 What's in this pack

| # | Asset | Path | Purpose |
|---|-------|------|---------|
| 1 | **Reference architecture** | [`docs/sdlc-reference-architecture.md`](docs/sdlc-reference-architecture.md) | Teams → workspaces → capacities → branches → pipelines decision matrix and answers to the customer's "current questions" |
| 2 | **Customer notebook** | [`notebook/fabric-sdlc-purview-demo.ipynb`](notebook/fabric-sdlc-purview-demo.ipynb) | Visual walk-through with embedded draw.io diagrams, KQL/REST evidence cells, and "live" governance actions |
| 3 | **Purview REST scripts** | [`scripts/purview_fabric_governance.py`](scripts/purview_fabric_governance.py) | Create governance domains, register Fabric data source, trigger scan — all via REST API |
| 4 | **ADO pipeline templates** | [`ado-pipelines/`](ado-pipelines/) | YAML templates per team using the Fabric DevOps extension + `fabric-cicd` Python package |
| 5 | **GitHub Actions mirror** | [`.github-workflows/`](.github-workflows/) | Same SDLC expressed as GitHub Actions for cross-runner demo (rename to `.github/workflows/` to enable) |

## 🎯 The 3-team topology demoed here

```
        ┌─────────────────────────────────────────────────────────────┐
        │                    Master / Prod Workspace                  │
        │              (analytics-prod — F64 capacity)                │
        └───────────────▲──────────────▲──────────────▲───────────────┘
                        │              │              │
            ┌───────────┴──┐   ┌───────┴──────┐   ┌───┴────────────┐
            │ DE-Dev/UAT   │   │ Reporting    │   │ Analytics      │
            │ (F8 cap.)    │   │ Dev/UAT (F4) │   │ Dev/UAT (F4)   │
            └──────────────┘   └──────────────┘   └────────────────┘
                  │                   │                    │
            DE Repo (ADO)       Reporting Repo (GH)   Analytics Repo (GH)
            ┌─────────────┐     ┌─────────────────┐   ┌──────────────────┐
            │ dev → test  │     │ dev → test      │   │ dev → test       │
            │   → main    │     │   → main        │   │   → main         │
            └─────────────┘     └─────────────────┘   └──────────────────┘
```

See [`docs/sdlc-reference-architecture.md`](docs/sdlc-reference-architecture.md#3-pipeline-topology-options) for the full trade-off matrix between **one master pipeline / two pipelines / three per-team pipelines**.

## 🚀 Quickstart (templated)

```powershell
# 1. Install the python deps used by the Purview script and fabric-cicd
pip install -r requirements.txt

# 2. Copy and edit the env template
Copy-Item .env.example .env
# edit .env — fill TENANT_ID, PURVIEW_ACCOUNT, FABRIC_TENANT_ID, SPN_*, KEYVAULT_NAME

# 3. Dry-run the Purview governance bootstrap
python scripts/purview_fabric_governance.py --dry-run

# 4. Real run (requires Purview Data Source Admin on the target collection)
python scripts/purview_fabric_governance.py
```

## 🔁 Live execution checklist

Before running anything against your tenant, gather:

- [ ] Entra Tenant ID
- [ ] Purview account name (e.g. `naga-purview`)
- [ ] Service Principal (Client ID + Secret) granted:
  - `Purview Data Source Admin` on target collection
  - Member of the Fabric admin-API security group
- [ ] Key Vault name (for the linked ADO variable group)
- [ ] Fabric capacity IDs for DE / Reporting / Analytics (one per team in the demo topology)
- [ ] ADO project name (`NagaDevops`) and PAT with `Build (Read & execute)` + `Variable Groups (Read, create, manage)`

## 📚 References

- ADO marketplace extension: <https://marketplace.visualstudio.com/items?itemName=ms-fabric.fabric-devops-pipelines>
- `fabric-cicd` package: <https://microsoft.github.io/fabric-cicd>
- ADO + fabric-cicd tutorial: <https://learn.microsoft.com/fabric/cicd/tutorial-fabric-cicd-azure-devops>
- Purview Fabric scan (same tenant): <https://learn.microsoft.com/purview/register-scan-fabric-tenant>
- Purview governance domains: <https://learn.microsoft.com/purview/data-gov-best-practices-domains-and-gov-domains>
- Fabric Git integration: <https://learn.microsoft.com/fabric/cicd/git-integration/intro-to-git-integration>
