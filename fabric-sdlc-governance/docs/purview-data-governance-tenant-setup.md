# New Tenant Setup: Microsoft Purview Data Governance (Unified Catalog)

Step-by-step guide for bootstrapping Microsoft Purview **data governance** (Unified
Catalog + Data Map) in a brand-new tenant. Distilled from the official Microsoft Learn
docs — use this as the checklist before/alongside running
[`scripts/purview_fabric_governance.py`](../scripts/purview_fabric_governance.py).

> Sources:
> - [Get started with data governance in Microsoft Purview](https://learn.microsoft.com/purview/data-governance-get-started)
> - [Sample setup walkthrough of Unified Catalog and Data Map](https://learn.microsoft.com/purview/data-governance-setup-sample)
> - [Data Governance Roles and Permissions](https://learn.microsoft.com/purview/data-governance-roles-permissions)
> - [Learn about data governance in the Microsoft Purview portal](https://learn.microsoft.com/purview/data-governance-purview-portal)

## Prerequisites

1. A **Microsoft Purview Enterprise** account:
   - New tenant/customer → just go to <https://purview.microsoft.com> (no prior Azure Purview account needed).
   - Existing free account → [upgrade to enterprise](https://learn.microsoft.com/purview/data-governance-free-version-upgrade-to-enterprise).
   - Existing classic account → [upgrade to the new experience](https://learn.microsoft.com/purview/data-governance-purview-portal#how-to-use-the-new-experience).
2. Data sources you plan to govern should be [registered](https://learn.microsoft.com/purview/data-map-data-sources-register-manage) and [scanned](https://learn.microsoft.com/purview/data-map-scan-ingestion) in Microsoft Purview Data Map. See the [list of supported data sources](https://learn.microsoft.com/purview/data-map-data-sources).

## Business concepts (what you're building)

Unified Catalog organizes governance around five business concepts:

1. **[Governance domains](https://learn.microsoft.com/purview/unified-catalog-governance-domains)** — a boundary for common governance, ownership, and discovery (e.g. functional domains like HR/Sales/Finance, subject areas like Product/Parties, or regulatory domains like SOX/PCI).
2. **[Data products](https://learn.microsoft.com/purview/unified-catalog-data-products)** — a packaged group of assets (tables, files, Power BI reports) with a use case, shared to consumers. Owned by exactly one governance domain, discoverable across many.
3. **[Critical data elements (preview)](https://learn.microsoft.com/purview/unified-catalog-critical-data-elements)**
4. **[Glossary terms](https://learn.microsoft.com/purview/unified-catalog-glossary-terms)**
5. **[Objectives and key results (OKRs)](https://learn.microsoft.com/purview/unified-catalog-okrs)**

## Step 1 — Assign the Data Governance Administrator role

1. Sign in to the [Microsoft Purview portal](https://purview.microsoft.com) with an account that has the *Role management* role (e.g. Purview Administrator).
2. **Settings → Roles and scopes → Role groups**.
3. Select the **Data Governance** role group.
4. **Choose users** / **Choose groups** → add the people who'll administer governance → **Select**.

This grants [application-level permissions](https://learn.microsoft.com/purview/data-governance-roles-permissions#catalog-level-permissions) such as governance domain creation.

## Step 2 — Create your first governance domain

1. Assign users the **governance domain creator** role (see [how to assign catalog-level roles](https://learn.microsoft.com/purview/data-governance-roles-permissions#how-to-assign-catalog-level-roles)).
2. In Unified Catalog: **Catalog management → Governance domains → New governance domain**.
3. Set **name**, **description**, and **type** (e.g. *data domain*, *functional domain*, *regulatory domain*). Leave **parent** blank for a top-level domain.
4. Select **Create**.
5. Create a few more domains to mirror your org structure — e.g. a **Corporate** functional domain as parent, with **Sales** as a child domain.
6. Open the domain → **Roles** tab → assign:
   - **Governance domain owner** — point of support/decision authority for the domain (required — [assign governance domain roles](https://learn.microsoft.com/purview/data-governance-roles-permissions#how-to-assign-governance-domain-roles)).
   - **Data stewards** — business experts who curate metadata and glossary terms.
   - **Data product owners** — know which assets are best to consume.
7. Back on the **Details** tab → **Manage policies** → **Manage access policies** → e.g. check **Permit data copies** to require requester attestation.
8. **Save changes**.
9. Select **Publish** on the governance domain — this publishes all other concepts within it.

## Step 3 — Register and scan data sources

- [Register your data sources](https://learn.microsoft.com/purview/data-map-data-sources-register-manage) in Microsoft Purview Data Map.
- [Scan the data sources](https://learn.microsoft.com/purview/data-map-scan-ingestion#scanning) to capture metadata.

## Step 4 — Build data products

1. Assign **data product owners** ([catalog-level roles](https://learn.microsoft.com/purview/data-governance-roles-permissions#how-to-assign-catalog-level-roles)) to create data products in your governance domains.
2. [Create at least one data product](https://learn.microsoft.com/purview/unified-catalog-data-products-create-manage#create-data-products) per domain, linking it to the relevant registered/scanned assets.

## Step 5 — Grant catalog access

- Assign users [catalog reader permissions](https://learn.microsoft.com/purview/data-governance-roles-permissions#how-to-assign-governance-domain-roles) on your governance domains so they can view and explore data products in Unified Catalog.

## Step 6 — Connect business concepts (recommended)

| Concept | Purpose | How |
|---|---|---|
| **Glossary terms** | Shared, business-friendly vocabulary for data discovery | On the domain page → **Glossary terms** card → **View all** → **New term** → fill name/description/owner/acronyms/links → **Create** → optionally **Manage Policies** (e.g. *Manager approval required*) → **Publish**. Build term hierarchies via parent/related terms, or use **Get suggested terms** for AI-generated suggestions. |
| **OKRs** | Tie a domain's data to measurable business goals | Domain page → **OKR** box → **New OKR** → enter objective, owner, target date → **Create** → **Add key result** to make it measurable → link the OKR to a data product. |
| **Critical data elements (preview)** | Flag high-importance fields across data products | Domain page → CDEs section. |
| **Health management actions** | Steps to improve a data product's governance health score | Review flagged gaps on the domain/data product **Health** page; addressing them raises the score and overall trust/discoverability. |

Suggested role assignment order for Step 6:

1. Assign **data steward** permission in the governance domain (creates/manages glossary terms).
2. Create at least one OKR in the domain, and link it to a data product.
3. Assign **data health reader** permissions in Unified Catalog (catalog-level) so users can monitor governance scores.
4. Publish glossary terms, and link them to data products to improve discoverability.

## Roles cheat sheet

| Scope | Roles |
|---|---|
| **Tenant level** (org-wide, Data Map + Unified Catalog) | Purview Administrators, Data Source Administrators, Data Governance |
| **Catalog level** (Unified Catalog browsing/building) | Governance domain creator, Data health reader |
| **Governance domain level** | Domain owner, Data steward, Data product owner, Catalog reader |

> Microsoft recommends the fewest-permissions principle — minimize the number of users with Global Administrator, and scope roles to the domain/catalog level wherever possible. See [Microsoft Purview roles and permissions](https://learn.microsoft.com/purview/purview-permissions).

## Next: automate with this repo

Once the domain/role structure above is agreed with the customer, use
[`scripts/purview_fabric_governance.py`](../scripts/purview_fabric_governance.py) to create
governance domains, register the Fabric data source, and trigger a scan via the Purview
REST API — start with `--dry-run` before running for real.
