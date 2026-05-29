# Fabric SDLC + Governance — Reference Architecture

This is the **decision-grade** reference for running a 3-team Fabric estate (Data Engineering, Reporting, Analytics) with true CI/CD via Azure DevOps + GitHub and governance via Microsoft Purview.

It directly answers the customer's "current questions":

| Customer question | Recommendation (and why) |
|---|---|
| One master pipeline, two, or three? | **Three pipelines, one per team, all targeting a shared `main` (Prod) workspace.** Per-team autonomy + a single auditable promotion path to Prod. (See §3.) |
| How many Fabric compute resources (capacities)? | **Two minimum, three preferred.** One non-prod F8 (shared for DE/Reporting/Analytics dev+UAT), one prod F64. Optionally split DE prod (Spark heavy) from BI prod (interactive) on separate capacities to isolate noisy neighbors. (See §4.) |
| How are capacities aligned — by env or by team? | **Primary axis = environment (Dev/UAT/Prod). Secondary axis = workload type at Prod tier** (DE Spark vs. interactive BI). Aligning by team at every tier wastes capacity. |
| Table structures + column types | Standardize on Delta in OneLake; medallion (`bronze/silver/gold`); enforce types in `silver` via the data contract layer. (See §5.) |
| Data contracts for testing schemas | YAML contract per gold table, validated in CI with `great_expectations` or `chispa`; schema drift fails the PR. (See §5.) |
| Hooking into Purview | Register Fabric tenant as Purview data source, scan recurring, classify with Information Protection labels, expose governance domains for each business team. (See §6.) |

---

## 1. Teams and ownership

| Team | Items they own | Repo | Branch model | Workspace tier |
|------|----------------|------|--------------|----------------|
| **Data Engineering** | Lakehouses, Notebooks, Spark Jobs, Pipelines, Data Warehouses | ADO `Fabric-DataEngineering` | `feature/* → dev → test → main` | DE-Dev, DE-UAT, **Prod (shared)** |
| **Reporting (Power BI)** | Semantic models, Reports, Dashboards, Apps | GitHub `fabric-reporting` | same | Reporting-Dev, Reporting-UAT, **Prod (shared)** |
| **Analytics (NEW)** | KQL DBs, Real-Time Dashboards, Eventstreams, Data Activator, Data Science notebooks | GitHub `fabric-analytics` | same | Analytics-Dev, Analytics-UAT, **Prod (shared)** |

> **Why the "Analytics" team is created separately**: the experimental nature (KQL / streaming / DS notebooks) needs faster release cadence and a different review bar than DE. Separating it now prevents bottlenecking the DE PR queue later.

## 2. Workspaces

```
                                Prod (one workspace)
                                ┌───────────────────────────┐
                                │ analytics-prod            │
                                │ - DE Lakehouses + WH      │
                                │ - Power BI semantic       │
                                │ - KQL DBs + RT dashboards │
                                └───────────────────────────┘
                                       ▲   ▲   ▲
                ┌──────────────────────┘   │   └───────────────────────┐
                │                          │                           │
        ┌──────────────┐         ┌──────────────────┐         ┌────────────────┐
        │ de-uat       │         │ reporting-uat    │         │ analytics-uat  │
        └──────▲───────┘         └────────▲─────────┘         └────────▲───────┘
               │                          │                            │
        ┌──────────────┐         ┌──────────────────┐         ┌────────────────┐
        │ de-dev       │         │ reporting-dev    │         │ analytics-dev  │
        │ ⇄ Git (dev)  │         │ ⇄ Git (dev)      │         │ ⇄ Git (dev)    │
        └──────────────┘         └──────────────────┘         └────────────────┘
```

**Only `*-dev` workspaces are Git-connected.** UAT and Prod receive items via the `fabric-cicd` Python package called from ADO/GitHub jobs — this is the pattern the Microsoft tutorial endorses ([source](https://learn.microsoft.com/fabric/cicd/tutorial-fabric-cicd-azure-devops)). UAT/Prod branches act as **deployment records**, not workspace mirrors.

## 3. Pipeline topology — comparison

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| **A. One master pipeline** | Single source of truth; easiest auditing | All teams blocked by any failing stage; long PR queue | ❌ Avoid for >1 team |
| **B. Two pipelines** (DE separate; BI+Analytics combined) | Reasonable isolation | Reporting + Analytics still coupled; KQL releases blocked by Power BI gates | ⚠️ Acceptable interim |
| **C. Three pipelines** (one per team) → all promote to **shared Prod workspace** | Per-team autonomy + cadence; clear ownership; failures localized | Three sets of variable groups + environments to maintain | ✅ **Recommended** |

> The shared **Prod workspace** is what gives the business "one pane of glass." The three pipelines simply own different subsets of items in that workspace via the `item_type_in_scope` filter in `fabric-cicd`.

### Promotion gates

```
feature/*  ──PR──▶  dev  ──CI: build+contracts──▶  test  ──manual approval──▶  main (Prod)
                       │                              │                           │
                  Fabric DEV ws                  Fabric UAT ws              Fabric PROD ws
                  (Git connected)               (deploy via fabric-cicd)   (deploy via fabric-cicd)
```

## 4. Capacity sizing

| Tier | Capacity | SKU (start) | Assigned workspaces | Why |
|------|----------|-------------|--------------------|-----|
| Dev/UAT | `cap-fabric-nonprod` | **F8** | All `*-dev` and `*-uat` | Burst-friendly, cheap; pause when idle |
| Prod (interactive) | `cap-fabric-prod-bi` | **F32 / F64** | `analytics-prod` (BI items) | Sized for concurrent report users |
| Prod (engineering) | `cap-fabric-prod-de` (optional) | **F32+** | `analytics-prod` (Lakehouse/WH compute) | Isolate Spark CU spikes from BI users; only add when DE saturates the shared capacity |

**Don't align capacities to teams.** Teams ≠ workloads. A Power BI dev report and a KQL dev dashboard cost roughly the same CU; mixing them on a single non-prod capacity is fine and 3× cheaper than per-team capacities.

## 5. Table structures, types, and data contracts

### Medallion in OneLake

```
abfss://onelake.dfs.fabric.microsoft.com/
└─ analytics-prod.Lakehouse/
   └─ Tables/
      ├─ bronze/   (raw, schema-on-read)
      ├─ silver/   (typed, deduplicated, contract-enforced)
      └─ gold/     (business-ready, consumed by Power BI Direct Lake)
```

### Type policy

| Layer | Rule |
|---|---|
| `bronze` | Strings + timestamps OK; no enforcement |
| `silver` | Strict types: `decimal(p,s)` not `float`; `int` not `bigint` unless needed; `varchar(n)` sized; no nullable PKs |
| `gold` | Star schema; surrogate keys `bigint`; degenerate dims promoted; column ordering matters for Direct Lake compression |

### Data contracts (YAML, one per gold table)

`contracts/gold/fact_sales.yml`:
```yaml
table: gold.fact_sales
owner: data-engineering
sla: { freshness_hours: 6, completeness_pct: 99.5 }
columns:
  - { name: sale_id, type: bigint, nullable: false, pk: true }
  - { name: customer_id, type: bigint, nullable: false, fk: dim_customer }
  - { name: amount, type: decimal(18,2), nullable: false, range: [0, 1000000] }
  - { name: sale_ts, type: timestamp, nullable: false }
expectations:
  - row_count_min: 1000
  - unique: [sale_id]
```

The CI job runs `python scripts/validate_contracts.py contracts/gold/*.yml` against the **`*-uat`** workspace **before** promoting to `main`. A schema diff fails the build; the PR cannot merge.

## 6. Purview governance plan

### Governance domains to create

| Domain | Owners | Maps to Fabric domain | Sample data products |
|---|---|---|---|
| **Sales & Revenue** | CFO org | yes | `fact_sales`, `dim_customer` |
| **Operations** | COO org | yes | `fact_shipments`, `dim_warehouse` |
| **Customer 360** | CMO org | yes | `gold.customer_unified` |
| **Platform & Telemetry** | Platform team | no | Spark logs, Fabric capacity metrics |

> Purview hard limit: **5 platform domains**. Governance domains in Unified Catalog have no such hard limit and are the right fit for business-team mapping ([source](https://learn.microsoft.com/purview/data-gov-best-practices-domains-and-gov-domains)).

### Scan plan

1. Register Fabric tenant as a Purview data source (same-tenant flow).
2. Use **system-assigned managed identity** of Purview, added to the Fabric admin-API security group.
3. Enable **"Enhance admin APIs responses with detailed metadata"** + **"…with DAX and mashup expressions"** in the Fabric admin portal.
4. Schedule a **weekly recurring scan** at 02:00 UTC Sunday.
5. Tag scanned assets to governance domains via the Unified Catalog APIs (script does this in §3 of `purview_fabric_governance.py`).
6. Apply Information Protection sensitivity labels — `Confidential\Sales` on the Sales domain, etc.

## 7. Sequence — a feature lands in Prod

```
DE engineer ─── git push feature/x ────────────────────────────────────────────────┐
                                                                                   │
ADO PR pipeline (CI):                                                              ▼
  ✓ lint notebooks (nbqa)
  ✓ pytest unit tests on PySpark transforms
  ✓ validate_contracts.py against silver schemas
  ✓ fab CLI: dry-run deploy to de-dev (validates item references)
                │
                ▼
PR merged → dev branch → Fabric Git pulls into  de-dev workspace (auto)
                │
                ▼
ADO release pipeline (CD, dev → test):
  ✓ fabric-cicd deploy to de-uat workspace
  ✓ Run integration tests (Spark notebook executes via Fabric API)
  ✓ Re-run contracts vs. uat data
                │
                ▼   manual approval gate (Test → Main)
                ▼
ADO release pipeline (CD, test → main):
  ✓ fabric-cicd deploy to analytics-prod (DE items only)
  ✓ Trigger Purview scan (REST: POST .../scans/{name}/runs/{guid})
  ✓ Notify Reporting + Analytics teams (Teams webhook) of new contracts
```

## 8. RACI

| Activity | DE | Reporting | Analytics | Platform | Governance |
|---|----|-----------|-----------|----------|------------|
| Fabric capacity sizing | C | C | C | **R/A** | I |
| Workspace creation | I | I | I | **R/A** | I |
| Branch + Git connection | **R** | **R** | **R** | A | I |
| ADO/GH pipeline templates | C | C | C | **R/A** | I |
| Data contracts | **R/A** | C | C | I | C |
| Purview domain creation | I | I | I | C | **R/A** |
| Purview scans | I | I | I | C | **R/A** |
| Sensitivity labels | C | C | C | I | **R/A** |

R = Responsible · A = Accountable · C = Consulted · I = Informed
