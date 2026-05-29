# What's New in This Pack — End-to-End SDLC + Governance

This document supplements `README.md` with the **full** demo set added to support:
- Per-environment ADO settings & approvals (dev / test / prod)
- Contoso Retail **sample data** (PII-rich)
- **Data dictionary** (YAML, per-table, per-column)
- **Ontology** (terms + triples) published to Purview Unified Catalog
- Custom **Purview classifications** + **MIP sensitivity labels**
- Classification → Label **auto-labeling** rules
- **DLP** policy guidance for Confidential-PII protection in Lakehouse / Warehouse
- Fabric **capacity start/stop** in pipelines for cost control

## ADO Resources (already provisioned in `ncheruvu0468/NagaDevops`)

| Resource | Name | Notes |
|---|---|---|
| Repo | `fabric-sdlc` | Holds this folder's contents |
| Service connection | `azure-fabric-sso` | WIF → Entra app `Purview-SIT-Migration` (`47a48c18-…`) |
| Variable group | `fabric-shared` | TENANT_ID, SVC_CONN, capacity, sub, Purview account |
| Variable group | `fabric-dev` | workspace, lakehouse, warehouse, Purview collection, default sensitivity |
| Variable group | `fabric-test` | same shape as dev |
| Variable group | `fabric-prod` | same shape as dev (default sensitivity = Confidential-PII) |
| Environment | `fabric-dev` | Auto |
| Environment | `fabric-test` | 1 approver |
| Environment | `fabric-prod` | 1 approver (extend to 2 in portal for real prod) |
| Pipeline | `fabric-de` | Build → DeployDev → DeployTest → DeployProd |
| Pipeline | `fabric-reporting` | Build → 3-stage |
| Pipeline | `fabric-analytics` | Build → 3-stage |

## Repo Structure (delta)

```
contracts/
  dictionary/      # Per-table data dictionary YAMLs
    customers.yml employees.yml products.yml orders.yml order_items.yml
  ontology/        # Business ontology — terms + triples (RDF-lite)
    retail.yml
  classifications/ # Custom Purview classification rule definitions
    custom-classifications.yml
  labels/          # MIP sensitivity label catalogue + auto-label rules
    sensitivity-labels.yml
scripts/
  load_sample_data.py                  # Generate Contoso CSVs
  fabric_deploy.py                     # fabric-cicd wrapper (WIF-aware)
  validate_dictionary.py               # CI gate
  validate_ontology.py                 # CI gate
  purview_publish_glossary.py          # Ontology → Purview glossary
  purview_apply_classification_rules.py# Custom classifications
  purview_apply_labels.py              # Classification → label auto-apply
  purview_enforce_dlp.py               # Post-deploy DLP verification
  run_integration_tests.py             # Data-quality + classification checks
  grant_spn_access.ps1                 # One-time RBAC for the WIF app
  labels/
    create_mip_labels.ps1              # Create MIP labels in M365 compliance
    configure_dlp_policy.ps1           # Create Fabric DLP policy
ado-pipelines/templates/
  validate-artifacts.yml
  capacity-control.yml                 # resume/suspend Fabric F4
  deploy-with-fabric-cicd.yml          # WIF-based deploy (no client secret)
  trigger-purview-scan.yml             # Scan + glossary + classify + label
```

## One-Time Setup (run by user, ~5 min)

```pwsh
cd c:\Git\AZ\msft-fabric-utils\fabric-sdlc-governance
# 1. Grant the SPN access to Fabric capacity + Purview + workspaces
pwsh ./scripts/grant_spn_access.ps1

# 2. Create MIP labels in compliance.microsoft.com (needs Compliance Admin)
pwsh ./scripts/labels/create_mip_labels.ps1 -Tenant '62c0cb46-1fcc-4c79-ba1b-d7d9fdfbaa68'

# 3. Configure DLP policy for Fabric (preview cmdlets — falls back to portal instructions)
pwsh ./scripts/labels/configure_dlp_policy.ps1
```

## Pipeline Flow

```
PR / push to main
   │
   ▼
[ Build ]  validate contracts + dictionary + ontology YAMLs
   │
   ▼
[ DeployDev ]            (auto)
   resume capacity → fabric-cicd deploy → load sample data
   → trigger Purview scan → publish glossary → apply classification rules → auto-label assets
   │
   ▼  approval gate
[ DeployTest ]           (1 approver)
   resume capacity → deploy → integration tests → re-scan Purview
   │
   ▼  approval gate
[ DeployProd ]           (1 approver — extend to 2 in portal)
   resume capacity → deploy → re-scan Purview → verify DLP policy active
```

## Sensitivity Label Logic

| Column / Classification | Auto-applied Label |
|---|---|
| Email, Phone, Loyalty ID, SSN | **Confidential-PII** |
| Credit Card, HR compensation | **Highly-Confidential-Restricted** |
| Internal employee ID | **Confidential-PII** |
| (none of the above) | **Internal** (default) |

DLP rule: any asset labeled `Confidential-PII` or higher blocks access for users outside the data-stewards / hr-data security groups when accessed from Fabric Lakehouse/Warehouse SQL endpoints.

## Demo Talk Track (5-minute version)

1. **Pipelines tab** in ADO — show 3 pipelines, the staged YAML, the approval gate icon.
2. **Run** `fabric-de` → watch dev deploy → switch to Purview → see new domain `Contoso Retail Ontology` populate with terms.
3. **Approve test gate** → watch test deploy + integration tests run.
4. **Approve prod gate** → highlight that capacity wakes up, fabric-cicd publishes, Purview re-scans, DLP verification step runs.
5. **Purview portal** → open a scanned `customers` table → show columns auto-classified as `MICROSOFT.PERSONAL.EMAIL` / `CUSTOMER_LOYALTY_ID` → asset has sensitivity label `Confidential-PII`.
6. **Try a query** as non-data-steward user → DLP blocks → tell the story of governance applied end-to-end without writing a single line of bespoke security code.
